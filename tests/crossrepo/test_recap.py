"""TASK-57 across the repositories: after Canvas's Stop (POST /interrupt) through the SDK
fork's agent-server and its ACP bridge, the next message's fresh run is given the
conversation, whichever way the bridge delivers that message to dr-acp."""

import sys
import threading
import time
from pathlib import Path

import pytest

from deep_reasoning.acp.runlog import (
    Home,
    PromptEnd,
    RecapNote,
    RunLog,
    RunStart,
    SessionIndex,
)
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from dr_app.profile import PROFILE_NAME, desired_profile
from tests.acp.scenarios import (
    BASE_CONFIG,
    FIRST_QUESTION,
    answering_from_the_recap,
    repl,
    task_and_turn,
)
from tests.crossrepo.agent_server import agent_server, sdk_checkout
from tests.library.conftest import write_config

FIRST = "Which course is lightest?"
WAIT = "Wait for me."
SLEEP = "time.sleep(60)"
TIMEOUT_S = 120.0


def waiting_once(plan):
    """answering_from_the_recap(plan), except that WAIT's first drive sleeps in a cell and
    any later one answers at once: the bridge may send it again after the Stop."""
    follow = answering_from_the_recap(plan)
    slept = threading.Event()

    def respond(messages):
        if task_and_turn(messages)[0] != WAIT:
            return follow(messages)
        if slept.is_set():
            return repl("FinalAnswer('done waiting')")
        slept.set()
        return repl("import time", SLEEP, "FinalAnswer('waited')")

    return respond


def until(predicate, deadline: float):
    while not (value := predicate()):
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.1)
    return value


@pytest.mark.crossrepo
def test_after_a_stop_through_the_bridge_the_next_message_is_given_the_first(
    tmp_path, home
):
    work = tmp_path / "work"
    work.mkdir()
    responder = waiting_once({FIRST: [repl("FinalAnswer('STAT101')")]})
    with (
        FakeOpenAI(responder) as model,
        agent_server(sdk_checkout(), tmp_path / "agent-server") as server,
    ):
        library = Library.open(library_path(home), starter=False)
        client = {**BASE_CONFIG["client"], "base_url": model.base_url}
        library.import_config(
            write_config(tmp_path / "config", BASE_CONFIG | {"client": client})
        )
        dr_acp = Path(sys.executable).parent / "dr-acp"
        profile = desired_profile(None, dr_acp=dr_acp, home=home)
        server.request("POST", f"/api/agent-profiles/{PROFILE_NAME}", profile)
        saved = server.request("GET", f"/api/agent-profiles/{PROFILE_NAME}")["profile"]
        conversation = server.request(
            "POST",
            "/api/conversations",
            {
                "agent_profile_id": saved["id"],
                "workspace": {"kind": "LocalWorkspace", "working_dir": str(work)},
            },
        )["id"]
        server.ask(conversation, FIRST, time.monotonic() + TIMEOUT_S)
        server.request(
            "POST",
            f"/api/conversations/{conversation}/events",
            {"role": "user", "content": [{"type": "text", "text": WAIT}], "run": True},
        )
        deadline = time.monotonic() + TIMEOUT_S
        until(lambda: sleeping(home), deadline)
        server.request("POST", f"/api/conversations/{conversation}/interrupt")
        until(
            lambda: (
                server.request("GET", f"/api/conversations/{conversation}")[
                    "execution_status"
                ]
                in ("paused", "finished", "error")
            ),
            deadline,
        )
        server.ask(conversation, FIRST_QUESTION, time.monotonic() + TIMEOUT_S)
    [session] = (home / "sessions").glob("*.json")
    runs = SessionIndex.model_validate_json(session.read_text()).runs
    assert len(runs) == 2
    fresh = list(RunLog.read(Home(home), runs[1]))
    [start] = [e for e in fresh if isinstance(e, RunStart)]
    given = RecapNote(turns=2, left_out=0, shortened=False)
    assert (start.after, start.recap) == ("stopped", given)
    answers = [e.answer for e in fresh if isinstance(e, PromptEnd)]
    assert answers[-1] == FIRST


def sleeping(home: Path) -> bool:
    """Some run's log has the cell that sleeps."""
    return any(SLEEP in log.read_text() for log in home.glob("runs/*/events.jsonl"))
