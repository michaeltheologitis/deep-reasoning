"""Tool sources to check and save, and a guard for what must start no process."""

from pathlib import Path

import pytest

from deep_reasoning.tools import check

FIXTURES = Path(__file__).parent / "fixtures"


def source(fixture: str) -> str:
    """The text of fixtures/<fixture>.py, a tool's source."""
    return (FIXTURES / f"{fixture}.py").read_text()


@pytest.fixture
def no_process(monkeypatch):
    """Any attempt to start Check's process fails the test."""

    def refuse(*args, **kwargs):
        raise AssertionError("Check started a process")

    monkeypatch.setattr(check.subprocess, "Popen", refuse)
