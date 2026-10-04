"""D4's routes in the App backend (§7.2) and the gate on D2's PUT /tools/{name} (§3.5)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from deep_reasoning.library import Library
from deep_reasoning.library.api import create_app
from deep_reasoning.mcp.grants import shim_source
from deep_reasoning.mcp.wire import McpServerStatus, remember_seen
from deep_reasoning.tools import texts
from tests.library.conftest import ROUTER, write_config
from tests.tools.conftest import source

PORT = 8123
ORIGIN = f"http://127.0.0.1:{PORT}"
GITHUB = {
    "server": "github",
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
}
GITHUB_YAML = """\
factory: mcp_server
name: github
server: github
transport: stdio
command: npx
args:
- -y
- '@modelcontextprotocol/server-github'
env:
- GITHUB_PERSONAL_ACCESS_TOKEN
factory_from: tools/github.py
"""


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


def grant(client, name="github", **fields):
    body = GITHUB | {"granted_in": ["router"], "base_version": 0}
    return client.put(f"/mcp/{name}", json=body | fields)


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


def test_an_mcp_block_through_put_tools_is_refused(client, no_process):
    response = client.put(
        "/tools/github",
        json={
            "yaml": "factory: mcp_server\nserver: github\n",
            "source": shim_source(),
            "base_version": 0,
        },
    )
    assert response.status_code == 400
    assert response.json()["message"] == texts.mcp_via_grant("github")


@pytest.mark.parametrize("base_version", [0, 1], ids=["new", "the head's"])
def test_a_grant_cannot_replace_a_tool_of_your_own(
    client, lib, no_process, base_version
):
    lib.put_tool("word_count", "factory: make", source=source("word_count"))
    response = grant(client, "word_count", base_version=base_version)
    assert (response.status_code, response.json()["error"]) == (409, "refused")
    assert response.json()["message"] == texts.mcp_name_taken("word_count")
    record = lib.tool("word_count")
    assert (record.version, record.source) == (1, source("word_count"))


@pytest.mark.parametrize("base_version", [0, 1], ids=["new", "the head's"])
def test_a_tool_of_your_own_cannot_replace_a_grant(
    client, lib, no_process, base_version
):
    grant(client)
    response = put_tool(client, "github", base_version=base_version)
    assert (response.status_code, response.json()["error"]) == (409, "refused")
    assert response.json()["message"] == texts.mcp_via_grant("github")
    record = lib.tool("github")
    assert (record.version, record.source) == (1, shim_source())


def test_put_mcp_writes_the_block_and_the_shim_and_grants(client, lib, no_process):
    response = grant(client)
    assert response.status_code == 201
    assert response.json() == {
        "name": "github",
        "version": 1,
        **GITHUB,
        "url": None,
        "headers": [],
        "granted_in": ["router"],
        "shim_current": True,
        "seen": None,
    }
    record = lib.tool("github")
    assert (record.yaml, record.source, record.granted_in) == (
        GITHUB_YAML,
        shim_source(),
        ["router"],
    )


def test_put_mcp_resent_unchanged_makes_no_tool_version(client, lib):
    grant(client)
    response = grant(client, granted_in=["router", "courses"], base_version=1)
    assert response.status_code == 200
    assert (response.json()["version"], response.json()["granted_in"]) == (
        1,
        ["router", "courses"],
    )
    assert [h.version for h in lib.history("tool", "github")] == [1]


def test_a_server_cannot_be_granted_under_two_names(client, lib):
    grant(client)
    response = grant(client, "gh")
    assert response.status_code == 409
    assert (response.json()["error"], response.json()["message"]) == (
        "refused",
        texts.mcp_server_taken("github", "github"),
    )
    assert "gh" not in lib.state().tools


@pytest.mark.parametrize(
    ("fields", "sentence"),
    [
        ({"command": None}, texts.MCP_NEEDS_COMMAND),
        ({"transport": "http", "command": None}, texts.MCP_NEEDS_URL),
        ({"transport": "sse", "command": None, "url": ""}, texts.MCP_NEEDS_URL),
    ],
    ids=["stdio", "http", "sse"],
)
def test_put_mcp_refuses_a_grant_without_its_command_or_url(
    client, lib, fields, sentence
):
    response = grant(client, **fields)
    assert (response.status_code, response.json()["message"]) == (400, sentence)
    assert "github" not in lib.state().tools


@pytest.mark.parametrize(
    ("body", "said"),
    [
        (GITHUB | {"granted_in": ["router"]}, "Field required"),
        (
            GITHUB | {"granted_in": ["router"], "base_version": 0, "yaml": "x: 1"},
            "Extra inputs are not permitted",
        ),
    ],
    ids=["no base_version", "a yaml it does not have"],
)
def test_a_put_mcp_body_it_cannot_read_is_told_the_mcp_bodys_fields(
    client, lib, body, said
):
    response = client.put("/mcp/github", json=body)
    assert (response.status_code, response.json()["error"]) == (400, "bad_request")
    assert response.json()["message"] == f"{texts.MCP_BAD_REQUEST} {said}"
    assert "github" not in lib.state().tools


@pytest.mark.parametrize("name", ["run_all", "not a name", "class"])
def test_put_mcp_refuses_a_name_the_repl_cannot_bind(client, lib, name):
    response = grant(client, name)
    assert (response.status_code, response.json()["error"]) == (422, "invalid")
    assert name not in lib.state().tools


def test_get_mcp_lists_grants_with_their_last_seen_tools(client, lib):
    put_tool(client, "word_count")
    grant(client)
    at = datetime(2026, 10, 3, 14, 2, tzinfo=UTC)
    told = "- `github(tool, /, **arguments)`\n  MCP server 'github' (stdio): …"
    bound = McpServerStatus(
        tool="github",
        server="github",
        transport="stdio",
        state="bound",
        count=12,
        told=told,
    )
    remember_seen(lib.path.parent, "run-1", [bound], at)
    [listed] = client.get("/mcp").json()
    assert (listed["name"], listed["seen"]) == (
        "github",
        {"at": "2026-10-03T14:02:00Z", "run": "run-1", "count": 12, "told": told},
    )


def test_get_mcp_says_when_a_grant_has_an_old_shim(client, lib):
    grant(client)
    older = shim_source().replace("version 1", "version 0", 1)
    lib.put_tool("github", GITHUB_YAML, source=older)
    [listed] = client.get("/mcp").json()
    assert (listed["version"], listed["shim_current"]) == (2, False)


def test_mcp_routes_answer_only_their_own_host(lib, no_process):
    foreign = TestClient(
        create_app(lib, same_user=lambda c, s: True),
        base_url=f"http://evil.example:{PORT}",
    )
    answers = [
        foreign.get("/mcp"),
        foreign.put("/mcp/github", json=GITHUB),
        foreign.post("/tools/x/check", json={"yaml": "factory: make"}),
    ]
    assert [(a.status_code, a.json()["error"]) for a in answers] == [
        (403, "forbidden")
    ] * 3
