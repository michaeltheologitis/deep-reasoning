"""D4's routes in the App backend (§7.2) and the gate on D2's PUT /tools/{name} (§3.5)."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from deep_reasoning.library import Library
from deep_reasoning.library.api import create_app
from deep_reasoning.tools import texts
from tests.library.conftest import ROUTER, write_config
from tests.tools.conftest import source

PORT = 8123
ORIGIN = f"http://127.0.0.1:{PORT}"


@pytest.fixture
def lib(tmp_path: Path) -> Library:
    """A Library holding our router config: root, router and courses."""
    library = Library.open(tmp_path / "home" / "library.sqlite", starter=False)
    library.import_config(write_config(tmp_path / "router", ROUTER))
    return library


@pytest.fixture
def client(lib: Library) -> TestClient:
    return TestClient(create_app(lib, same_user=lambda c, s: True), base_url=ORIGIN)


def put_tool(client, name, fixture="word_count", **fields):
    body = {"yaml": "factory: make", "source": source(fixture), "base_version": 0}
    return client.put(f"/tools/{name}", json=body | fields)


def test_check_route_answers_200_with_a_report(client):
    built = client.post(
        "/tools/word_count/check",
        json={
            "yaml": "factory: make",
            "source": source("word_count"),
            "example": 'word_count("a b")',
        },
    )
    failed = client.post(
        "/tools/word_count/check",
        json={"yaml": "factory: make", "source": "def make(:\n"},
    )
    assert (built.status_code, failed.status_code) == (200, 200)
    assert (built.json()["outcome"], built.json()["example"]["value"]) == (
        "built",
        "2",
    )
    assert failed.json()["outcome"] == "syntax"


def test_a_checked_tool_is_saved_with_its_grants(client, lib):
    response = put_tool(client, "word_count", granted_in=["router"])
    assert response.status_code == 201
    record = lib.tool("word_count")
    assert (record.source, record.granted_in, record.data) == (
        source("word_count"),
        ["router"],
        {"factory": "make", "factory_from": "tools/word_count.py"},
    )


@pytest.mark.parametrize(
    ("fixture", "factory", "outcome"),
    [
        ("not_func", "make", "not_func"),
        ("word_count", "mkae", "bad_factory"),
        ("import_error", "make", "import_failed"),
    ],
    ids=["not_func", "misspelled", "import_error"],
)
def test_a_tool_that_cannot_build_is_not_saved(client, lib, fixture, factory, outcome):
    rev = lib.rev()
    response = put_tool(
        client,
        "word_count",
        fixture,
        yaml=f"factory: {factory}",
        accept_check_failure=True,
    )
    assert response.status_code == 422
    body = response.json()
    assert (body["error"], body["message"]) == (
        "check_failed",
        texts.check_failed("word_count"),
    )
    assert (body["check"]["outcome"], body["check"]["can_save_anyway"]) == (
        outcome,
        False,
    )
    assert lib.rev() == rev


def test_a_structural_failure_cannot_be_saved_anyway(client, lib):
    response = client.put(
        "/tools/word_count",
        json={
            "yaml": "factory: make",
            "source": "def make(:\n",
            "base_version": 0,
            "accept_check_failure": True,
        },
    )
    assert (response.status_code, response.json()["check"]["outcome"]) == (
        422,
        "syntax",
    )
    assert "word_count" not in lib.state().tools


def test_save_anyway_stores_a_raising_tool_only_when_asked(client, lib):
    refused = put_tool(client, "word_count", "env_at_build")
    assert refused.status_code == 422
    assert refused.json()["check"]["outcome"] == "raised"
    assert refused.json()["check"]["can_save_anyway"] is True
    assert "word_count" not in lib.state().tools

    saved = put_tool(client, "word_count", "env_at_build", accept_check_failure=True)
    assert saved.status_code == 201
    assert lib.tool("word_count").source == source("env_at_build")


def test_a_grant_only_change_runs_no_check(client, lib, no_process):
    lib.put_tool("word_count", "factory: make", source=source("not_func"))
    response = put_tool(
        client, "word_count", "not_func", granted_in=["router"], base_version=1
    )
    assert response.status_code == 200
    assert (response.json()["version"], response.json()["granted_in"]) == (
        1,
        ["router"],
    )
