"""The recorder: deep_reasoner's events -> RunEvents (§6.1), and the tripwire on what
deep_reasoner's events carry (E4)."""

import asyncio
import contextlib
import json
import logging
from pathlib import Path

import pytest
import structlog
from deep_reasoner.core import configure_structlog_fixture, set_cache_dir
from deep_reasoner.mocks import FakeCompletionClient
from deep_reasoner.v2 import cli as dr_cli
from structlog.contextvars import bound_contextvars

from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.worker._upstream_standin import (
    AgentEnded,
    AgentStarted,
    CellEnded,
    CellStarted,
    ModelCalled,
    Stopped,
    Thought,
)
from deep_reasoning.acp.worker.recorder import EventSink, Recorder
from tests.acp.scenarios import repl, scripted

PRICES = PriceTable({})
DR_RUN = "20261002-000000-abcdef"
FAN_OUT = repl(
    "r = run_all([anext(subagent().send(f'Summarize C{i}')) for i in (1, 2)])",
    "print(r)",
)


class Recording:
    """A Recorder writing to a file, fed events by hand."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "events.jsonl"
        self._file = self.path.open("wb")
        self.recorder = Recorder(EventSink(self._file.fileno()), PRICES)

    def feed(self, *events):
        for event in events:
            self.recorder.feed(event)
        return self

    def start(self, node, parent=None, cell=None, task="t", backbone="chat"):
        return self.feed(
            AgentStarted(node, parent, cell, "root", backbone, task, 4, DR_RUN)
        )

    def events(self, *kinds: str) -> list[dict]:
        self._file.flush()
        rows = [json.loads(line) for line in self.path.read_text().splitlines()]
        return [r for r in rows if not kinds or r["kind"] in kinds]


@pytest.fixture
def rec(tmp_path):
    return Recording(tmp_path)


def pick(event: dict, *keys: str) -> tuple:
    return tuple(event[key] for key in keys)


def test_each_event_is_its_run_event(rec):
    rec.start(1).feed(
        Thought(1, "Set x."),
        CellStarted(1, 1, "a = 1", "scripted"),
        CellEnded(1, 1, "a = 1", "(no output)", interrupted=False),
        CellStarted(1, 2, "loop()", "think"),
        CellEnded(1, 2, "loop()", "", interrupted=True),
    )
    thought, start, end, second, interrupted = rec.events(
        "thought", "cell.start", "cell.end"
    )
    assert thought == {"kind": "thought", "node": 1, "text": "Set x."}
    assert pick(start, "cell", "code", "origin") == (1, "a = 1", "puppeteered")
    assert pick(end, "cell", "output", "interrupted") == (1, "(no output)", False)
    assert pick(second, "cell", "origin") == (2, "think")
    assert pick(interrupted, "cell", "code", "interrupted") == (2, "loop()", True)


@pytest.mark.parametrize(
    ("status", "answer", "text"),
    [
        ("done", "one", "one"),
        ("done", {"x": 1}, "{'x': 1}"),
        ("exhausted", "Agent failed.", "Agent failed."),
        ("failed", None, None),
        ("stopped", Stopped(1), None),
    ],
)
def test_an_agent_answers_its_text_only_when_done_or_exhausted(
    rec, status, answer, text
):
    rec.start(1).feed(AgentEnded(1, status, 1, answer, None, None))
    end = rec.events("agent.end")[0]
    assert pick(end, "status", "dr_status", "answer") == (status, status, text)


def test_a_child_carries_its_ancestry_and_the_cell_it_was_started_in(rec):
    rec.start(1).start(2, 1, 1, task="Summarize C1").start(4, 2, 3)
    first, child = rec.events("agent.start")[1:]
    assert pick(first, "parent", "ancestry", "parent_cell") == (1, [1, 2], 1)
    assert pick(child, "parent", "ancestry", "depth") == (2, [1, 2, 4], 3)
    assert pick(child, "drive", "backbone", "dr_run") == (1, "chat", DR_RUN)


def test_a_second_start_of_a_node_is_its_next_drive(rec):
    rec.start(1).feed(AgentEnded(1, "done", 1, 1, None, None)).start(1)
    assert [e["drive"] for e in rec.events("agent.start")] == [1, 2]


def test_model_calls_are_priced_and_a_claude_session_is_an_exact_cost(rec):
    usage = {"prompt_tokens": 30, "completion_tokens": 10}
    rec.start(1).feed(
        ModelCalled(1, "think", "gpt-6-luna", usage, None),
        ModelCalled(1, "tool", "unpriced", usage, None),
        ModelCalled(1, "claude", "sonnet", {"input_tokens": 5}, 0.01),
    )
    think, tool, claude = rec.events("usage")
    assert think == {
        "kind": "usage",
        "node": 1,
        "call": "think",
        "model": "gpt-6-luna",
        "tokens_in": 30,
        "tokens_out": 10,
        "cost_usd": pytest.approx(8e-6),
        "cost_source": "table",
        "context_window": 1_050_000,
    }
    assert pick(tool, "call", "cost_usd", "cost_source") == ("tool", None, None)
    assert pick(claude, "cost_usd", "cost_source", "tokens_in") == (0.01, "claude", 5)


class Reasoner:
    """deep_reasoner's stop(node_id): True for an agent it is running."""

    def __init__(self, *running: int) -> None:
        self.running = set(running)

    def stop(self, node: int) -> bool:
        return node in self.running


def test_a_stop_is_accepted_only_for_a_running_agent(rec):
    rec.start(1).start(2, 1, 1).start(3, 1, 1)
    rec.feed(AgentEnded(3, "done", 1, "x", None, None))
    for node in (2, 9, 3):
        rec.recorder.stop(node, Reasoner(1, 2))
    replies = [
        pick(e, "node", "mode", "accepted", "reason", "backbone")
        for e in rec.events("stop.accepted")
    ]
    assert replies == [
        (2, "dean", True, None, "chat"),
        (9, "dean", False, "no such agent in this run", None),
        (3, "dean", False, "the agent has already ended", "chat"),
    ]


def test_text_over_8_mib_keeps_its_head_and_tail(rec):
    big = "a" * (5 * 1024 * 1024) + "b" * (5 * 1024 * 1024)
    rec.start(1).feed(CellEnded(1, 1, "print(big)", big, interrupted=False))
    output = rec.events("cell.end")[0]["output"]
    assert output.startswith("aaa") and output.endswith("bbb")
    assert "bytes elided" in output
    assert len(output.encode()) <= 8 * 1024 * 1024 + 100


def test_tripwire_deep_reasoners_events_carry_everything_the_recorder_reads(
    tmp_path, monkeypatch
):
    """A scripted run on the real deep_reasoner: a main decomposition fans out two children,
    one calls the llm tool, then a second prompt resumes the root."""
    plan = {
        "Rank the courses.": [repl("FinalAnswer(r)", think="Both answered.")],
        "Summarize C1": [
            repl("FinalAnswer('ok C1 ' + llm('say hi'))", think="Ask the tool.")
        ],
        "Summarize C2": [repl("FinalAnswer('ok C2')")],
        "say hi": ["hi"],
        "second question": [repl("FinalAnswer(len(r))")],
    }
    monkeypatch.setattr(
        dr_cli, "build_client", lambda cfg: FakeCompletionClient(scripted(plan))
    )
    cfg = dr_cli.V2Config(
        system_prompt="Scripted.",
        model="m",
        max_iter=4,
        task="Rank the courses.",
        namespaces={"root": {"tools": ["llm"]}},
        decompositions=[
            {
                "name": "fan",
                "messages": [
                    {"role": "user", "content": "{{ task }}"},
                    {"role": "assistant", "content": FAN_OUT},
                ],
            }
        ],
    )
    rec = Recording(tmp_path)
    set_cache_dir(None)
    configure_structlog_fixture(console=False, default_level=logging.CRITICAL)
    run_dir = tmp_path / "run"
    reasoner, alias = dr_cli.build_reasoner(
        cfg, run_dir=run_dir, main_decomposition="fan"
    )

    async def drive():
        answers = []
        with bound_contextvars(task_id="run", log_dir=str(run_dir)), alias:
            for task in (cfg.task, "second question"):
                async with contextlib.aclosing(reasoner.events(task)) as events:
                    async for event in events:
                        rec.recorder.feed(event)
                answers.append(reasoner.final_answer)
        return answers

    try:
        answers = asyncio.run(drive())
    finally:
        dr_cli.close_run(reasoner)
        structlog.reset_defaults()
    assert answers == [["ok C1 hi", "ok C2"], 2]
    starts = rec.events("agent.start")
    assert [(e["node"], e["parent"], e["drive"], e["parent_cell"]) for e in starts] == [
        (1, None, 1, None),
        (2, 1, 1, 1),
        (starts[2]["node"], 1, 1, 1),
        (1, None, 2, None),
    ]
    assert {e["backbone"] for e in starts} == {"chat"}
    root_cells = [
        (e["cell"], e["origin"]) for e in rec.events("cell.start") if e["node"] == 1
    ]
    assert root_cells == [(1, "puppeteered"), (2, "think"), (3, "think")]
    cell_ends = rec.events("cell.end")
    assert len(cell_ends) == len(rec.events("cell.start"))
    assert not any(e["interrupted"] for e in cell_ends)
    ends = {(e["node"], e["status"], e["answer"]) for e in rec.events("agent.end")}
    assert ends >= {(2, "done", "ok C1 hi"), (starts[2]["node"], "done", "ok C2")}
    calls = {(e["node"], e["call"]) for e in rec.events("usage")}
    assert calls == {
        (1, "think"),
        (2, "think"),
        (2, "tool"),
        (starts[2]["node"], "think"),
    }
    assert "Ask the tool." in [e["text"] for e in rec.events("thought")]
