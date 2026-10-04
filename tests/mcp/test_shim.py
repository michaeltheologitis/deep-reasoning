"""The shim (D4 §4.3, §4.6, §8.3, §8.4): one MCP server as a deep_reasoner tool. Here in
plain dr's mode (no SESSION), against fake servers of our own on stdio, HTTP and SSE."""

import ast
import concurrent.futures
import copy
import os
import signal
import socket
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
from deep_reasoner.primitives import Func
from deep_reasoner.repls.backends import copy_env
from deep_reasoner.tools.base import load_tool_factory
from deep_reasoner.v2.messages import func

from deep_reasoning.mcp import shim
from tests.processes import alive, running_after

SERVERS = Path(__file__).parent / "servers"
FIXTURES = Path(__file__).parent / "fixtures"
ECHO = SERVERS / "echo_server.py"
START_S = 30  # a ceiling for a FastMCP server's start on a slow machine
DESCRIPTION = """\
MCP server 'echo' (stdio): call a tool as echo.<tool>(…) or echo("<tool name>", **arguments); a failed call raises McpToolError.
  echo.echo(text: str) -> str
    Return the text unchanged.
  echo.add(a: int, b: int = …) -> dict
    Add two whole numbers.
  echo.plain(text: str) -> str
    Return the text as plain content, with no structured result.
  echo.picture() -> str
    A one-pixel image.
  echo.fail(why: str) -> str
    Always fails, saying why.
  echo.token() -> str
    The ECHO_TOKEN this server was started with.
  echo.env_names() -> list
    The names of this server's environment variables.
  echo.sleep(seconds: float) -> str
    Sleep, then say so.
  echo.crash() -> str
    End this server's process at once.
  echo("2nd-opinion", question: str) -> str
    A tool whose name cannot be a Python attribute.
  echo.whoami() -> str
    The Authorization header of an HTTP request."""


def block(**fields) -> dict:
    """An MCP block's params as make_tools passes them: without factory and factory_from."""
    return {
        "name": "echo",
        "server": "echo",
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(ECHO)],
        "env": ["ECHO_TOKEN"],
        "connect_timeout_s": START_S,
    } | fields


def abandon(values) -> None:
    for value in values:
        if isinstance(value, shim.Server):
            value._connection.abandon()


@pytest.fixture(autouse=True)
def plain_dr(monkeypatch):
    """No dr-acp worker installed a SESSION."""
    monkeypatch.setattr(shim, "SESSION", None)


@pytest.fixture
def factory():
    """mcp_server(None, block(**fields)); every server it connected is abandoned after."""
    made = []

    def make(**fields) -> Func:
        built = shim.mcp_server(None, block(**fields))
        made.append(built.value)
        return built

    yield make
    abandon(made)


@pytest.fixture(scope="module")
def echo():
    """One echo server, connected in plain mode, shared by the tests that only call it."""
    before, shim.SESSION = shim.SESSION, None
    os.environ["ECHO_TOKEN"] = "tok-module"
    try:
        built = shim.mcp_server(None, block())
    finally:
        shim.SESSION = before
        del os.environ["ECHO_TOKEN"]
    assert isinstance(built.value, shim.Server), built.description
    yield built
    abandon([built.value])


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def test_the_shim_connects_from_its_block_with_env_from_the_environment(
    factory, monkeypatch
):
    monkeypatch.setenv("ECHO_TOKEN", "tok-secret-1")
    monkeypatch.setenv("D4_NOT_FOR_SERVERS", "worker-only")
    built = factory()
    assert isinstance(built, Func)
    assert built.value.token() == "tok-secret-1"
    assert "D4_NOT_FOR_SERVERS" not in built.value.env_names()


def test_results_are_unwrapped_dicts_text_or_blocks(echo):
    server = echo.value
    assert server.echo("hi") == "hi"
    assert server.add(2) == {"sum": 3}
    assert server.plain("line one\nline two") == "line one\nline two"
    assert server.env_names() == sorted(server.env_names())
    [picture] = server.picture()
    assert (picture["type"], picture["mimeType"]) == ("image", "image/png")


def test_a_failed_call_raises_mcp_tool_error_with_the_servers_text(echo):
    with pytest.raises(shim.McpToolError) as failed:
        echo.value.fail("no luck")
    assert str(failed.value) == "echo.fail failed: Error executing tool fail: no luck"
    with pytest.raises(shim.McpToolError) as invalid:
        echo.value.echo()
    assert str(invalid.value).startswith("echo.echo failed: Error executing tool echo:")
    assert "Field required" in str(invalid.value)


def test_positional_arguments_follow_the_described_order(echo):
    add = echo.value.add
    assert (add(2, 5), add(2), add(b=4, a=1)) == ({"sum": 7}, {"sum": 3}, {"sum": 5})
    with pytest.raises(TypeError):
        add(1, 2, 3)


def test_tools_without_an_identifier_are_called_by_their_exact_name(echo):
    server = echo.value
    assert server("2nd-opinion", question="why") == "ask again: why"
    assert server("echo", text="by name") == "by name"
    assert not any(name.startswith("2nd") for name in vars(server))


def test_the_description_is_what_8_4_says(echo):
    assert echo.description == DESCRIPTION
    told = func("echo", echo.value, echo.description).describe()
    assert told.splitlines()[:2] == [
        "- `echo(tool, /, **arguments)`",
        "  " + DESCRIPTION.splitlines()[0],
    ]


def test_a_server_survives_fork(echo):
    server = echo.value
    assert copy.deepcopy(server) is server
    assert copy.copy(server) is server
    assert copy.deepcopy(server.echo) is server.echo
    assert copy_env({"echo": server})["echo"] is server


def test_calls_from_many_threads_and_under_nest_asyncio(echo):
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        said = list(pool.map(echo.value.echo, [str(i) for i in range(32)]))
    assert said == [str(i) for i in range(32)]
    # nest_asyncio patches asyncio for the whole process, so this half runs in a child.
    script = textwrap.dedent(
        f"""
        import asyncio, sys
        import nest_asyncio
        from deep_reasoning.mcp import shim
        built = shim.mcp_server(None, {block()!r})
        async def inside_a_running_loop():
            return built.value.echo("inside")
        before = asyncio.run(inside_a_running_loop())
        nest_asyncio.apply()
        after = asyncio.run(inside_a_running_loop())
        print(before, after)
        """
    )
    done = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=os.environ | {"ECHO_TOKEN": "t"},
    )
    assert done.stdout.strip() == "inside inside", done.stderr[-2000:]


def test_without_the_mcp_package_the_factory_returns_a_stand_in(monkeypatch):
    monkeypatch.setitem(sys.modules, "mcp", None)
    built = shim.mcp_server(None, block())
    sentence = (
        "echo is not available in this conversation: the mcp package is not installed "
        "(pip install mcp)."
    )
    assert built.description == sentence
    with pytest.raises(shim.McpToolError) as called:
        built.value("echo", text="hi")
    with pytest.raises(shim.McpToolError) as reached:
        built.value.echo("hi")
    assert (str(called.value), str(reached.value)) == (sentence, sentence)


def test_a_stand_in_is_plain_to_deep_reasoners_seams():
    stand_in = shim.unavailable("echo", shim.NOT_ENABLED).value
    assert getattr(stand_in, "__cross_namespace__", None) is None
    assert copy.deepcopy(stand_in) is stand_in
    assert func("echo", stand_in).describe().startswith("- `echo(*args, **kwargs)`")


@pytest.mark.parametrize(
    ("server", "fields", "reason"),
    [
        (
            "crash_server.py",
            {"env": ["CRASH_TOKEN", "D4_MISSING_ONE"]},
            (
                "its MCP server could not be started (McpError: Connection closed); not "
                "set in the environment: D4_MISSING_ONE"
            ),
        ),
        (
            "hang_server.py",
            {"connect_timeout_s": 1},
            "its MCP server did not answer within 1 s when the conversation started",
        ),
    ],
    ids=["crashes", "hangs"],
)
def test_a_server_it_cannot_reach_becomes_a_stand_in_saying_why(
    factory, monkeypatch, server, fields, reason
):
    monkeypatch.setenv("CRASH_TOKEN", "crash-secret")
    monkeypatch.setenv("ECHO_TOKEN", "t")
    built = factory(args=[str(SERVERS / server)], **fields)
    assert built.description == f"echo is not available in this conversation: {reason}."


def test_properties_that_take_any_value_or_none_are_described_as_any_and_never(
    factory,
):
    odd = factory(name="odd", server="odd", args=[str(SERVERS / "odd_server.py")])
    assert isinstance(odd.value, shim.Server)
    described = odd.description.splitlines()
    assert "  odd.odd(anything: Any = …, nothing: Never = …) -> str" in described


def test_a_call_that_never_answers_raises_after_its_timeout(factory):
    server = factory(call_timeout_s=1).value
    started = time.monotonic()
    with pytest.raises(shim.McpToolError) as raised:
        server.sleep(30)
    assert time.monotonic() - started < 3
    assert str(raised.value) == "echo.sleep did not answer within 1 s"
    assert server.echo("still here") == "still here"


def test_a_server_that_dies_fails_the_call_and_every_later_one_at_once(factory):
    server = factory().value
    with pytest.raises(shim.McpToolError) as in_flight:
        server.crash()
    started = time.monotonic()
    with pytest.raises(shim.McpToolError) as later:
        server.echo("anyone?")
    assert time.monotonic() - started < 0.5
    stopped = (
        "MCP server 'echo' stopped (McpError: Connection closed); echo is unavailable "
        "for the rest of this run."
    )
    assert (str(in_flight.value), str(later.value)) == (stopped, stopped)


def test_a_hand_off_outside_the_grant_is_refused():
    spec, _ = shim.spec_from_block(block(), {})
    connection = shim.Connection(spec, errlog=sys.stderr)
    granted = shim.Server(
        "echo", connection, granted=frozenset({"router", "router.archive"})
    )
    anywhere = shim.Server("echo", connection, granted=None)
    assert granted.__cross_namespace__(None, "courses") is granted
    assert granted.__cross_namespace__("root", "router.archive") is granted
    assert anywhere.__cross_namespace__("root", "courses") is anywhere
    with pytest.raises(PermissionError) as refused:
        granted.__cross_namespace__("router", "courses")
    assert str(refused.value) == (
        "MCP server 'echo' is granted to router, router.archive, not to 'courses', so echo "
        "cannot be handed to a sub-agent there. Grant it to 'courses' in the Library's "
        "Tools tab."
    )


def test_the_shim_imports_only_the_standard_library_at_module_level():
    tree = ast.parse(Path(shim.__file__).read_text())
    imported = [
        alias.name if isinstance(node, ast.Import) else node.module
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    ]
    assert imported
    assert [m for m in imported if m.split(".")[0] not in sys.stdlib_module_names] == []


def test_a_stored_v1_shim_works_with_todays_session(monkeypatch):
    stored = load_tool_factory(
        "echo", "mcp_server", "shim_v1.py", str(FIXTURES / "main.yaml")
    )
    connected = shim.unavailable("echo", "a stand-in this test installed")
    monkeypatch.setattr(shim, "SESSION", {"echo": connected})
    assert stored(None, block()) is connected
    missing = stored(None, block(name="other"))
    assert missing.description == (
        "other is not available in this conversation: it was not connected when this "
        "conversation started."
    )


def test_the_guard_ends_its_server_when_its_parent_is_killed(tmp_path):
    parent = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import subprocess, sys, time; "
                "subprocess.Popen(sys.argv[1:], start_new_session=True); time.sleep(3600)"
            ),
            sys.executable,
            "-I",
            shim.__file__,
            "--guard",
            "--",
            sys.executable,
            str(SERVERS / "hang_server.py"),
        ],
        env=os.environ | {"ECHO_MARKER_DIR": str(tmp_path)},
        stdin=subprocess.PIPE,
    )
    deadline = time.monotonic() + START_S
    while not list(tmp_path.iterdir()) and time.monotonic() < deadline:
        time.sleep(0.05)
    [marker] = tmp_path.iterdir()
    server = int(marker.name)
    assert alive(server)
    parent.send_signal(signal.SIGKILL)
    parent.wait()
    assert running_after([server], 1.5) == []


@pytest.mark.parametrize("code", [0, 7])
def test_the_guard_passes_the_exit_code(code):
    done = subprocess.run(
        [
            sys.executable,
            "-I",
            shim.__file__,
            "--guard",
            "--",
            sys.executable,
            "-c",
            f"raise SystemExit({code})",
        ],
        timeout=30,
        check=False,
    )
    assert done.returncode == code


@pytest.mark.parametrize(
    ("transport", "flag", "path"),
    [("http", "--http", "/mcp"), ("sse", "--sse", "/sse")],
)
def test_an_http_server_is_reached_with_its_headers(
    factory, monkeypatch, transport, flag, path
):
    port = free_port()
    server = subprocess.Popen([sys.executable, str(ECHO), flag, str(port)])
    try:
        deadline = time.monotonic() + START_S
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        monkeypatch.setenv("ECHO_AUTHORIZATION", "Bearer from-the-environment")
        built = factory(
            transport=transport,
            url=f"http://127.0.0.1:{port}{path}",
            headers={"Authorization": "ECHO_AUTHORIZATION"},
        )
        assert built.value.whoami() == "Bearer from-the-environment"
        assert built.description.startswith(f"MCP server 'echo' ({transport}):")
    finally:
        server.terminate()
        server.wait()
