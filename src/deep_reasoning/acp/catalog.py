"""What a conversation can run: namespaces and their slash commands (§4.6, D2's seam)."""

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class CommandEntry:
    name: str  # the slash command without "/": the decomposition name, slugged
    decomposition: str  # the name main_decomposition_turns looks up
    description: str  # the use-when line
    hint: str  # shown until the task is typed


@dataclass(frozen=True)
class CatalogSnapshot:
    namespaces: tuple[str, ...]  # "root" first, then by name
    default_namespace: str
    commands: Mapping[str, tuple[CommandEntry, ...]]  # namespace -> its menu


@dataclass(frozen=True)
class RunSource:
    config_path: Path  # a plain dr main.yaml the worker loads
    namespace: str  # becomes cfg.entry_namespace
    client: Mapping[str, Any]  # the config's client block as loaded: D5's upstream
    versions: Mapping[str, Any]  # recorded in run.start


class Catalog(Protocol):
    def snapshot(self) -> CatalogSnapshot:
        """Blocking: the front runs it in a thread."""
        ...

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """Blocking: the front runs it in a thread."""
        ...


def slug(name: str) -> str:
    """Lower case, runs of non-alphanumerics -> "-", trimmed."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_dr_config(path: Path) -> Any:
    """load_cli_config(path, schema=V2Config), a relative namespaces_dir resolved
    against the config's directory, as dr does."""
    # deep_reasoner is imported only when a catalog is read (in a thread), never at
    # dr-acp's start-up.
    from deep_reasoner.config import load_cli_config
    from deep_reasoner.v2.cli import V2Config

    cfg = load_cli_config(path, schema=V2Config)
    if cfg.namespaces_dir is not None and not Path(cfg.namespaces_dir).is_absolute():
        cfg.namespaces_dir = str((path.parent / cfg.namespaces_dir).resolve())
    return cfg


def _menu(decompositions: list[Any]) -> tuple[CommandEntry, ...]:
    """One command per decomposition name, first occurrence winning; colliding slugs
    numbered in menu order."""
    entries: list[CommandEntry] = []
    seen_names: set[str] = set()
    taken: set[str] = set()
    for decomposition in decompositions:
        if decomposition.name in seen_names:
            continue
        seen_names.add(decomposition.name)
        name, n = slug(decomposition.name), 1
        while name in taken:
            n += 1
            name = f"{slug(decomposition.name)}-{n}"
        taken.add(name)
        description = f"Open with the '{decomposition.name}' decomposition"
        entries.append(CommandEntry(name, decomposition.name, description, "the task"))
    return tuple(entries)


class ConfigCatalog:
    """The catalog of one plain dr config, until D2's Library."""

    def __init__(self, path: Path) -> None:
        self._path = path.resolve()

    def snapshot(self) -> CatalogSnapshot:
        """Namespaces: root, the config's inline ones, the namespaces_dir ones. Each
        namespace's menu: the decompositions main_decomposition_turns can find from it,
        config first, then the namespace's, first name wins."""
        from deep_reasoner.namespaces import ROOT, load_namespaces_from_dir
        from deep_reasoner.v2.cli import build_namespace_registry

        cfg = load_dr_config(self._path)
        named = set(cfg.namespaces)
        if cfg.namespaces_dir is not None:
            named |= {ns.name for ns in load_namespaces_from_dir(cfg.namespaces_dir)}
        namespaces = (ROOT, *sorted(named - {ROOT}))
        registry = build_namespace_registry(cfg)
        try:
            commands = {
                ns: _menu([*cfg.decompositions, *registry.resolve(ns).decompositions])
                for ns in namespaces
            }
        finally:
            registry.close()
        return CatalogSnapshot(namespaces, cfg.entry_namespace, commands)

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """The given path unchanged, its client block, and its sha256."""
        cfg = load_dr_config(self._path)
        return RunSource(
            config_path=self._path,
            namespace=namespace,
            client=cfg.client.model_dump(mode="json"),
            versions={
                "config_sha256": hashlib.sha256(self._path.read_bytes()).hexdigest()
            },
        )
