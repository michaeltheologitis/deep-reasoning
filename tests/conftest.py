from contextlib import closing
from pathlib import Path

import pytest

from deep_reasoning.library import import_config, open_library

# Copies of deep_reasoner 0.3.0's docs/configs, in their layout, so _compose paths still resolve.
CONFIGS = Path(__file__).parent / "configs"


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    """A home directory of the test's own, so no test touches the real ~/.deep-reasoning."""
    path = tmp_path / "home"
    path.mkdir()
    monkeypatch.setenv("HOME", str(path))
    return path


@pytest.fixture
def advisors():
    return CONFIGS / "catalog" / "advisors.yaml"


@pytest.fixture
def waitlist():
    return CONFIGS / "examples" / "waitlist" / "waitlist.yaml"


@pytest.fixture
def library(tmp_path):
    return tmp_path / "library.sqlite"


@pytest.fixture
def imported(library, advisors):
    """A Library holding advisors.yaml."""
    with closing(open_library(library)) as connection:
        import_config(connection, advisors)
    return library
