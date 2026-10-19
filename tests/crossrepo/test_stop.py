"""TASK-69 across the repositories: after Canvas's Stop (POST /interrupt) through the SDK
fork's agent-server and its ACP bridge, the next message reaches dr-acp alone, and
Canvas's Resume (▷, POST /run) still sends the stopped one again. Canvas's socket sends a
message into the same server call as POST /events, which these tests use.

The first test needs the SDK fork's fix (41381bf on its deep-reasoning branch, for
dr-3): on dr-2 the bridge sends the stopped message again ahead of the next one.
"""

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from deep_reasoning.acp.recap import read_turns
from deep_reasoning.acp.runlog import Home, PromptStart, RunEnd, RunLog, SessionIndex
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from tests.acp.scenarios import BASE_CONFIG, repl, scripted, task_and_turn
from tests.crossrepo.agent_server import RunningAgentServer, agent_server, sdk_checkout
from tests.library.conftest import write_config

FIRST = "Which course is lightest?"
SPIN = "Spin."
QUESTION = "What did I ask first?"
PLAN = {
    FIRST: [repl("FinalAnswer('STAT101')")],
    QUESTION: [repl(f"FinalAnswer({FIRST!r})")],
}
SLEEP = "time.sleep(60)"
TIMEOUT_S = 120.0


def spinning_once(plan):
    """scripted(plan), except that SPIN's first drive sleeps in a cell and any later one
    answers at once, so a replay fails an assertion rather than the timeout."""
    follow = scripted(plan)
    slept = threading.Event()

    def respond(messages):
        if task_and_turn(messages)[0] != SPIN:
            return follow(messages)
        if slept.is_set():
            return repl("FinalAnswer('replayed')")
        slept.set()
        return repl("import time", SLEEP, "FinalAnswer('spun')")

    return respond


@contextmanager
def conversation_through_the_bridge(
    tmp_path: Path, home: Path
) -> Iterator[tuple[RunningAgentServer, str]]:
    """A conversation on the deep_reasoner profile in the SDK fork's agent-server, whose
    Library calls a FakeOpenAI answering spinning_once(PLAN)."""
    work = tmp_path / "work"
    work.mkdir()
    with (
        FakeOpenAI(spinning_once(PLAN)) as model,
        agent_server(sdk_checkout(), tmp_path / "agent-server") as server,
    ):
        library = Library.open(library_path(home), starter=False)
        client = {**BASE_CONFIG["client"], "base_url": model.base_url}
        library.import_config(
            write_config(tmp_path / "config", BASE_CONFIG | {"client": client})
        )
        yield server, server.open_conversation(home, work)


def stop_while_spinning(
    server: RunningAgentServer, conversation: str, home: Path
) -> None:
    """SPIN sent, then Canvas's Stop once its cell sleeps in a run log; returns once the
    conversation is paused."""
    server.post(conversation, SPIN)
    deadline = time.monotonic() + TIMEOUT_S
    while not any(SLEEP in log.read_text() for log in home.glob("runs/*/events.jsonl")):
        assert time.monotonic() < deadline, f"no run log holds {SLEEP}"
        time.sleep(0.1)
    server.request("POST", f"/api/conversations/{conversation}/interrupt")
    status = server.wait(conversation, ("paused", "finished", "error"), deadline)
    assert status == "paused"


def runs_of(home: Path) -> list[str]:
    [session] = (home / "sessions").glob("*.json")
    return SessionIndex.model_validate_json(session.read_text()).runs


def prompts(home: Path, run: str) -> list[str]:
    """What dr-acp was sent in the run, in order."""
    return [e.task for e in RunLog.read(Home(home), run) if isinstance(e, PromptStart)]


def turns(home: Path, runs: list[str]) -> list[tuple[str, str]]:
    """TASK-57's turns of the conversation, as (message, how it ended)."""
    return [(turn.message, turn.ended) for turn in read_turns(Home(home), runs)]


@pytest.mark.crossrepo
def test_after_a_stop_through_the_bridge_the_next_message_is_sent_alone(tmp_path, home):
    with conversation_through_the_bridge(tmp_path, home) as (server, conversation):
        server.ask(conversation, FIRST, time.monotonic() + TIMEOUT_S)
        stop_while_spinning(server, conversation, home)
        server.ask(conversation, QUESTION, time.monotonic() + TIMEOUT_S)
    runs = runs_of(home)
    assert len(runs) == 2, runs
    assert prompts(home, runs[0]) == [FIRST, SPIN]
    [end] = [e for e in RunLog.read(Home(home), runs[0]) if isinstance(e, RunEnd)]
    assert end.reason == "stopped"
    assert prompts(home, runs[1]) == [QUESTION]
    assert turns(home, runs) == [
        (FIRST, "answered"),
        (SPIN, "stopped"),
        (QUESTION, "answered"),
    ]


@pytest.mark.crossrepo
def test_resume_after_a_stop_through_the_bridge_sends_the_stopped_message_again(
    tmp_path, home
):
    with conversation_through_the_bridge(tmp_path, home) as (server, conversation):
        stop_while_spinning(server, conversation, home)
        server.request("POST", f"/api/conversations/{conversation}/run")
        deadline = time.monotonic() + TIMEOUT_S
        status = server.wait(conversation, ("finished", "error", "stuck"), deadline)
        assert status == "finished"
    runs = runs_of(home)
    assert len(runs) == 2, runs
    assert prompts(home, runs[1]) == [SPIN]
    assert turns(home, runs) == [(SPIN, "stopped"), (SPIN, "answered")]
