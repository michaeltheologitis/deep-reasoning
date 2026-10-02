"""The recorder: deep_reasoner's events -> RunEvents (§6.1), stop classification (§6.3),
and the tripwire on what it reads from deep_reasoner (E4)."""

import asyncio
import json
import logging
from pathlib import Path

import pytest
import structlog
from deep_reasoner.core import configure_structlog_fixture, set_cache_dir
from deep_reasoner.mocks import FakeCompletionClient
from deep_reasoner.v2 import cli as dr_cli
from deep_reasoner.v2.decompositions import main_decomposition_turns
from structlog.contextvars import bound_contextvars

from deep_reasoning.acp.costs import Price, PriceTable
from deep_reasoning.acp.worker.recorder import EventSink, Recorder
from deep_reasoning.acp.worker.stop import StoppedByUser
from tests.acp.scenarios import repl, scripted

PRICES = PriceTable(
    {"m": Price(input_per_mtok=1.0, output_per_mtok=2.0, context_window=100)}
)
FAN_OUT = repl(
    "r = run_all([anext(subagent().send(f'Summarize C{i}')) for i in (1, 2)])",
    "print(r)",
)


class Recording:
    """A Recorder writing to a file, fed event dicts by hand."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "events.jsonl"
        self._file = self.path.open("wb")
        self.recorder = Recorder(EventSink(self._file.fileno()), PRICES)

    def log(self, event: str, node: int, *ancestry: int, kind: str = "agent", **fields):
        anc = ancestry or (node,)
        event_dict = {
            "event": event,
            "node_id": node,
            "ancestry": anc,
            "kind": kind,
            **fields,
        }
        assert self.recorder(None, "debug", dict(event_dict)) == event_dict
        return self

    def start(
        self, node: int, *ancestry: int, task: str = "t", backbone: str = "DeepReasoner"
    ):
        return self.log(
            "agent.start",
            node,
            *ancestry,
            task=task,
            max_iter=4,
            backbone=backbone,
            namespace="root",
            run="20261002-000000-abcdef",
        )

    def think(self, node: int, *ancestry: int, reply: str):
        messages = [
            {"role": "user", "content": "t"},
            {"role": "assistant", "content": reply},
        ]
        return self.log("agent.loop", node, *ancestry, messages=messages)

    def execute(self, node: int, *ancestry: int, source: str, output: str):
        observation = f"<observation>\n{output}\n</observation>"
        return self.log(
            "repl.execute", node, *ancestry, source=source, observation=observation
        )

    def end(self, node: int, *ancestry: int, status: str = "done", **fields):
        return self.log("agent.end", node, *ancestry, status=status, iter=1, **fields)

    def events(self, *kinds: str) -> list[dict]:
        self._file.flush()
        rows = [json.loads(line) for line in self.path.read_text().splitlines()]
        return [r for r in rows if not kinds or r["kind"] in kinds]


@pytest.fixture
def rec(tmp_path):
    return Recording(tmp_path)


def test_a_think_reply_is_a_thought_and_a_cell_its_execution_closes(rec):
    rec.start(1).think(1, reply=repl("x = 1", "print(x)", think="Set x."))
    rec.execute(1, source="x = 1\nprint(x)", output="1")
    rec.execute(1, source="FinalAnswer('one')", output="FinalAnswer: 'one'")
    rec.end(1)
    thought, start, end, inferred_start, inferred_end, agent_end = rec.events(
        "thought", "cell.start", "cell.end", "agent.end"
    )
    assert thought == {"kind": "thought", "node": 1, "text": "Set x."}
    assert (start["cell"], start["code"], start["origin"]) == (
        1,
        "x = 1\nprint(x)",
        "think",
    )
    assert (end["cell"], end["output"], end["interrupted"]) == (1, "1", False)
    assert (inferred_start["cell"], inferred_start["origin"]) == (2, "inferred")
    assert inferred_end["output"] == "FinalAnswer: 'one'"
    assert (agent_end["status"], agent_end["answer"]) == ("done", "one")


def test_a_reply_without_a_block_is_only_a_thought(rec):
    rec.start(1).think(1, reply="<think>Hmm.</think> I will answer later.")
    assert [
        (e["kind"], e.get("text")) for e in rec.events("thought", "cell.start")
    ] == [("thought", "Hmm. I will answer later.")]


def test_a_child_names_its_parents_open_cell(rec):
    rec.start(1).think(1, reply=FAN_OUT).start(2, 1, 2, task="Summarize C1")
    child = rec.events("agent.start")[-1]
    assert (
        child["parent"],
        child["ancestry"],
        child["depth"],
        child["parent_cell"],
    ) == (1, [1, 2], 2, 1)
    assert (child["drive"], child["backbone"], child["dr_run"]) == (
        1,
        "chat",
        "20261002-000000-abcdef",
    )


def test_a_child_of_a_parent_with_no_open_cell_opens_an_inferred_one_first(rec):
    rec.start(1).start(2, 1, 2)
    inferred, child = rec.events("cell.start", "agent.start")[1:]
    assert (
        inferred["node"],
        inferred["cell"],
        inferred["code"],
        inferred["origin"],
    ) == (1, 1, "", "inferred")
    assert child["parent_cell"] == 1
    rec.execute(1, source="r = subagent('x')", output="(no output)")
    assert rec.events("cell.end")[-1]["code"] == "r = subagent('x')"


def test_puppeteered_turns_open_the_roots_first_cells_in_order(rec):
    rec.recorder.set_puppeteer([repl("a = 1"), repl("b = 2")])
    rec.start(1).log("agent.turn", 1, iter=1).execute(
        1, source="a = 1", output="(no output)"
    )
    rec.log("agent.turn", 1, iter=2).execute(1, source="b = 2", output="(no output)")
    rec.log("agent.turn", 1, iter=3).think(1, reply=repl("FinalAnswer(a + b)"))
    starts = [(e["code"], e["origin"]) for e in rec.events("cell.start")]
    assert starts == [
        ("a = 1", "puppeteered"),
        ("b = 2", "puppeteered"),
        ("FinalAnswer(a + b)", "think"),
    ]


def test_model_calls_are_priced_and_owned_by_the_agent_that_made_them(rec):
    usage = {"prompt_tokens": 30, "completion_tokens": 10}
    rec.start(1).log("llm.call", 1, model="m", usage=usage)
    rec.think(1, reply=repl("x = llm('hi')"))
    rec.log("llm.call", 3, 1, 3, kind="llm", model="unpriced", usage=usage)
    think, tool = rec.events("usage")
    assert think == {
        "kind": "usage",
        "node": 1,
        "call": "think",
        "model": "m",
        "tokens_in": 30,
        "tokens_out": 10,
        "cost_usd": pytest.approx(50e-6),
        "cost_source": "table",
        "context_window": 100,
    }
    assert (tool["node"], tool["call"], tool["cost_usd"], tool["cost_source"]) == (
        1,
        "tool",
        None,
        None,
    )


def test_a_claude_session_is_an_exact_cost_and_a_thought(rec):
    rec.start(1, backbone="ClaudeDeepReasoner")
    rec.log(
        "claude.call",
        2,
        1,
        2,
        kind="claude",
        cost_usd=0.01,
        model="sonnet",
        usage={"input_tokens": 5, "output_tokens": 3},
        response="ok",
    )
    start, usage, thought = rec.events("agent.start", "usage", "thought")
    assert start["backbone"] == "claude_code"
    assert (
        usage["call"],
        usage["cost_usd"],
        usage["cost_source"],
        usage["tokens_in"],
    ) == ("claude", 0.01, "claude", 5)
    assert thought["text"] == "ok"


def test_a_forks_own_llm_and_repl_nodes_work_for_the_fork(rec):
    """deep_reasoner logs a forked agent's think and cells on kind llm and kind repl
    nodes directly under the fork, not on the fork's own node."""
    rec.start(1).think(1, reply=FAN_OUT).start(3, 1, 3)
    rec.log("llm.call", 4, 1, 3, 4, kind="llm", model="m", usage={"prompt_tokens": 1})
    messages = [{"role": "assistant", "content": repl("FinalAnswer(42)")}]
    rec.log("agent.loop", 4, 1, 3, 4, kind="llm", messages=messages)
    observation = "<observation>\nFinalAnswer: 42\n</observation>"
    rec.log(
        "repl.execute",
        5,
        1,
        3,
        5,
        kind="repl",
        source="FinalAnswer(42)",
        observation=observation,
    )
    rec.end(3, 1, 3)
    usage, start, end, agent_end = rec.events(
        "usage", "cell.start", "cell.end", "agent.end"
    )[-4:]
    assert (usage["node"], usage["call"]) == (3, "think")
    assert (start["node"], start["code"], start["origin"]) == (
        3,
        "FinalAnswer(42)",
        "think",
    )
    assert (end["node"], end["cell"]) == (3, 1)
    assert (agent_end["node"], agent_end["answer"]) == (3, "42")


def test_an_agent_that_ends_in_a_cell_closes_it_interrupted(rec):
    rec.start(1).think(1, reply=repl("loop()")).end(
        1, status="failed", detail="RunKilled: "
    )
    cell_end, agent_end = rec.events("cell.end", "agent.end")
    assert (cell_end["cell"], cell_end["code"], cell_end["interrupted"]) == (
        1,
        "loop()",
        True,
    )
    assert (agent_end["status"], agent_end["detail"]) == ("failed", "RunKilled: ")


def test_an_exhausted_agent_answers_deep_reasoners_sentence(rec):
    rec.start(1).end(1, status="exhausted")
    assert rec.events("agent.end")[0]["answer"] == (
        "Agent failed to produce a final answer within 4 iterations."
    )


def test_a_second_start_of_a_node_is_its_next_drive_with_a_fresh_answer(rec):
    rec.start(1).execute(1, source="FinalAnswer(1)", output="FinalAnswer: 1").end(1)
    rec.start(1).think(1, reply="<think>no code</think>").end(1)
    first, second = rec.events("agent.end")
    assert first["answer"] == "1"
    assert second["answer"] is None
    assert [e["drive"] for e in rec.events("agent.start")] == [1, 2]


def fan_out_under_two(rec):
    """Root 1 runs children 2 and 3 in one cell; 2 runs 4 and 5 in its own cell."""
    rec.start(1).think(1, reply=FAN_OUT)
    rec.start(2, 1, 2).start(3, 1, 3)
    rec.think(2, 1, 2, reply=FAN_OUT).start(4, 1, 2, 4).start(5, 1, 2, 5)
    return rec


def test_interim_stops_the_branch_at_each_ones_next_turn(rec):
    fan_out_under_two(rec)
    receipt = rec.recorder.arm(2)
    assert (receipt.node, receipt.mode, receipt.accepted) == (2, "interim", True)
    with pytest.raises(StoppedByUser) as course:
        rec.log("agent.turn", 4, 1, 2, 4, iter=2)
    assert str(course.value) == "stopped #2 and its branch (#4, #5)."
    rec.end(4, 1, 2, 4, status="failed", detail=f"StoppedByUser: {course.value}")
    rec.end(5, 1, 2, 5, status="failed", detail="CancelledError: ")
    rec.execute(2, 1, 2, source="r = run_all(...)", output="Traceback ...")
    with pytest.raises(StoppedByUser) as department:
        rec.log("agent.turn", 2, 1, 2, iter=2)
    assert str(department.value) == (
        "stopped #2 and its branch (#4, #5). Its running sibling #3 in this run_all was "
        "stopped with it (A3)."
    )
    rec.end(2, 1, 2, status="failed", detail=f"StoppedByUser: {department.value}")
    rec.end(3, 1, 3, status="failed", detail="CancelledError: ")
    ends = {e["node"]: e for e in rec.events("agent.end")}
    assert {
        n: (e["status"], e["stopped_by"], e["collateral"]) for n, e in ends.items()
    } == {
        4: ("stopped", 2, False),
        5: ("stopped", 2, False),
        2: ("stopped", 2, False),
        3: ("stopped", 2, True),
    }
    accepted = rec.events("stop.accepted")
    assert accepted == [
        {
            "kind": "stop.accepted",
            "node": 2,
            "mode": "interim",
            "accepted": True,
            "reason": None,
            "backbone": "chat",
        }
    ]


def test_dean_stop_classifies_by_the_nearest_target_and_never_raises(rec):
    fan_out_under_two(rec)
    rec.recorder.note_stop(2, "dean")
    rec.log("agent.turn", 4, 1, 2, 4, iter=2)
    rec.end(4, 1, 2, 4, status="stopped").end(2, 1, 2, status="stopped").end(
        3, 1, 3, status="done"
    )
    ends = {e["node"]: (e["status"], e["stopped_by"]) for e in rec.events("agent.end")}
    assert ends == {4: ("stopped", 2), 2: ("stopped", 2), 3: ("done", None)}


@pytest.mark.parametrize(
    ("status", "detail", "expected"),
    [
        ("failed", "ValueError: boom", ("failed", None)),
        ("done", None, ("done", None)),
        ("exhausted", None, ("exhausted", None)),
        ("failed", "CancelledError: ", ("failed", None)),
    ],
)
def test_without_a_stop_deep_reasoners_status_stands(rec, status, detail, expected):
    fan_out_under_two(rec)
    rec.end(3, 1, 3, status=status, **({"detail": detail} if detail else {}))
    end = rec.events("agent.end")[0]
    assert (end["status"], end["stopped_by"]) == expected
    assert end["dr_status"] == status


def test_a_target_driven_again_after_its_stop_runs_normally(rec):
    rec.start(1).think(1, reply=FAN_OUT).start(2, 1, 2)
    rec.recorder.arm(2)
    with pytest.raises(StoppedByUser):
        rec.log("agent.turn", 2, 1, 2, iter=1)
    rec.end(2, 1, 2, status="failed", detail="StoppedByUser: stopped #2.")
    rec.start(2, 1, 2).log("agent.turn", 2, 1, 2, iter=1)
    assert rec.events("agent.start")[-1]["drive"] == 2


def test_a_stop_for_an_unknown_or_ended_agent_is_not_accepted(rec):
    rec.start(1).think(1, reply=FAN_OUT).start(2, 1, 2).end(2, 1, 2)
    unknown, ended = rec.recorder.arm(9), rec.recorder.arm(2)
    assert (unknown.accepted, ended.accepted) == (False, False)
    assert [e["accepted"] for e in rec.events("stop.accepted")] == [False, False]
    rec.log("agent.turn", 1, iter=2)


def test_text_over_8_mib_keeps_its_head_and_tail(rec):
    big = "a" * (5 * 1024 * 1024) + "b" * (5 * 1024 * 1024)
    rec.start(1).execute(1, source="print(big)", output=big)
    output = rec.events("cell.end")[0]["output"]
    assert output.startswith("aaa") and output.endswith("bbb")
    assert "bytes elided" in output
    assert len(output.encode()) <= 8 * 1024 * 1024 + 100


def test_tripwire_deep_reasoner_still_logs_everything_the_recorder_reads(
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
    rec.recorder.set_puppeteer(
        main_decomposition_turns("fan", cfg.task, cfg.decompositions)
    )
    set_cache_dir(None)
    configure_structlog_fixture(
        console=False, extra_processors=[rec.recorder], default_level=logging.CRITICAL
    )
    run_dir = tmp_path / "run"
    reasoner, alias = dr_cli.build_reasoner(
        cfg, run_dir=run_dir, main_decomposition="fan"
    )

    async def drive():
        with bound_contextvars(task_id="run", log_dir=str(run_dir)), alias:
            return [
                await reasoner.acall(cfg.task),
                await reasoner.acall("second question"),
            ]

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
