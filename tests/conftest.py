import importlib
import sys
from pathlib import Path

import pytest

# juplit.test() is true in any process that has imported pytest, so deep_reasoner's
# modules would run their notebook tests when first imported here. Import them once with
# pytest out of sight.
_pytest = sys.modules.pop("pytest")
try:
    for module in (
        "deep_reasoner.v2.cli",
        "deep_reasoner.mocks",
        "deep_reasoner.v2.decompositions",
        "deep_reasoner.v2.messages",
    ):
        importlib.import_module(module)
finally:
    sys.modules["pytest"] = _pytest


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """$DR_HOME for one test: run logs, session indexes, prices."""
    return tmp_path / "home"


@pytest.fixture
def work(tmp_path: Path) -> Path:
    """The conversation's working folder: the worker's cwd."""
    path = tmp_path / "work"
    path.mkdir()
    return path
