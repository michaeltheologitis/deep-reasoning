"""The SQLite file: schema and migrations, connections, the writer, heads and history (§4.2)."""

import contextlib
import json
import os
import re
import secrets
import sqlite3
import sys
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path

from deep_reasoning.library import texts
from deep_reasoning.library.records import HistoryEntry, Kind, LibraryError
from deep_reasoning.library.shapes import deep_reasoner_build

__all__ = ["Kind"]

SCHEMA_V1 = """
CREATE TABLE revisions (
    rev INTEGER PRIMARY KEY,
    at TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT
) STRICT;

CREATE TABLE versions (
    kind TEXT NOT NULL CHECK (kind IN ('profile', 'namespace', 'decomposition', 'tool')),
    name TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    rev INTEGER NOT NULL REFERENCES revisions (rev),
    deleted INTEGER NOT NULL DEFAULT 0 CHECK (deleted IN (0, 1)),
    yaml TEXT,
    attached TEXT,
    slug TEXT,
    use_when TEXT,
    hint TEXT,
    source TEXT,
    deep_reasoner TEXT NOT NULL,
    PRIMARY KEY (kind, name, version),
    CHECK ((deleted = 1) = (yaml IS NULL)),
    CHECK (kind <> 'profile' OR name = 'profile'),
    CHECK (kind IN ('profile', 'namespace') OR attached IS NULL),
    CHECK (kind = 'decomposition' OR (slug IS NULL AND use_when IS NULL AND hint IS NULL)),
    CHECK (kind = 'tool' OR source IS NULL)
) STRICT;

CREATE INDEX versions_rev ON versions (rev);

CREATE TRIGGER versions_no_update BEFORE UPDATE ON versions
BEGIN SELECT RAISE(ABORT, 'library versions are immutable'); END;
CREATE TRIGGER versions_no_delete BEFORE DELETE ON versions
BEGIN SELECT RAISE(ABORT, 'library versions are immutable'); END;
CREATE TRIGGER revisions_no_update BEFORE UPDATE ON revisions
BEGIN SELECT RAISE(ABORT, 'library revisions are immutable'); END;
CREATE TRIGGER revisions_no_delete BEFORE DELETE ON revisions
BEGIN SELECT RAISE(ABORT, 'library revisions are immutable'); END;
"""

MIGRATIONS: tuple[str, ...] = (
    SCHEMA_V1,
)  # MIGRATIONS[i] takes user_version i to i + 1

NETWORK_FILESYSTEMS: frozenset[str] = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)
MOUNTS = Path("/proc/self/mounts")
BUSY_TIMEOUT_MS = 5000

# One version as it is read back: the version joined to its revision's time and action.
Row = HistoryEntry

_ROWS = """
SELECT v.kind, v.name, v.version, v.rev, r.at AS saved_at, r.action, v.deleted, v.yaml,
       v.attached AS decompositions, v.slug, v.use_when, v.hint, v.source, v.deep_reasoner
  FROM versions AS v JOIN revisions AS r USING (rev)
"""
# Creation order is the rowid of an entity's version 1.
_HEADS = (
    _ROWS
    + """
 WHERE v.version = (SELECT MAX(w.version) FROM versions AS w
                     WHERE w.kind = v.kind AND w.name = v.name AND w.rev <= :rev)
   AND v.deleted = 0
 ORDER BY (SELECT w.rowid FROM versions AS w
            WHERE w.kind = v.kind AND w.name = v.name AND w.version = 1)
"""
)


def _row(record: sqlite3.Row) -> Row:
    attached = record["decompositions"]
    return Row.model_validate(
        {**record, "decompositions": attached and json.loads(attached)}
    )


def filesystem_type(path: Path, *, mounts: Path = MOUNTS) -> str | None:
    """The type of the filesystem holding path: the longest mount point it is under."""
    resolved = path.resolve()
    best: tuple[int, str] | None = None
    for line in mounts.read_text().splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        # The kernel escapes spaces, tabs, newlines and backslashes in mount points as octal.
        point = Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[1]))
        if resolved.is_relative_to(point) and (
            best is None or len(point.parts) > best[0]
        ):
            best = (len(point.parts), fields[2])
    return best[1] if best else None


def refuse_network_filesystem(path: Path, *, mounts: Path = MOUNTS) -> None:
    """LibraryError NETWORK_FS for a path on NFS, SMB, 9p or sshfs (Linux only)."""
    if sys.platform != "linux" or not mounts.exists():
        return
    fstype = filesystem_type(path, mounts=mounts)
    if fstype in NETWORK_FILESYSTEMS:
        raise LibraryError(texts.network_fs(str(path), fstype))


def connect(path: Path, *, mounts: Path = MOUNTS) -> sqlite3.Connection:
    """Refuses a network filesystem (Linux); migrates an older schema."""
    refuse_network_filesystem(path, mounts=mounts)
    conn = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = FULL")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply MIGRATIONS[user_version:], each in its own BEGIN IMMEDIATE: two processes
    migrating at once apply a step once, and a step that fails leaves the file as it
    was. In autocommit mode executescript commits nothing of its own."""
    (version,) = conn.execute("PRAGMA user_version").fetchone()
    for target, script in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.execute("BEGIN IMMEDIATE")
        try:
            (current,) = conn.execute("PRAGMA user_version").fetchone()
            if current < target:
                conn.executescript(f"{script}\nPRAGMA user_version = {target};")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise


def create(path: Path, seed: Callable[[Path], None]) -> bool:
    """Build a library under a temporary name (0600, WAL, schema; seed(temporary) writes
    revision 1) and publish it at path with os.link. False: another process published first."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}-{secrets.token_hex(4)}.new")
    # SQLite gives -wal and -shm the database file's permissions: create it private first.
    os.close(os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    try:
        with contextlib.closing(connect(temporary)) as conn:
            conn.execute("PRAGMA journal_mode = WAL")
        seed(temporary)
        try:
            os.link(temporary, path)
        except FileExistsError:
            return False
        return True
    finally:
        for leftover in (
            temporary,
            *(Path(f"{temporary}{s}") for s in ("-wal", "-shm")),
        ):
            leftover.unlink(missing_ok=True)


def current_rev(conn: sqlite3.Connection) -> int:
    (rev,) = conn.execute("SELECT COALESCE(MAX(rev), 0) FROM revisions").fetchone()
    return rev


def heads(conn: sqlite3.Connection, *, rev: int | None = None) -> list[Row]:
    """Every live entity's head as of rev (default: now), in creation order."""
    as_of = current_rev(conn) if rev is None else rev
    return [_row(r) for r in conn.execute(_HEADS, {"rev": as_of})]


def history(conn: sqlite3.Connection, kind: Kind, name: str) -> list[Row]:
    """Every version of one entity, newest first, tombstones included."""
    query = _ROWS + " WHERE v.kind = ? AND v.name = ? ORDER BY v.version DESC"
    return [_row(r) for r in conn.execute(query, (kind, name))]


def decomposition_named(conn: sqlite3.Connection, slug: str) -> str | None:
    """The name of the decomposition most recently saved with this slug, deleted or not."""
    found = conn.execute(
        "SELECT name FROM versions WHERE kind = 'decomposition' AND slug = ?"
        " ORDER BY rev DESC LIMIT 1",
        (slug,),
    ).fetchone()
    return found["name"] if found else None


@contextlib.contextmanager
def read(path: Path) -> Iterator[sqlite3.Connection]:
    """One read transaction: every query inside sees the same revision."""
    with contextlib.closing(connect(path)) as conn:
        conn.execute("BEGIN")
        try:
            yield conn
        finally:
            conn.execute("ROLLBACK")


class Writer:
    """One save's view of the file: reads see this transaction's own versions."""

    def __init__(
        self, conn: sqlite3.Connection, action: str, detail: str | None
    ) -> None:
        self._conn = conn
        self._action = action
        self._detail = detail
        self.rev: int | None = None  # None until the first add

    def head(self, kind: Kind, name: str) -> Row | None:
        """The entity's highest version, tombstone or not, inside this transaction."""
        rows = history(self._conn, kind, name)
        return rows[0] if rows else None

    def heads(self) -> list[Row]:
        """Every live head inside this transaction, this save's versions included."""
        return heads(self._conn)

    def add(
        self,
        kind: Kind,
        name: str,
        *,
        yaml: str | None,
        deleted: bool = False,
        attached: Sequence[str] | None = None,
        slug: str | None = None,
        use_when: str | None = None,
        hint: str | None = None,
        source: str | None = None,
    ) -> int:
        """Insert the next version (creating this save's revision first); return its number."""
        if self.rev is None:
            self.rev = current_rev(self._conn) + 1
            at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._conn.execute(
                "INSERT INTO revisions (rev, at, action, detail) VALUES (?, ?, ?, ?)",
                (self.rev, at, self._action, self._detail),
            )
        head = self.head(kind, name)
        version = head.version + 1 if head else 1
        self._conn.execute(
            "INSERT INTO versions (kind, name, version, rev, deleted, yaml, attached, slug,"
            " use_when, hint, source, deep_reasoner)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                kind,
                name,
                version,
                self.rev,
                int(deleted),
                yaml,
                json.dumps(list(attached)) if attached is not None else None,
                slug,
                use_when,
                hint,
                source,
                deep_reasoner_build(),
            ),
        )
        return version


@contextlib.contextmanager
def write(path: Path, action: str, detail: str | None = None) -> Iterator[Writer]:
    """BEGIN IMMEDIATE … COMMIT, or ROLLBACK on any exception."""
    with contextlib.closing(connect(path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield Writer(conn, action, detail)
        except BaseException:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")
