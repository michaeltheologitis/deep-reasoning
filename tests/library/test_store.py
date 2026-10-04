import sqlite3
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from deep_reasoning.library import store
from deep_reasoning.library.records import LibraryError


def seed(path: Path) -> None:
    with store.write(path, "create") as w:
        w.add("profile", "profile", yaml="{}\n", attached=[])
        w.add("namespace", "root", yaml="name: root\n", attached=[])


@pytest.fixture
def db(tmp_path: Path) -> Path:
    path = tmp_path / "home" / "library.sqlite"
    assert store.create(path, seed)
    return path


def names(rows: list[store.Row]) -> list[tuple[str, str, int]]:
    return [(r.kind, r.name, r.version) for r in rows]


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE versions SET yaml = 'x'",
        "DELETE FROM versions",
        "UPDATE revisions SET action = 'x'",
        "DELETE FROM revisions",
    ],
)
def test_versions_and_revisions_cannot_be_updated_or_deleted(db, statement):
    conn = store.connect(db)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        conn.execute(statement)


def test_a_migration_that_fails_halfway_leaves_the_file_unmigrated(
    tmp_path, monkeypatch
):
    path = tmp_path / "library.sqlite"
    twice = "CREATE TABLE a (x);\nCREATE TABLE a (x);\n"
    monkeypatch.setattr(store, "MIGRATIONS", (twice,))
    with pytest.raises(sqlite3.OperationalError, match="already exists"):
        store.connect(path)
    conn = sqlite3.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone() == (0,)
    assert conn.execute("SELECT name FROM sqlite_master").fetchall() == []


def test_a_save_that_changes_nothing_makes_no_revision(db):
    with store.write(db, "put namespace", "root") as w:
        assert w.head("namespace", "root").version == 1
    with store.read(db) as conn:
        assert store.current_rev(conn) == 1


def test_one_save_is_one_revision_however_many_versions_it_writes(db):
    with store.write(db, "import", "x.yaml") as w:
        assert w.add("namespace", "a", yaml="name: a\n", attached=[]) == 1
        assert w.add("namespace", "root", yaml="name: root\n", attached=["d"]) == 2
        assert w.rev == 2
    with store.read(db) as conn:
        assert store.current_rev(conn) == 2
        assert {r.rev for r in store.heads(conn)} == {1, 2}


def test_heads_as_of_a_revision_ignore_later_versions(db):
    with store.write(db, "put namespace", "a") as w:
        w.add("namespace", "a", yaml="name: a\n", attached=[])
    with store.write(db, "put namespace", "a") as w:
        w.add("namespace", "a", yaml="name: a\ntools: [llm]\n", attached=[])
    with store.write(db, "delete namespace", "a") as w:
        w.add("namespace", "a", yaml=None, deleted=True)
    with store.read(db) as conn:
        assert names(store.heads(conn, rev=1)) == [
            ("profile", "profile", 1),
            ("namespace", "root", 1),
        ]
        assert names(store.heads(conn, rev=3))[-1] == ("namespace", "a", 2)
        assert names(store.heads(conn)) == names(store.heads(conn, rev=1))
        assert [r.version for r in store.history(conn, "namespace", "a")] == [3, 2, 1]


def test_heads_are_in_creation_order_within_one_revision(db):
    with store.write(db, "import") as w:
        for name in ("zeta", "alpha", "mid"):
            w.add("namespace", name, yaml=f"name: {name}\n", attached=[])
    with store.read(db) as conn:
        assert [r.name for r in store.heads(conn)][2:] == ["zeta", "alpha", "mid"]


def test_an_exception_inside_a_save_writes_nothing(db):
    with pytest.raises(RuntimeError), store.write(db, "import") as w:
        w.add("namespace", "a", yaml="name: a\n", attached=[])
        raise RuntimeError("halfway")
    with store.read(db) as conn:
        assert store.current_rev(conn) == 1


def test_a_new_library_file_is_private_to_its_user(db):
    assert stat.S_IMODE(db.stat().st_mode) == 0o600
    assert stat.S_IMODE(db.parent.stat().st_mode) & 0o077 == 0
    with store.read(db) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        for sidecar in (Path(f"{db}-wal"), Path(f"{db}-shm")):
            assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600


def test_a_second_creator_loses_and_leaves_nothing_behind(db):
    assert not store.create(db, seed)
    assert sorted(p.name for p in db.parent.iterdir()) == ["library.sqlite"]


WRITER = textwrap.dedent(
    """
    import sys
    from pathlib import Path
    from deep_reasoning.library import store

    path, who = Path(sys.argv[1]), sys.argv[2]
    for i in range(20):
        with store.write(path, "put namespace", who) as w:
            w.add("namespace", f"{who}{i}", yaml=f"name: {who}{i}\\n", attached=[])
    """
)


def test_two_processes_saving_at_once_both_land(db):
    writers = [
        subprocess.Popen([sys.executable, "-c", WRITER, str(db), who])
        for who in ("a", "b")
    ]
    assert [p.wait(timeout=60) for p in writers] == [0, 0]
    with store.read(db) as conn:
        assert store.current_rev(conn) == 41
        assert len(store.heads(conn)) == 42


def test_a_library_on_a_network_filesystem_is_refused(tmp_path):
    mounts = tmp_path / "mounts"
    shared = tmp_path / "nfs home"
    mounts.write_text(
        "/dev/sda1 / ext4 rw,relatime 0 0\n"
        f"server:/export {str(shared).replace(' ', chr(92) + '040')} nfs4 rw 0 0\n"
    )
    with pytest.raises(LibraryError, match=r"network filesystem \(nfs4\)"):
        store.connect(shared / "u" / "library.sqlite", mounts=mounts)
    store.connect(tmp_path / "library.sqlite", mounts=mounts).close()
