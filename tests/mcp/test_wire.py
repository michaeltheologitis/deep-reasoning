"""What the front sends its worker about MCP servers, and what it remembers (D4 §4.1, §4.7)."""

import stat
from datetime import UTC, datetime

import acp.schema
import yaml

from deep_reasoning.mcp.wire import (
    McpSeen,
    McpServerSpec,
    McpServerStatus,
    forwarded_specs,
    read_seen,
    redact,
    remember_seen,
    servers_named,
    specs_for_run,
)

AT = datetime(2026, 10, 3, 14, 2, tzinfo=UTC)


def dumped(server) -> dict:
    """As D1 keeps a forwarded server on the session."""
    return server.model_dump(mode="json", by_alias=True)


def stdio(name: str, **env: str) -> dict:
    return dumped(
        acp.schema.McpServerStdio(
            name=name,
            command="npx",
            args=["-y", f"@example/{name}"],
            env=[acp.schema.EnvVariable(name=k, value=v) for k, v in env.items()],
        )
    )


def remote(kind, name: str, **headers: str) -> dict:
    return dumped(
        kind(
            name=name,
            url=f"https://{name}.example/mcp",
            headers=[
                acp.schema.HttpHeader(name=k, value=v) for k, v in headers.items()
            ],
            type="http" if kind is acp.schema.HttpMcpServer else "sse",
        )
    )


def main_yaml(tmp_path, tools):
    path = tmp_path / "main.yaml"
    path.write_text(yaml.safe_dump({"model": "m", "tools": tools}))
    return path


def test_forwarded_specs_read_acps_stdio_http_and_sse_shapes():
    forwarded = [
        stdio("github", GITHUB_TOKEN="ghp-secret"),
        {**stdio("typed"), "type": "stdio"},
        remote(acp.schema.HttpMcpServer, "postgres", Authorization="Bearer pg"),
        remote(acp.schema.SseMcpServer, "wiki", Cookie="c=1"),
    ]
    assert forwarded_specs(forwarded) == [
        McpServerSpec(
            name="github",
            transport="stdio",
            command="npx",
            args=["-y", "@example/github"],
            env={"GITHUB_TOKEN": "ghp-secret"},
        ),
        McpServerSpec(
            name="typed",
            transport="stdio",
            command="npx",
            args=["-y", "@example/typed"],
        ),
        McpServerSpec(
            name="postgres",
            transport="http",
            url="https://postgres.example/mcp",
            headers={"Authorization": "Bearer pg"},
        ),
        McpServerSpec(
            name="wiki",
            transport="sse",
            url="https://wiki.example/mcp",
            headers={"Cookie": "c=1"},
        ),
    ]


def test_other_mcp_server_types_are_ignored():
    acp_server = dumped(
        acp.schema.AcpMcpServer(name="inner", server_id="x", type="acp")
    )
    assert forwarded_specs([acp_server, {"name": "ws", "type": "websocket"}]) == []


def test_servers_named_reads_mcp_blocks_only(tmp_path):
    tools = {
        "gh": {"factory": "mcp_server", "server": "github", "name": "gh"},
        "word_count": {"factory": "make", "factory_from": "tools/word_count.py"},
        "notes": {"factory": "rag"},
    }
    assert servers_named(main_yaml(tmp_path, tools)) == {"github"}
    assert servers_named(main_yaml(tmp_path, {})) == set()


def test_a_run_gets_only_the_specs_its_blocks_name(tmp_path):
    config = main_yaml(
        tmp_path, {"gh": {"factory": "mcp_server", "server": "github", "name": "gh"}}
    )
    forwarded = [stdio("github", T="one-secret"), stdio("slack", T="other-secret")]
    specs = specs_for_run(forwarded, config)
    assert [s.name for s in specs] == ["github"]
    assert "other-secret" not in str([s.model_dump() for s in specs])


def test_redact_replaces_every_secret_value():
    text = "invalid token ghp-secret (header Bearer pg-secret); id ab; ghp-secret again"
    assert redact(text, ["ghp-secret", "Bearer pg-secret", "ab", ""]) == (
        "invalid token [redacted] (header [redacted]); id ab; [redacted] again"
    )


def test_the_seen_cache_round_trips_and_is_private(tmp_path):
    home = tmp_path / "home"
    bound = McpServerStatus(
        tool="gh", server="github", transport="stdio", state="bound", count=3, told="t1"
    )
    failed = McpServerStatus(
        tool="pg", server="postgres", transport="http", state="failed", detail="x"
    )
    remember_seen(home, "run-1", [bound, failed], AT)
    assert read_seen(home, "github") == McpSeen(at=AT, run="run-1", count=3, told="t1")
    assert read_seen(home, "postgres") is None

    remember_seen(home, "run-2", [bound.model_copy(update={"count": 4})], AT)
    assert (read_seen(home, "github").run, read_seen(home, "github").count) == (
        "run-2",
        4,
    )

    [written] = (home / "mcp").iterdir()
    assert stat.S_IMODE((home / "mcp").stat().st_mode) == 0o700
    assert stat.S_IMODE(written.stat().st_mode) == 0o600
