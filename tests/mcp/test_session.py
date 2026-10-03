"""The worker's side (D4 §4.4): which servers a run connects, all at once, and what each
agent is told; E9's "granted elsewhere" and "hangs" at the session's start."""

import sys
import time
from pathlib import Path

import pytest
import yaml
from deep_reasoner.v2.messages import func

from deep_reasoning.acp.catalog import load_dr_config
from deep_reasoning.mcp import shim
from deep_reasoning.mcp.grants import shim_source
from deep_reasoning.mcp.session import open_session
from deep_reasoning.mcp.wire import McpServerSpec
from tests.processes import running_after

SERVERS = Path(__file__).parent / "servers"
START_S = 30


def mcp_block(alias: str, server: str | None = None, **fields) -> dict:
    return {
        "factory": "mcp_server",
        "factory_from": f"tools/{alias}.py",
        "name": alias,
        "server": server or alias,
        "transport": "stdio",
        "command": "unused-under-dr-acp",
        "connect_timeout_s": START_S,
    } | fields


def spec(name: str, script: str = "echo_server.py", **env: str) -> McpServerSpec:
    return McpServerSpec(
        name=name,
        transport="stdio",
        command=sys.executable,
        args=[str(SERVERS / script)],
        env=env,
    )


def config(directory: Path, namespaces: dict, tools: dict, entry: str = "root"):
    """A dr config with these namespaces and MCP blocks, loaded as the worker loads it."""
    (directory / "tools").mkdir(parents=True)
    for alias in tools:
        (directory / "tools" / f"{alias}.py").write_text(shim_source())
    main = {
        "model": "m",
        "client": {"base_url": "http://127.0.0.1:9/v1"},
        "entry_namespace": entry,
        "namespaces": namespaces,
        "tools": tools,
    }
    (directory / "main.yaml").write_text(yaml.safe_dump(main))
    return load_dr_config(directory / "main.yaml")


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    path = tmp_path / "runs" / "run-1"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def opened():
    """Every Server that open_session connected is abandoned after the test."""
    yield
    for built in (shim.SESSION or {}).values():
        if isinstance(built.value, shim.Server):
            built.value._connection.abandon()
    shim.SESSION = None


@pytest.fixture(scope="module")
def grants(tmp_path_factory):
    """One session over five MCP blocks, from root, which may spawn only into a:
    echo granted to a; lonely granted nowhere; walled granted only to c; hidden granted
    to a but not forwarded; everywhere granted to root."""
    tmp = tmp_path_factory.mktemp("grants")
    markers = tmp / "markers"
    markers.mkdir()
    cfg = config(
        tmp / "config",
        {
            "root": {"spawn": ["a"], "tools": ["everywhere"]},
            "a": {"tools": ["echo", "hidden"]},
            "a.b": {},
            "c": {"tools": ["walled"]},
        },
        {
            name: mcp_block(name)
            for name in ("echo", "lonely", "walled", "hidden", "everywhere")
        },
    )
    marker = {"ECHO_MARKER_DIR": str(markers), "ECHO_TOKEN": "t"}
    specs = [spec(n, **marker) for n in ("echo", "lonely", "walled", "everywhere")]
    run = tmp / "runs" / "run-1"
    run.mkdir(parents=True)
    statuses = open_session(cfg, specs, run_dir=run)
    session = dict(shim.SESSION)
    yield {s.tool: s for s in statuses}, session, markers
    for built in session.values():
        if isinstance(built.value, shim.Server):
            built.value._connection.abandon()
    shim.SESSION = None


def test_only_granted_and_reachable_servers_are_started(grants):
    statuses, session, markers = grants
    assert {t: s.state for t, s in statuses.items()} == {
        "echo": "bound",
        "lonely": "skipped",
        "walled": "skipped",
        "hidden": "not_enabled",
        "everywhere": "bound",
    }
    assert len(list(markers.iterdir())) == 2
    assert set(session) == set(statuses)


def test_a_server_granted_nowhere_is_not_started(grants):
    statuses, session, _ = grants
    assert statuses["lonely"].detail == "granted to no namespace"
    assert session["lonely"].description == shim.UNAVAILABLE.format(
        name="lonely", reason=shim.NOT_REACHED
    )


def test_a_server_granted_only_where_spawning_is_not_allowed_is_not_started(grants):
    statuses, session, _ = grants
    assert (
        statuses["walled"].detail == "granted only where this conversation cannot spawn"
    )
    assert statuses["walled"].granted == ["c"]
    with pytest.raises(shim.McpToolError):
        session["walled"].value.anything()


def test_a_granted_server_not_forwarded_is_not_enabled(grants):
    statuses, session, _ = grants
    assert (statuses["hidden"].granted, statuses["hidden"].transport) == (
        ["a", "a.b"],
        "stdio",
    )
    assert session["hidden"].description == shim.UNAVAILABLE.format(
        name="hidden", reason=shim.NOT_ENABLED
    )


def test_grant_sets_follow_deep_reasoners_resolution(grants):
    statuses, session, _ = grants
    assert statuses["echo"].granted == ["a", "a.b"]
    assert statuses["everywhere"].granted == ["root", "a", "a.b", "c"]
    assert (
        session["echo"].value.__cross_namespace__("a", "a.b") is session["echo"].value
    )
    with pytest.raises(PermissionError):
        session["echo"].value.__cross_namespace__("root", "c")


def test_statuses_carry_what_the_agent_is_told(grants):
    statuses, session, _ = grants
    echo = statuses["echo"]
    assert (
        echo.told
        == func("echo", session["echo"].value, session["echo"].description).describe()
    )
    assert (echo.count, echo.server, echo.detail) == (11, "echo", None)
    assert 0 < echo.seconds < START_S
    assert session["echo"].value.echo("bound") == "bound"


def test_without_mcp_blocks_the_session_is_empty(tmp_path, run_dir, opened):
    cfg = config(tmp_path / "config", {"root": {}}, {})
    assert open_session(cfg, [spec("echo")], run_dir=run_dir) == []
    assert shim.SESSION == {}


def test_servers_connect_at_once_and_a_silent_one_is_given_up_at_the_deadline(
    tmp_path, run_dir, opened
):
    names = ("one", "two", "three")
    cfg = config(
        tmp_path / "config",
        {"root": {"tools": list(names)}},
        {n: mcp_block(n, connect_timeout_s=1.5) for n in names},
    )
    started = time.monotonic()
    statuses = open_session(
        cfg, [spec(n, "hang_server.py") for n in names], run_dir=run_dir
    )
    took = time.monotonic() - started
    assert [(s.state, s.seconds) for s in statuses] == [("no_answer", 1.5)] * 3
    assert 1.5 <= took < 3


@pytest.mark.parametrize("printed", [{}, {"CRASH_SPLIT": "1"}], ids=["whole", "split"])
def test_a_server_that_exits_at_start_is_failed_with_its_stderr_redacted(
    tmp_path, run_dir, opened, printed
):
    cfg = config(
        tmp_path / "config", {"root": {"tools": ["wiki"]}}, {"wiki": mcp_block("wiki")}
    )
    secret = spec(
        "wiki", "crash_server.py", CRASH_TOKEN="crash-secret-value", **printed
    )
    [status] = open_session(cfg, [secret], run_dir=run_dir)
    assert status.state == "failed"
    assert (
        status.detail
        == 'McpError: Connection closed; it printed: "invalid token [redacted]"'
    )
    assert (run_dir / "mcp-wiki.log").read_text() == "invalid token [redacted]\n"


def test_a_server_given_up_is_ended_within_three_seconds(tmp_path, run_dir, opened):
    markers = tmp_path / "markers"
    markers.mkdir()
    cfg = config(
        tmp_path / "config",
        {"root": {"tools": ["silent"]}},
        {"silent": mcp_block("silent", connect_timeout_s=1)},
    )
    silent = spec("silent", "hang_server.py", ECHO_MARKER_DIR=str(markers))
    [status] = open_session(cfg, [silent], run_dir=run_dir)
    assert status.state == "no_answer"
    [marker] = markers.iterdir()
    assert running_after([int(marker.name)], 3) == []
