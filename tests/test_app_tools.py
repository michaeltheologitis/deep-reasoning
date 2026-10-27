import json
import sqlite3
from contextlib import closing
from itertools import count
from pathlib import Path

import pytest

from deep_reasoning.app_tools import build_history, open_read_only
from deep_reasoning.library import open_library, writing
from deep_reasoning.runs import LOST, chat_runs, read_turn, save_event

RUNS = Path(__file__).parent / "runs"
CHAT = "a-chat"
ANOTHER_CHAT = "another-chat"
CURRENT = "20261027-235959-000000"
RUN_NUMBERS = count()


def recorded(name):
    """A recorded run's events, as the app file holds them."""
    lines = (RUNS / f"{name}.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def plant(library, chat, events):
    """*events* as a run of *chat* in the app file; its id."""
    run = f"20261027-120000-{next(RUN_NUMBERS):06d}"
    with closing(open_library(library)) as connection:
        for event in events:
            if event["kind"] == "turn.start":
                event = event | {"run": run, "chat": chat}
            save_event(connection, run, event)
    return run


def history_of(library, chat=CHAT, run=CURRENT):
    """The history tool, as the run *run* of *chat* gets it."""
    told = {"library": str(library), "chat": chat, "run": run}
    return build_history(None, told).value


def cost_of_calls(events, nodes):
    return sum(
        event["cost"]
        for event in events
        if event["kind"] == "usage" and event["node"] in nodes
    )


def test_turns_number_the_chats_earlier_messages_as_the_recap_does(library):
    plant(library, CHAT, recorded("nested"))
    plant(library, CHAT, [{"seq": 1, "t": 1.0, "kind": "usage"}])
    plant(library, CHAT, recorded("failing"))
    current = plant(library, CHAT, recorded("fanout"))
    turns = history_of(library, run=current).turns()
    with closing(open_library(library)) as connection:
        recap = [read_turn(connection, run) for run in chat_runs(connection, CHAT)]
    expected = [turn.message for turn in recap if turn is not None][:-1]
    assert [turn["message"] for turn in turns] == expected
    assert [(turn["turn"], turn["message"], turn["answer"]) for turn in turns] == [
        (1, "Plan the term.", "CS: CS101 is light"),
        (2, "Survive failures.", "recovered"),
    ]
    assert turns[0]["cost"] == pytest.approx(
        cost_of_calls(recorded("nested"), {1, 2, 3})
    )
    assert [turn["agents"] for turn in turns] == [2, 1]


def test_another_chats_runs_are_never_seen(library):
    plant(library, CHAT, recorded("nested"))
    plant(library, ANOTHER_CHAT, recorded("drives"))
    assert [turn["message"] for turn in history_of(library).turns()] == [
        "Plan the term."
    ]
    assert [turn["message"] for turn in history_of(library, ANOTHER_CHAT).turns()] == [
        "Remember and fork."
    ]


def test_an_agents_cost_counts_its_own_calls_and_its_sub_agents(library):
    plant(library, CHAT, recorded("nested"))
    survey, read = history_of(library).agents(1)
    events = recorded("nested")
    assert [(agent["node"], agent["parent"]) for agent in (survey, read)] == [
        (2, 1),
        (3, 2),
    ]
    assert survey["cost"] == pytest.approx(cost_of_calls(events, {2, 3}))
    assert read["cost"] == pytest.approx(cost_of_calls(events, {3}))
    assert (survey["result"], survey["steps"], read["steps"]) == (
        "CS: CS101 is light",
        2,
        1,
    )


def test_steps_drill_down_through_the_sub_agents_each_cell_started(library):
    plant(library, CHAT, recorded("nested"))
    history = history_of(library)
    assert [step["agents"] for step in history.steps(1)] == [[2], []]
    [delegated, answered] = history.steps(1, node=2)
    assert delegated["code"] == "course = subagent('Read CS101.')\nprint(course)"
    assert (delegated["output"], delegated["agents"]) == ("CS101 is light", [3])
    assert answered["output"] == "FinalAnswer: 'CS: CS101 is light'"
    assert history.steps(1, node=3)[0]["code"] == "FinalAnswer('CS101 is light')"


def test_a_fan_out_lists_each_sub_agent_under_the_cell_that_started_them(library):
    plant(library, CHAT, recorded("fanout"))
    history = history_of(library)
    thought, fanned, _ = history.steps(1)
    assert (thought["kind"], thought["text"]) == ("think", "Fan out.")
    assert fanned["agents"] == [2, 3]
    assert [agent["task"] for agent in history.agents(1)] == [
        "Summarize C1.",
        "Summarize C2.",
    ]


def test_a_sub_agent_driven_twice_has_a_row_per_drive_and_its_steps_in_order(library):
    plant(library, CHAT, recorded("drives"))
    history = history_of(library)
    drives = [(agent["node"], agent["drive"]) for agent in history.agents(1)]
    assert drives == [(2, 1), (2, 2)]
    assert history.steps(1)[0]["agents"] == [2]
    assert [step["drive"] for step in history.steps(1, node=2)] == [1, 2]


@pytest.mark.parametrize("name", ["stopped", "killed"])
def test_what_a_stopped_run_left_going_reads_as_stopped(library, name):
    plant(library, CHAT, recorded(name))
    history = history_of(library)
    [agent] = history.agents(1)
    going = [history.steps(1)[-1], history.steps(1, node=agent["node"])[-1]]
    assert agent["status"] == "stopped"
    assert [cell["status"] for cell in going] == ["stopped", "stopped"]


def test_a_run_the_app_stopped_under_reads_as_failed(library):
    plant(library, CHAT, recorded("killed")[:-1])
    history = history_of(library)
    [turn] = history.turns()
    assert (turn["outcome"], turn["detail"]) == ("failed", LOST)
    assert history.agents(1)[0]["status"] == "stopped"


def test_a_call_with_an_unpriced_model_has_no_cost(library):
    plant(library, CHAT, recorded("unpriced"))
    history = history_of(library)
    assert history.turns()[0]["cost"] is None
    assert [agent["cost"] for agent in history.agents(1)] == [None, None]


def test_a_message_or_node_that_is_not_there_is_refused_in_plain_words(library):
    plant(library, CHAT, recorded("nested"))
    history = history_of(library)
    for call in (lambda: history.steps(2), lambda: history.agents(0)):
        with pytest.raises(ValueError, match="numbered 1 to 1"):
            call()
    with pytest.raises(ValueError, match=r"nodes are \[1, 2, 3\]"):
        history.steps(1, node=7)
    with pytest.raises(ValueError, match="no earlier messages"):
        history_of(library, ANOTHER_CHAT).agents(1)


def test_the_tool_reads_the_app_file_without_writing_it_or_running_its_own_sql(
    library,
):
    plant(library, CHAT, recorded("nested"))
    with closing(open_library(library)) as connection, writing(connection):
        connection.execute("CREATE VIEW planted AS SELECT id FROM chats")
        connection.execute(
            "CREATE TRIGGER wipe AFTER INSERT ON events BEGIN DELETE FROM runs; END"
        )
    before = library.read_bytes()
    with closing(open_read_only(library)) as connection:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("DELETE FROM events")
        with pytest.raises(sqlite3.OperationalError, match="planted"):
            connection.execute("SELECT * FROM planted")
    assert history_of(library).turns()[0]["message"] == "Plan the term."
    assert library.read_bytes() == before
