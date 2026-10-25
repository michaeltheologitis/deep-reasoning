from contextlib import closing
from pathlib import Path

import pytest

from deep_reasoning.library import (
    UPSERT_SETTING,
    dump,
    import_config,
    open_library,
    writing,
)

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


@pytest.fixture
def anyio_backend():
    return "asyncio"


def fake_client(fake):
    return {
        "base_url": fake.base_url,
        "api_key_env": "OPENAI_API_KEY",
        "max_retries": 0,
    }


@pytest.fixture
def fake_config(monkeypatch):
    """The engine config for a run whose model is a FakeOpenAI, as Runs.start takes it:
    call it with the fake."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    def config_for(fake, **settings):
        config = {
            "model": "gpt-6-luna",
            "client": fake_client(fake),
            "system_prompt": "You are a scripted test agent.",
            "max_iter": 6,
            "entry_namespace": "root",
        }
        return lambda folder: config | settings

    return config_for


@pytest.fixture
def library_on(library, monkeypatch):
    """A new Library whose run settings reach the model at a FakeOpenAI: call it with
    the fake."""
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    def on(fake):
        with closing(open_library(library)) as connection, writing(connection):
            connection.execute(UPSERT_SETTING, ("client", dump(fake_client(fake))))
        return library

    return on
