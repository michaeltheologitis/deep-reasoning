import contextlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, get_args

import yaml

from deep_reasoning.library import configdir, shapes, store, texts
from deep_reasoning.library.catalog import library_path
from deep_reasoning.library.records import (
    Change,
    DecompositionMeta,
    DecompositionRecord,
    Entry,
    HistoryEntry,
    ImportReport,
    Kind,
    LibraryNotFound,
    LibraryState,
    NamespaceRecord,
    ProfileRecord,
    ToolRecord,
)
from deep_reasoning.library.store import Row, Writer

STARTER = Path(__file__).with_name("starter.yaml")
ROOT = "root"
PROFILE = "profile"


class Library:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def open(cls, path: Path | None = None, *, starter: bool = True) -> "Library":
        """Open path (default library_path()), creating it when absent: revision 1 is the
        starter's import, or, with starter=False, an empty profile and a bare root."""
        path = Path(path) if path is not None else library_path()
        if not path.exists():
            store.create(path, _seed_starter if starter else _seed_bare)
        store.connect(path).close()
        return cls(path)

    # ── reads: each one read transaction ──────────────────────────────────────────

    def rev(self) -> int:
        with store.read(self.path) as conn:
            return store.current_rev(conn)

    def state(self, *, rev: int | None = None) -> LibraryState:
        with store.read(self.path) as conn:
            current = store.current_rev(conn)
            if rev is not None and not 1 <= rev <= current:
                raise LibraryNotFound(texts.no_revision(rev, current))
            as_of = current if rev is None else rev
            return _state(self.path, store.heads(conn, rev=as_of), as_of)

    def profile(self) -> ProfileRecord:
        return self.state().profile

    def namespaces(self) -> list[NamespaceRecord]:
        """Root first, then creation order."""
        return list(self.state().namespaces.values())

    def namespace(self, name: str) -> NamespaceRecord:
        return self._get(self.state().namespaces, "namespace", name)

    def decompositions(self) -> list[DecompositionRecord]:
        """By slug."""
        return list(self.state().decompositions.values())

    def decomposition(self, key: str) -> DecompositionRecord:
        """key is a name or a slug: both are unique, and no name is another's slug."""
        found = self.state().decompositions
        by_slug = {d.slug: d for d in found.values()}
        return self._get({**by_slug, **found}, "decomposition", key)

    def tools(self) -> list[ToolRecord]:
        return list(self.state().tools.values())

    def tool(self, name: str) -> ToolRecord:
        return self._get(self.state().tools, "tool", name)

    def history(self, kind: Kind, key: str) -> list[HistoryEntry]:
        """Newest first, tombstones included; works for deleted entities."""
        with store.read(self.path) as conn:
            rows = store.history(conn, kind, key)
            if not rows and kind == "decomposition":
                named = store.decomposition_named(conn, key)
                rows = store.history(conn, kind, named) if named else []
        if not rows:
            raise LibraryNotFound(texts.not_found(kind, key))
        return rows

    # ── writes: each one revision (or none, when nothing changes) ──────────────────

    def import_config(self, path: str | Path) -> ImportReport:
        """A dr config (its main YAML, or a directory holding main.yaml), merged by name."""
        parts = configdir.read_config(Path(path))
        return self._import(parts, "import", str(parts.main))

    # ── internals ───────────────────────────────────────────────────────────────

    @contextlib.contextmanager
    def _save(self, action: str, detail: str | None) -> Iterator[Writer]:
        with store.write(self.path, action, detail) as w:
            yield w

    def _get(self, records: dict[str, Any], kind: Kind, key: str) -> Any:
        if key not in records:
            raise LibraryNotFound(texts.not_found(kind, key))
        return records[key]

    def _import(
        self, parts: configdir.ConfigParts, action: str, detail: str
    ) -> ImportReport:
        """Validate every part, then write each one that differs from its head, in one
        revision: decompositions, tools, namespaces root first, then the profile."""
        decompositions = {
            name: shapes.validate_decomposition(shapes.canonical_yaml(body))
            for name, body in parts.decompositions.items()
        }
        tools = {
            name: (
                shapes.validate_tool(name, shapes.canonical_yaml(block), source),
                source,
            )
            for name, (block, source) in parts.tools.items()
        }
        namespaces = [
            (shapes.validate_namespace(shapes.canonical_yaml(data)), attached)
            for data, attached in parts.namespaces
        ]
        profile = shapes.validate_profile(shapes.canonical_yaml(parts.profile))
        changed: list[Change] = []
        unchanged: list[Entry] = []

        def put(w: Writer, kind: Kind, name: str, **fields: Any) -> None:
            was_live = _live(w, kind, name) is not None
            version = _add(w, kind, name, **fields)
            if version is None:
                unchanged.append(Entry(kind=kind, name=name))
            else:
                changed.append(
                    Change(kind=kind, name=name, version=version, created=not was_live)
                )

        with self._save(action, detail) as w:
            for name, shaped in decompositions.items():
                head = _live(w, "decomposition", name)
                kept = (
                    DecompositionMeta.model_validate(head, from_attributes=True)
                    if head
                    else DecompositionMeta()
                )
                meta = parts.metadata.get(name, kept)
                put(
                    w,
                    "decomposition",
                    name,
                    yaml=shaped.yaml,
                    slug=shapes.slug(name),
                    use_when=meta.use_when,
                    hint=meta.hint,
                )
            for name, (shaped, source) in tools.items():
                put(w, "tool", name, yaml=shaped.yaml, source=source)
            for shaped, attached in namespaces:
                put(
                    w,
                    "namespace",
                    shaped.name,
                    yaml=shaped.yaml,
                    decompositions=attached,
                )
            put(
                w, "profile", PROFILE, yaml=profile.yaml, decompositions=parts.top_level
            )
        return ImportReport(
            source=parts.main, rev=w.rev, changed=changed, unchanged=unchanged
        )


def _live(w: Writer, kind: Kind, name: str) -> Row | None:
    head = w.head(kind, name)
    return head if head is not None and not head.deleted else None


def _add(w: Writer, kind: Kind, name: str, **fields: Any) -> int | None:
    """Write the next version unless the head is live and equal; the version written.
    fields: yaml, and decompositions, slug, use_when, hint and source (default None)."""
    fields = (
        dict.fromkeys(("decompositions", "slug", "use_when", "hint", "source")) | fields
    )
    if fields["decompositions"] is not None:
        fields["decompositions"] = list(fields["decompositions"])
    head = _live(w, kind, name)
    if head and head.model_dump(include=set(fields)) == fields:
        return None
    return w.add(kind, name, attached=fields.pop("decompositions"), **fields)


# ── records from live heads ───────────────────────────────────────────────────────────


def _state(path: Path, rows: list[Row], rev: int) -> LibraryState:
    """Records from live heads: derived lists (namespaces, top_level, granted_in) included."""
    of = {
        kind: [r.model_dump() for r in rows if r.kind == kind]
        for kind in get_args(Kind)
    }
    for listing in of["profile"] + of["namespace"]:
        listing["decompositions"] = listing["decompositions"] or []
    [p] = of["profile"]
    profile = ProfileRecord.model_validate(
        {**p, "default_namespace": _default_namespace(p["yaml"])}
    )
    ordered = sorted(of["namespace"], key=lambda r: r["name"] != ROOT)
    namespaces = {r["name"]: NamespaceRecord.model_validate(r) for r in ordered}

    def derived(name: str, listed: Callable[[NamespaceRecord], list[str]]) -> list[str]:
        return [n for n, ns in namespaces.items() if name in listed(ns)]

    decompositions = {
        r["name"]: DecompositionRecord.model_validate(
            {
                **r,
                "namespaces": derived(r["name"], lambda ns: ns.decompositions),
                "top_level": r["name"] in profile.decompositions,
            }
        )
        for r in sorted(of["decomposition"], key=lambda r: r["slug"])
    }
    tools = {
        r["name"]: ToolRecord.model_validate(
            {**r, "granted_in": derived(r["name"], lambda ns: ns.data.get("tools", []))}
        )
        for r in of["tool"]
    }
    return LibraryState(
        path=path,
        rev=rev,
        profile=profile,
        namespaces=namespaces,
        decompositions=decompositions,
        tools=tools,
    )


def _default_namespace(profile_yaml: str) -> str:
    return (yaml.safe_load(profile_yaml) or {}).get("entry_namespace", ROOT)


# ── files: a failed write undone, and a new library's first revision ──────────────────


def _seed_bare(path: Path) -> None:
    with store.write(path, "create") as w:
        w.add("profile", PROFILE, yaml=shapes.canonical_yaml({}), attached=[])
        w.add(
            "namespace", ROOT, yaml=shapes.canonical_yaml({"name": ROOT}), attached=[]
        )


def _seed_starter(path: Path) -> None:
    Library(path)._import(configdir.read_config(STARTER), "create", str(STARTER))
