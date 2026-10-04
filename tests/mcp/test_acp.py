"""MCP servers and your own tools through dr-acp (D4 §4, E9): the Library grants them, a
conversation's worker binds them, and each agent sees only what its namespace is granted.
A real dr-acp over stdio, a FakeOpenAI model, fake MCP servers of our own."""

import asyncio
import sys
import time
from pathlib import Path

import acp.schema
import pytest
from starlette.testclient import TestClient

from deep_reasoning.acp import texts
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from deep_reasoning.library.api import create_app
from deep_reasoning.mcp import shim
from deep_reasoning.mcp.wire import read_seen
from tests.acp.harness import dr_acp, eventually, run, run_ids
from tests.acp.scenarios import BASE_CONFIG, repl, scripted
from tests.acp.test_agent import responses
from tests.library.conftest import write_config
from tests.mcp.conftest import put_grant
from tests.processes import running_after
from tests.tools.conftest import source

SERVERS = Path(__file__).parent / "servers"
CONFIG = {
    **BASE_CONFIG,
    "entry_namespace": "router",
    "namespaces": {
        "root": {},
        "router": {"spawn": ["router", "course_advisor"]},
        "router.archive": {},
        "course_advisor": {},
    },
}
ECHO_TOLD = "- `echo(tool, /, **arguments)`"
CRASH_SECRET = "crash-secret-value"


def library(home: Path, base_url: str, tmp: Path) -> Library:
    """The Library dr-acp runs from: our router config, on the fake model."""
    lib = Library.open(library_path(home), starter=False)
    config = {**CONFIG, "client": {**CONFIG["client"], "base_url": base_url}}
    lib.import_config(write_config(tmp / "config", config))
    return lib


def forwarded(
    name: str, script: str = "echo_server.py", **env: str
) -> acp.schema.McpServerStdio:
    """A stdio server as OpenHands' bridge forwards it at session/new."""
    return acp.schema.McpServerStdio(
        name=name,
        command=sys.executable,
        args=[str(SERVERS / script)],
        env=[acp.schema.EnvVariable(name=k, value=v) for k, v in env.items()],
    )


def kinds(client, run_id: str, kind: str) -> list:
    return [e for e in client.run_log(run_id) if e.kind == kind]


def outputs(client, run_id: str) -> list[str]:
    return [e.output for e in kinds(client, run_id, "cell.end")]


def asked(model: FakeOpenAI, call: int = 0) -> str:
    return "\n".join(str(m.get("content", "")) for m in model.calls[call].messages)


def root_texts(client, session: str) -> list[str]:
    return [
        u["content"]["text"]
        for u in client.updates_on(session)
        if u["sessionUpdate"] == "agent_message_chunk"
    ]


def outcome(response) -> str:
    return response.field_meta["deep_reasoner"]["outcome"]


@pytest.fixture
def converse(home, work, tmp_path):
    """converse(plan, prompts, …) → (client, session, responses, model): the Library set up,
    dr-acp started, each prompt asked in turn. echo_in grants echo to those namespaces and
    forwards its server; otherwise setup(lib) and servers say what there is."""

    async def talk(plan, prompts, setup, servers, namespace):
        async with FakeOpenAI(scripted(plan)) as model:
            setup(library(home, model.base_url, tmp_path))
            async with dr_acp(None, home) as client:
                session = await client.open_session(work, servers)
                if namespace:
                    await client.conn.set_config_option(
                        config_id="namespace", session_id=session, value=namespace
                    )
                responses = [await client.ask(session, p) for p in prompts]
            return client, session, responses, model

    def conversation(
        plan, prompts, *, echo_in=None, setup=None, servers=(), namespace=None
    ):
        if echo_in is not None:
            setup = lambda lib: put_grant(lib, "echo", echo_in)
            servers = [forwarded("echo", ECHO_TOKEN="t")]
        return run(talk(plan, prompts, setup or (lambda lib: None), servers, namespace))

    return conversation


def test_dr_acp_advertises_http_and_sse(home):
    async def body():
        async with dr_acp(None, home) as client:
            return client

    client = run(body())
    (_, init), *_ = responses(client.lines)
    assert init["result"]["agentCapabilities"]["mcpCapabilities"] == {
        "http": True,
        "sse": True,
    }


def test_a_granted_server_is_bound_and_a_cell_calls_it(converse):
    plan = {
        "Say hi": [
            repl("print(echo.echo('hi from echo'))"),
            repl("FinalAnswer('done')"),
        ]
    }
    client, _, [response], model = converse(
        plan, ["Say hi through echo."], echo_in=["router"]
    )
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    [status] = kinds(client, run_id, "mcp.status")
    assert [(s.tool, s.state, s.count) for s in status.servers] == [
        ("echo", "bound", 11)
    ]
    assert outputs(client, run_id)[0].strip() == "hi from echo"
    assert ECHO_TOLD in asked(model)
    assert status.servers[0].told in asked(model)


def test_a_forwarded_server_no_grant_names_is_never_started(converse, tmp_path):
    markers = tmp_path / "markers"
    markers.mkdir()
    plan = {"Anything": [repl("FinalAnswer('done')")]}
    echo = forwarded("echo", ECHO_MARKER_DIR=str(markers), ECHO_TOKEN="t")
    client, _, [response], _ = converse(plan, ["Anything at all."], servers=[echo])
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    assert kinds(client, run_id, "mcp.status") == []
    assert list(markers.iterdir()) == []


@pytest.fixture
def crashed(converse):
    """A conversation whose granted wiki server crashes at start, printing its token."""
    return converse(
        {"Carry on": [repl("FinalAnswer('carried on')")]},
        ["Carry on without it."],
        setup=lambda lib: put_grant(lib, "wiki", ["router"]),
        servers=[forwarded("wiki", "crash_server.py", CRASH_TOKEN=CRASH_SECRET)],
    )


def test_a_server_that_crashes_at_start_is_reported_and_the_run_answers(crashed):
    client, session, [response], _ = crashed
    assert outcome(response) == "answered"
    notice = texts.mcp_failed(
        "wiki", 'McpError: Connection closed; it printed: "invalid token [redacted]"'
    )
    said = root_texts(client, session)
    assert said == [notice + "\n\n", "carried on"]


def test_server_secrets_never_reach_the_run_log_or_the_transcript(home, crashed):
    client, _, _, _ = crashed
    (run_id,) = run_ids(client.printer.updates)
    assert CRASH_SECRET not in (home / "runs" / run_id / "events.jsonl").read_text()
    assert CRASH_SECRET not in b"".join(client.lines).decode()
    assert CRASH_SECRET not in (home / "runs" / run_id / "worker.log").read_text()
    assert (home / "runs" / run_id / "mcp-wiki.log").read_text() == (
        "invalid token [redacted]\n"
    )


def test_the_notice_replays_on_load(home, work, crashed):
    client, session, _, _ = crashed
    notice = root_texts(client, session)[0]

    async def load():
        async with dr_acp(None, home) as again:
            await again.conn.load_session(
                cwd=str(work), session_id=session, mcp_servers=[]
            )
            return again

    again = run(load())
    assert notice in root_texts(again, session)


def test_the_seen_cache_is_written_for_bound_servers(home, converse):
    plan = {"Look": [repl("FinalAnswer('looked')")]}
    client, _, _, _ = converse(plan, ["Look around."], echo_in=["router"])
    (run_id,) = run_ids(client.printer.updates)
    [status] = kinds(client, run_id, "mcp.status")
    seen = read_seen(home, "echo")
    assert (seen.run, seen.count, seen.told) == (run_id, 11, status.servers[0].told)


def test_no_stdio_server_outlives_a_root_stop(home, work, tmp_path):
    markers = tmp_path / "markers"
    markers.mkdir()

    async def body():
        plan = {"Spin": [repl("while True: pass")]}
        async with FakeOpenAI(scripted(plan)) as model:
            lib = library(home, model.base_url, tmp_path)
            put_grant(lib, "echo", ["router"])
            async with dr_acp(None, home) as client:
                server = forwarded("echo", ECHO_MARKER_DIR=str(markers), ECHO_TOKEN="t")
                session = await client.open_session(work, [server])
                asking = asyncio.create_task(client.ask(session, "Spin forever."))
                await eventually(
                    lambda: any(
                        u["sessionUpdate"] == "tool_call"
                        for u in client.updates_on(session)
                    )
                )
                await client.conn.cancel(session_id=session)
                response = await asking
                stopped = time.monotonic()
                return response, stopped

    response, stopped = run(body())
    assert response.stop_reason == "cancelled"
    [marker] = markers.iterdir()
    assert running_after([int(marker.name)], 2 - (time.monotonic() - stopped)) == []


def test_no_stdio_server_outlives_a_closed_session(home, work, tmp_path):
    markers = tmp_path / "markers"
    markers.mkdir()

    async def body():
        plan = {"Answer": [repl("FinalAnswer('answered')")]}
        async with FakeOpenAI(scripted(plan)) as model:
            lib = library(home, model.base_url, tmp_path)
            put_grant(lib, "echo", ["router"])
            async with dr_acp(None, home) as client:
                server = forwarded("echo", ECHO_MARKER_DIR=str(markers), ECHO_TOKEN="t")
                session = await client.open_session(work, [server])
                await client.ask(session, "Answer and close.")
                [marker] = markers.iterdir()
                await client.conn.close_session(session_id=session)
                return int(marker.name), time.monotonic()

    pid, closed = run(body())
    assert running_after([pid], 2 - (time.monotonic() - closed)) == []


def test_a_tool_saved_through_the_api_is_built_and_called_in_the_next_conversation(
    converse,
):
    def save_through_the_api(lib):
        api = TestClient(
            create_app(lib, same_user=lambda c, s: True),
            base_url="http://127.0.0.1:8123",
        )
        saved = api.put(
            "/tools/word_count",
            json={
                "yaml": "factory: make",
                "source": source("word_count"),
                "granted_in": ["router"],
                "base_version": 0,
            },
        )
        assert saved.status_code == 201, saved.text

    plan = {
        "Count": [
            repl("print(word_count('one two three four'))"),
            repl("FinalAnswer('4')"),
        ]
    }
    client, _, [response], model = converse(
        plan, ["Count the words."], setup=save_through_the_api
    )
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    assert outputs(client, run_id)[0].strip() == "4"
    assert "- `word_count(text: str) -> int`" in asked(model)


def test_a_server_that_crashes_mid_run_fails_the_call_and_the_run_goes_on(converse):
    plan = {
        "Break it": [
            repl("echo.crash()"),
            repl("print(echo.echo('again'))"),
            repl("FinalAnswer('survived')"),
        ],
        "And then": [repl("FinalAnswer('still here')")],
    }
    client, session, responses, _ = converse(
        plan, ["Break it.", "And then?"], echo_in=["router"]
    )
    assert [outcome(r) for r in responses] == ["answered"] * 2
    (run_id,) = run_ids(client.printer.updates)
    stopped = shim.SERVER_STOPPED.format(
        server="echo", detail="McpError: Connection closed", name="echo"
    )
    crashed, again, _ = outputs(client, run_id)[:3]
    assert f"McpToolError: {stopped}" in crashed
    assert f"McpToolError: {stopped}" in again
    assert root_texts(client, session)[-2:] == ["survived", "still here"]


def test_session_new_does_not_wait_and_the_first_answer_waits_at_most_the_deadline(
    home, work, tmp_path
):
    markers = tmp_path / "markers"
    markers.mkdir()

    async def body():
        plan = {"Quick": [repl("FinalAnswer('quick')")]}
        async with FakeOpenAI(scripted(plan)) as model:
            lib = library(home, model.base_url, tmp_path)
            put_grant(lib, "silent", ["router"], block={"connect_timeout_s": 2})
            async with dr_acp(None, home) as client:
                server = forwarded(
                    "silent", "hang_server.py", ECHO_MARKER_DIR=str(markers)
                )
                session = await client.open_session(work, [server])
                started_at_new = list(markers.iterdir())
                response = await client.ask(session, "Quick answer.")
                return client, session, started_at_new, response

    client, session, started_at_new, response = run(body())
    assert started_at_new == []
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    [ready] = kinds(client, run_id, "worker.ready")
    [status] = kinds(client, run_id, "mcp.status")
    assert [(s.state, s.seconds) for s in status.servers] == [("no_answer", 2)]
    assert 2 <= status.t - ready.t < 2 + 3
    assert root_texts(client, session)[0] == texts.mcp_no_answer("silent", 2) + "\n\n"


def test_a_server_granted_elsewhere_is_not_in_this_agents_repl_or_prompt(converse):
    plan = {"Look": [repl("print('echo' in dir())"), repl("FinalAnswer('looked')")]}
    client, _, [response], model = converse(
        plan, ["Look for echo."], echo_in=["course_advisor"]
    )
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    assert outputs(client, run_id)[0].strip() == "False"
    assert "echo(tool" not in asked(model)


def test_a_sub_agent_spawned_into_a_granted_namespace_gets_it(converse):
    plan = {
        "Delegate": [
            repl("FinalAnswer(subagent('Use echo there.', namespace='course_advisor'))")
        ],
        "Use echo there": [repl("FinalAnswer(echo.echo('from the advisor'))")],
    }
    client, session, [response], _ = converse(
        plan, ["Delegate to the advisor."], echo_in=["course_advisor"]
    )
    assert outcome(response) == "answered"
    assert root_texts(client, session)[-1] == "from the advisor"


def test_a_grant_reaches_a_child_namespace(converse):
    plan = {"Echo": [repl("FinalAnswer(echo.echo('in the archive'))")]}
    client, session, [response], _ = converse(
        plan, ["Echo from the archive."], echo_in=["router"], namespace="router.archive"
    )
    assert outcome(response) == "answered"
    assert root_texts(client, session)[-1] == "in the archive"


def test_handing_a_server_to_an_ungranted_namespace_is_refused(converse):
    plan = {
        "Hand": [
            repl(
                "subagent('Never runs.', namespace='course_advisor', tools={'echo': echo})"
            ),
            repl("FinalAnswer('refused')"),
        ]
    }
    client, _, [response], _ = converse(plan, ["Hand echo over."], echo_in=["router"])
    assert outcome(response) == "answered"
    (run_id,) = run_ids(client.printer.updates)
    refusal = shim.HANDOFF_REFUSED.format(
        server="echo",
        granted="router, router.archive",
        dst="course_advisor",
        name="echo",
    )
    assert f"PermissionError: {refusal}" in outputs(client, run_id)[0]
    assert [a.task for a in kinds(client, run_id, "agent.start")] == ["Hand echo over."]
