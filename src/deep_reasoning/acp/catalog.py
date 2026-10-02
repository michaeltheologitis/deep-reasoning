"""What a conversation can run: namespaces and their slash commands (§4.6, D2's seam)."""

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
    raise NotImplementedError


def load_dr_config(path: Path) -> Any:
    """load_cli_config(path, schema=V2Config), a relative namespaces_dir resolved
    against the config's directory, as dr does."""
    raise NotImplementedError


class ConfigCatalog:
    """The catalog of one plain dr config, until D2's Library."""

    def __init__(self, path: Path) -> None: ...

    def snapshot(self) -> CatalogSnapshot:
        """Namespaces: root, the config's inline ones, the namespaces_dir ones. Each
        namespace's menu: the decompositions main_decomposition_turns can find from it,
        config first, then the namespace's, first name wins."""
        raise NotImplementedError

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """The given path unchanged, its client block, and its sha256."""
        raise NotImplementedError
