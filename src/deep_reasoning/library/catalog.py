"""LibraryCatalog: D1's Catalog over the Library (§4.7).

Nothing of deep_reasoner or of the Library is imported at module level: dr-acp builds
the catalog before it serves, and the first snapshot (in a thread) pays the import.
"""

import dataclasses
import tempfile
from pathlib import Path
from typing import Any

from deep_reasoning.acp.catalog import CatalogSnapshot, CommandEntry, RunSource
from deep_reasoning.acp.runlog import Home

LIBRARY_FILE = "library.sqlite"


def library_path(home: Path | None = None) -> Path:
    """Home.resolve(home).root / "library.sqlite": --home, else $DR_HOME, else
    ~/.deep-reasoning (D1's Home, acp/runlog.py). Here, not in library.py, so that dr-acp
    finds its library without importing deep_reasoner."""
    return Home.resolve(home).root / LIBRARY_FILE


class LibraryCatalog:
    """D1's Catalog (deep_reasoning.acp.catalog) over the Library at path."""

    def __init__(self, path: Path) -> None:
        """Stores the path; opens nothing and imports nothing until first used, then
        Library.open(path), which creates the library with the starter if it is absent."""
        self.path = path
        self._library: Any = None

    def _open(self) -> Any:
        from deep_reasoning.library.library import Library

        if self._library is None:
            self._library = Library.open(self.path)
        return self._library

    def snapshot(self) -> CatalogSnapshot:
        """Materialize into a temporary directory; take ConfigCatalog(main).snapshot();
        on each CommandEntry put the decomposition's use-when line (description) and
        hint where the Library has them; delete the directory."""
        from deep_reasoning.acp.catalog import ConfigCatalog

        library = self._open()
        state = library.state()
        with tempfile.TemporaryDirectory(prefix="dr-library-") as tmp:
            config = library.materialize(Path(tmp) / "config", rev=state.rev)
            snapshot = ConfigCatalog(config / "main.yaml").snapshot()

        def described(entry: CommandEntry) -> CommandEntry:
            record = state.decompositions[entry.decomposition]
            return dataclasses.replace(
                entry,
                description=record.use_when or entry.description,
                hint=record.hint or entry.hint,
            )

        commands = {
            ns: tuple(described(entry) for entry in entries)
            for ns, entries in snapshot.commands.items()
        }
        return dataclasses.replace(snapshot, commands=commands)

    def materialize(self, namespace: str, *, run_dir: Path) -> RunSource:
        """Library.materialize(run_dir / "config", namespace=namespace) (LibraryNotFound
        for a namespace that is not live); then ConfigCatalog(main).materialize(namespace,
        run_dir=run_dir) with versions replaced by the manifest's versions()."""
        import yaml

        from deep_reasoning.acp.catalog import ConfigCatalog
        from deep_reasoning.library.records import Manifest

        config = self._open().materialize(run_dir / "config", namespace=namespace)
        manifest = Manifest.model_validate(
            yaml.safe_load((config / "library.yaml").read_text())
        )
        source = ConfigCatalog(config / "main.yaml").materialize(
            namespace, run_dir=run_dir
        )
        return dataclasses.replace(source, versions=manifest.versions())
