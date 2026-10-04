"""An MCP grant as a D2 tool row (D4 §4.2)."""

from datetime import UTC, datetime

import pytest

from deep_reasoning.library import Library, ToolRecord, shapes
from deep_reasoning.library.records import LibraryBadRequest
from deep_reasoning.mcp.grants import (
    SHIM_MARKER,
    McpGrantBody,
    grant_record,
    header_env_name,
    is_mcp_tool,
    mcp_block,
    shim_source,
)
from deep_reasoning.tools import texts
from tests.mcp.conftest import put_grant


def body(**fields) -> McpGrantBody:
    return McpGrantBody(
        **{
            "server": "github",
            "transport": "stdio",
            "granted_in": [],
            "base_version": 0,
        }
        | fields
    )


def record(yaml_text: str, source: str | None) -> ToolRecord:
    return ToolRecord(
        version=1,
        rev=1,
        saved_at=datetime(2026, 10, 3, tzinfo=UTC),
        name="github",
        yaml=yaml_text,
        source=source,
        granted_in=["router"],
    )


@pytest.mark.parametrize(
    ("fields", "block"),
    [
        (
            {"command": "npx", "args": ["-y", "srv"], "env": ["GITHUB_TOKEN"]},
            {
                "factory": "mcp_server",
                "name": "gh",
                "server": "github",
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "srv"],
                "env": ["GITHUB_TOKEN"],
            },
        ),
        (
            {
                "server": "postgres",
                "transport": "http",
                "url": "https://db.lab.example/mcp",
                "headers": ["Authorization"],
            },
            {
                "factory": "mcp_server",
                "name": "gh",
                "server": "postgres",
                "transport": "http",
                "url": "https://db.lab.example/mcp",
                "headers": {"Authorization": "POSTGRES_AUTHORIZATION"},
            },
        ),
        (
            {"server": "wiki", "transport": "sse", "url": "http://127.0.0.1:9/sse"},
            {
                "factory": "mcp_server",
                "name": "gh",
                "server": "wiki",
                "transport": "sse",
                "url": "http://127.0.0.1:9/sse",
                "headers": {},
            },
        ),
    ],
    ids=["stdio", "http", "sse"],
)
def test_mcp_block_for_stdio_http_and_sse(fields, block):
    assert mcp_block("gh", body(**fields)) == block


@pytest.mark.parametrize(
    ("fields", "sentence"),
    [
        ({}, texts.MCP_NEEDS_COMMAND),
        ({"command": ""}, texts.MCP_NEEDS_COMMAND),
        ({"transport": "http"}, texts.MCP_NEEDS_URL),
        ({"transport": "sse", "url": ""}, texts.MCP_NEEDS_URL),
    ],
)
def test_mcp_block_needs_a_command_or_a_url(fields, sentence):
    with pytest.raises(LibraryBadRequest) as raised:
        mcp_block("gh", body(**fields))
    assert str(raised.value) == sentence


@pytest.mark.parametrize(
    ("server", "header", "variable"),
    [
        ("postgres", "Authorization", "POSTGRES_AUTHORIZATION"),
        ("my-db.lab", "X-Api-Key", "MY_DB_LAB_X_API_KEY"),
        ("-weird-", "--h--", "WEIRD_H"),
    ],
)
def test_header_env_name(server, header, variable):
    assert header_env_name(server, header) == variable


@pytest.mark.parametrize(
    ("yaml_text", "source", "is_grant"),
    [
        ("factory: mcp_server\nserver: github\n", shim_source(), True),
        ("factory: mcp_server\nserver: github\n", "def mcp_server(c, p): ...", False),
        ("factory: make\n", shim_source(), False),
        ("factory: mcp_server\n", None, False),
    ],
    ids=["grant", "no marker", "another factory", "no source"],
)
def test_is_mcp_tool_needs_the_factory_and_the_marker(yaml_text, source, is_grant):
    assert is_mcp_tool(record(yaml_text, source)) is is_grant


def test_the_shim_source_starts_with_its_marker_and_version():
    assert shim_source().startswith(f"{SHIM_MARKER}, version 1.")


def test_grant_record_reads_the_block():
    grant = mcp_block("github", body(command="npx", env=["T"], granted_in=["router"]))
    listed = grant_record(record(shapes.canonical_yaml(grant), shim_source()), None)
    assert listed.model_dump() == {
        "name": "github",
        "version": 1,
        "server": "github",
        "transport": "stdio",
        "command": "npx",
        "args": [],
        "url": None,
        "env": ["T"],
        "headers": [],
        "granted_in": ["router"],
        "shim_current": True,
        "seen": None,
    }


def test_an_exported_and_reimported_grant_is_still_a_grant(tmp_path):
    first = Library.open(tmp_path / "a.sqlite", starter=False)
    put_grant(first, "github", ["root"])
    exported = first.materialize(tmp_path / "export")
    second = Library.open(tmp_path / "b.sqlite", starter=False)
    second.import_config(exported)
    reimported = second.tool("github")
    assert is_mcp_tool(reimported)
    assert (reimported.granted_in, reimported.source) == (["root"], shim_source())
