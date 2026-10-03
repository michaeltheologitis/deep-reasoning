"""Library: the Python API over one library file (§4.5)."""

import contextlib
import shutil
import tempfile
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, Literal, get_args

import yaml
from pydantic import ValidationError

from deep_reasoning.library import configdir, shapes, store, texts
from deep_reasoning.library.catalog import library_path
from deep_reasoning.library.effective import Effective, effective
from deep_reasoning.library.records import (
    Change,
    DecompositionMeta,
    DecompositionRecord,
    Entry,
    FieldError,
    HistoryEntry,
    ImportReport,
    Kind,
    LibraryConflict,
    LibraryNotFound,
    LibraryRefused,
    LibraryState,
    LibraryValidationError,
    NamespaceRecord,
    Problem,
    ProfileRecord,
    ToolRecord,
    ValidationResult,
)
from deep_reasoning.library.store import Row, Writer

STARTER = Path(__file__).with_name("starter.yaml")
ROOT = "root"
PROFILE = "profile"


def _refuse(sentence: str, loc: str) -> LibraryValidationError:
    return LibraryValidationError(sentence, [FieldError(loc=loc, msg=sentence)])


def _parent(name: str) -> str:
    return name.rpartition(".")[0] or ROOT


def _default_namespace(profile_yaml: str) -> str:
    return (yaml.safe_load(profile_yaml) or {}).get("entry_namespace", ROOT)


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


def _records(state: LibraryState) -> dict[Kind, dict[str, Any]]:
    """Every live head's record, by kind, then by name."""
    return {
        "profile": {PROFILE: state.profile},
        "namespace": state.namespaces,
        "decomposition": state.decompositions,
        "tool": state.tools,
    }


def _check_invariants(rows: list[Row]) -> None:
    """§2.5, over every live head inside the save's transaction."""
    live = {(r.kind, r.name) for r in rows}
    if ("profile", PROFILE) not in live or ("namespace", ROOT) not in live:
        raise LibraryRefused(texts.REFUSE_ROOT)
    namespaces = [r for r in rows if r.kind == "namespace"]
    for ns in namespaces:
        if ns.name != ROOT and ("namespace", _parent(ns.name)) not in live:
            raise _refuse(texts.parent_missing(ns.name, _parent(ns.name)), "name")
    [profile] = [r for r in rows if r.kind == "profile"]
    default = _default_namespace(profile.yaml)
    if ("namespace", default) not in live:
        raise _refuse(texts.default_missing(default), "entry_namespace")
    by_slug: dict[str, str] = {}
    for d in (r for r in rows if r.kind == "decomposition"):
        other = by_slug.setdefault(d.slug, d.name)
        if other != d.name:
            raise _refuse(texts.slug_taken(d.name, d.slug, other), "name")
    for holder in [profile, *namespaces]:
        where = (
            "the top level"
            if holder.kind == "profile"
            else f"namespace '{holder.name}'"
        )
        seen: set[str] = set()
        for name in holder.decompositions or []:
            if ("decomposition", name) not in live:
                raise _refuse(texts.unknown_decomposition(name), "decompositions")
            if name in seen:
                raise _refuse(texts.listed_twice(name, where), "decompositions")
            seen.add(name)


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


def _live(w: Writer, kind: Kind, name: str) -> Row | None:
    head = w.head(kind, name)
    return head if head is not None and not head.deleted else None


def _live_namespaces(w: Writer, named: Sequence[str], loc: str) -> list[Row]:
    """Every live namespace; a name in named that is not one is refused, at loc."""
    namespaces = [r for r in w.heads() if r.kind == "namespace"]
    live = {ns.name for ns in namespaces}
    if unknown := [name for name in named if name not in live]:
        raise _refuse(texts.not_found("namespace", unknown[0]), loc)
    return namespaces


def _toggled(names: list[str], name: str, wanted: bool) -> list[str]:
    """names with name appended when wanted, else without it."""
    return [*names, name] if wanted else [n for n in names if n != name]


def _attached_set(w: Writer, decomposition: str, wanted: Sequence[str]) -> None:
    """Make wanted the exact set of namespaces whose lists name decomposition."""
    for ns in _live_namespaces(w, wanted, "namespaces"):
        want = ns.name in wanted
        if (decomposition in ns.decompositions) != want:
            listed = _toggled(ns.decompositions, decomposition, want)
            _add(w, "namespace", ns.name, yaml=ns.yaml, decompositions=listed)


def _top_level(w: Writer, decomposition: str, wanted: bool) -> None:
    profile = w.head("profile", PROFILE)
    if (decomposition in profile.decompositions) != wanted:
        listed = _toggled(profile.decompositions, decomposition, wanted)
        _add(w, "profile", PROFILE, yaml=profile.yaml, decompositions=listed)


def _granted_set(w: Writer, tool: str, wanted: Sequence[str]) -> None:
    """Make wanted the exact set of namespaces whose tools list names tool."""
    for ns in _live_namespaces(w, wanted, "granted_in"):
        tools, want = yaml.safe_load(ns.yaml).get("tools", []), ns.name in wanted
        if (tool in tools) != want:
            granted = _with_tools(ns, _toggled(tools, tool, want))
            _add(
                w, "namespace", ns.name, yaml=granted, decompositions=ns.decompositions
            )


def _with_tools(ns: Row, tools: list[str]) -> str:
    data = yaml.safe_load(ns.yaml)
    data.pop("tools", None)
    if tools:
        data["tools"] = tools
    return shapes.validate_namespace(shapes.canonical_yaml(data)).yaml


def _first_error(exc: LibraryValidationError) -> str:
    first = exc.errors[0]
    return f"{first.loc}: {first.msg}" if first.loc else first.msg


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

    def effective(self, namespace: str) -> Effective:
        """What namespace inherits; a stale head is LibraryValidationError, as at
        materialize."""
        state = self.state()
        self._get(state.namespaces, "namespace", namespace)
        try:
            return effective(state, namespace)
        except ValidationError:
            _refuse_stale(state)
            raise

    def check(self) -> list[Problem]:
        """Every live head re-validated under the installed deep_reasoner, plus granted
        tools the Library does not define and spawn targets it does not hold."""
        state = self.state()
        problems = _stale(state)
        has_model = bool(state.profile.data.get("model"))
        for ns in state.namespaces.values():
            for tool in ns.data.get("tools", []):
                if tool not in state.tools and not (tool == "llm" and has_model):
                    problems.append(
                        Problem(
                            kind="namespace",
                            name=ns.name,
                            message=texts.unknown_tool(ns.name, tool),
                        )
                    )
            for target in ns.data.get("spawn") or []:
                if target not in state.namespaces:
                    problems.append(
                        Problem(
                            kind="namespace",
                            name=ns.name,
                            message=texts.unknown_spawn(ns.name, target),
                        )
                    )
        return problems

    def validate(
        self,
        kind: Kind,
        text: str,
        *,
        name: str | None = None,
        source: str | None = None,
    ) -> ValidationResult:
        """Validate without saving. name is the tool's (a tool's YAML does not carry it);
        source is a tool's Python file, when it has one."""
        try:
            shaped = _validator(kind, name, source)(text)
        except LibraryValidationError as exc:
            key = name if kind == "tool" else _yaml_name(kind, text)
            return ValidationResult(
                ok=False,
                message=str(exc),
                errors=exc.errors,
                warnings=[],
                name=key,
                slug=shapes.slug(key) if kind == "decomposition" and key else None,
                yaml=None,
            )
        return ValidationResult(
            ok=True,
            message=None,
            errors=[],
            warnings=shaped.warnings,
            name=shaped.name,
            slug=shapes.slug(shaped.name) if kind == "decomposition" else None,
            yaml=shaped.yaml,
        )

    # ── writes: each one revision (or none, when nothing changes) ──────────────────

    def put_profile(
        self,
        text: str,
        *,
        decompositions: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> ProfileRecord:
        shaped = shapes.validate_profile(text)
        with self._save("put profile", None) as w:
            head = self._base(w, "profile", PROFILE, base_version)
            if decompositions is None:
                decompositions = head.decompositions
            _add(w, "profile", PROFILE, yaml=shaped.yaml, decompositions=decompositions)
            return self._read_back(w, "profile", PROFILE)

    def put_namespace(
        self,
        text: str,
        *,
        decompositions: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> NamespaceRecord:
        shaped = shapes.validate_namespace(text)
        name = shaped.name
        with self._save("put namespace", name) as w:
            head = self._base(w, "namespace", name, base_version)
            if decompositions is None:
                decompositions = head.decompositions if head else []
            _add(w, "namespace", name, yaml=shaped.yaml, decompositions=decompositions)
            return self._read_back(w, "namespace", name)

    def put_decomposition(
        self,
        text: str,
        *,
        use_when: str | None = None,
        hint: str | None = None,
        namespaces: Sequence[str] | None = None,
        top_level: bool | None = None,
        base_version: int | None = None,
    ) -> DecompositionRecord:
        shaped = shapes.validate_decomposition(text)
        name = shaped.name
        with self._save("put decomposition", name) as w:
            self._base(w, "decomposition", name, base_version)
            _add(
                w,
                "decomposition",
                name,
                yaml=shaped.yaml,
                slug=shapes.slug(name),
                use_when=use_when or None,
                hint=hint or None,
            )
            if namespaces is not None:
                _attached_set(w, name, namespaces)
            if top_level is not None:
                _top_level(w, name, top_level)
            return self._read_back(w, "decomposition", name)

    def put_tool(
        self,
        name: str,
        text: str,
        *,
        source: str | None = None,
        granted_in: Sequence[str] | None = None,
        base_version: int | None = None,
    ) -> ToolRecord:
        shaped = shapes.validate_tool(name, text, source)
        with self._save("put tool", name) as w:
            self._base(w, "tool", name, base_version)
            _add(w, "tool", name, yaml=shaped.yaml, source=source)
            if granted_in is not None:
                _granted_set(w, name, granted_in)
            return self._read_back(w, "tool", name)

    def delete(
        self,
        kind: Literal["namespace", "decomposition", "tool"],
        key: str,
        *,
        base_version: int | None = None,
    ) -> HistoryEntry:
        """Write a tombstone; cascades as §2.3 says; returns the tombstone."""
        name = self.decomposition(key).name if kind == "decomposition" else key
        with self._save(f"delete {kind}", name) as w:
            head = self._base(w, kind, name, base_version)
            if head is None:
                raise LibraryNotFound(texts.not_found(kind, name))
            if kind == "namespace":
                _refuse_namespace_delete(w, name)
            w.add(kind, name, yaml=None, deleted=True, slug=head.slug)
            if kind == "decomposition":
                _attached_set(w, name, [])
                _top_level(w, name, False)
            if kind == "tool":
                _granted_set(w, name, [])
            return w.head(kind, name)

    def import_config(self, path: str | Path) -> ImportReport:
        """A dr config (its main YAML, or a directory holding main.yaml), merged by name."""
        parts = configdir.read_config(Path(path))
        return self._import(parts, "import", str(parts.main))

    # ── files ───────────────────────────────────────────────────────────────────

    def materialize(
        self,
        dest: Path | None = None,
        *,
        namespace: str | None = None,
        rev: int | None = None,
    ) -> Path:
        """Write the Library (as of rev) as a plain dr config directory and return it.
        dest: absent or empty (default: a new temporary directory); namespace: the entry
        namespace written into main.yaml (default: the profile's)."""
        state = self.state(rev=rev)
        namespace = namespace or state.profile.default_namespace
        self._get(state.namespaces, "namespace", namespace)
        _refuse_stale(state)
        if dest is not None and dest.exists() and any(dest.iterdir()):
            raise LibraryRefused(texts.dest_not_empty(str(dest)))
        made = dest is None or not dest.exists()
        dest = Path(tempfile.mkdtemp(prefix="dr-library-")) if dest is None else dest
        dest.mkdir(parents=True, exist_ok=True)
        try:
            configdir.write_config(state, dest, namespace=namespace)
        except BaseException:
            _empty(dest, remove=made)
            raise
        return dest

    # ── internals ───────────────────────────────────────────────────────────────

    @contextlib.contextmanager
    def _save(self, action: str, detail: str | None) -> Iterator[Writer]:
        """One store.write whose changes must keep §2.5's invariants."""
        with store.write(self.path, action, detail) as w:
            yield w
            if w.rev is not None:
                _check_invariants(w.heads())

    def _get(self, records: dict[str, Any], kind: Kind, key: str) -> Any:
        if key not in records:
            raise LibraryNotFound(texts.not_found(kind, key))
        return records[key]

    def _read_back(self, w: Writer, kind: Kind, name: str) -> Any:
        """The entity's record as this transaction sees it."""
        rows = w.heads()
        state = _state(self.path, rows, max(r.rev for r in rows))
        return _records(state)[kind].get(name)

    def _base(
        self, w: Writer, kind: Kind, name: str, base_version: int | None
    ) -> Row | None:
        """The live head, after checking base_version against it (§4.5)."""
        head = _live(w, kind, name)
        if base_version is None:
            return head
        if base_version == 0 and head is not None:
            raise LibraryConflict(
                texts.conflict_exists(kind, name, head.version),
                self._read_back(w, kind, name),
            )
        if base_version >= 1 and head is None:
            raise LibraryNotFound(texts.not_found(kind, name))
        if base_version >= 1 and head.version != base_version:
            raise LibraryConflict(
                texts.conflict_stale(kind, name, head.version, base_version),
                self._read_back(w, kind, name),
            )
        return head

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


def _refuse_namespace_delete(w: Writer, name: str) -> None:
    if name == ROOT:
        raise LibraryRefused(texts.REFUSE_ROOT)
    if name == _default_namespace(w.head("profile", PROFILE).yaml):
        raise LibraryRefused(texts.refuse_default(name))
    children = [
        r.name
        for r in w.heads()
        if r.kind == "namespace" and r.name.startswith(f"{name}.")
    ]
    if children:
        raise LibraryRefused(texts.refuse_children(name, children))


def _validator(
    kind: Kind, name: str | None, source: str | None
) -> Callable[[str], shapes.Shaped]:
    if kind == "tool":
        return lambda text: shapes.validate_tool(name or "", text, source)
    return {
        "profile": shapes.validate_profile,
        "namespace": shapes.validate_namespace,
        "decomposition": shapes.validate_decomposition,
    }[kind]


def _yaml_name(kind: Kind, text: str) -> str | None:
    """The entity's key, when the YAML parses far enough to have one."""
    if kind == "profile":
        return PROFILE
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    name = data.get("name") if isinstance(data, dict) else None
    return name if isinstance(name, str) else None


def _stale(state: LibraryState) -> list[Problem]:
    """Every live head that no longer validates under the installed deep_reasoner."""
    problems = []
    for kind, records in _records(state).items():
        for name, record in records.items():
            source = record.source if kind == "tool" else None
            try:
                _validator(kind, name, source)(record.yaml)
            except LibraryValidationError as exc:
                message = texts.stale_head(
                    kind,
                    name,
                    record.version,
                    shapes.deep_reasoner_build(),
                    _first_error(exc),
                )
                problems.append(Problem(kind=kind, name=name, message=message))
    return problems


def _refuse_stale(state: LibraryState) -> None:
    """LibraryValidationError with one STALE_HEAD sentence per stale head, if any."""
    if problems := _stale(state):
        sentences = [p.message for p in problems]
        raise LibraryValidationError(
            "\n".join(sentences), [FieldError(loc="", msg=s) for s in sentences]
        )


def _empty(dest: Path, *, remove: bool) -> None:
    """Undo a failed write: remove dest if we made it, else everything written into it."""
    if remove:
        shutil.rmtree(dest, ignore_errors=True)
        return
    for child in dest.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def _seed_bare(path: Path) -> None:
    with store.write(path, "create") as w:
        w.add("profile", PROFILE, yaml=shapes.canonical_yaml({}), attached=[])
        w.add(
            "namespace", ROOT, yaml=shapes.canonical_yaml({"name": ROOT}), attached=[]
        )


def _seed_starter(path: Path) -> None:
    Library(path)._import(configdir.read_config(STARTER), "create", str(STARTER))
