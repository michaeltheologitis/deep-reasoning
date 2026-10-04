from pathlib import Path

from deep_reasoning.acp.runlog import Home

LIBRARY_FILE = "library.sqlite"


def library_path(home: Path | None = None) -> Path:
    """Home.resolve(home).root / "library.sqlite": home, else $DR_HOME, else
    ~/.deep-reasoning."""
    return Home.resolve(home).root / LIBRARY_FILE
