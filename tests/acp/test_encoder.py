"""The encoder, from hand-written RunEvents: §5.2 (native), §5.3 (flat), §5.7 (replay)."""

import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.catalog import CatalogSnapshot, CommandEntry
from deep_reasoning.acp.costs import NO_COST, CostLedger
from deep_reasoning.acp.encoder import (
    ChildRef,
    Encoder,
    closing_message,
    commands_update,
    config_update,
    idle_root_usage,
    namespace_option,
)
from deep_reasoning.acp.runlog import RUN_EVENT

R = "20261002-142233-4f1a2b"
ROOT = "s-7c1f9e0a2b4d6e8f"
DR2 = {
    "run": R,
    "node": 2,
    "parent": 1,
    "depth": 2,
    "namespace": "router",
    "backbone": "chat",
    "drive": 1,
}


def S(node):
    return f"{R}-n{node}"


def C(node, k):
    return f"{R}-n{node}-c{k}"


def ev(kind, **fields):
    return RUN_EVENT.validate_python({"kind": kind, **fields})


def run_start(after=None):
    return ev(
        "run.start",
        run=R,
        session=ROOT,
        index=1,
        after=after,
        cwd="/w",
        namespace="router",
        mode="native",
        decomposition=None,
        source={},
    )


def agent_start(
    node,
    parent=None,
    *,
    drive=1,
    parent_cell=None,
    task="Summarize the workload of the CS department.",
):
    ancestry = (
        [1] if parent is None else ([1, node] if parent == 1 else [1, parent, node])
    )
    return ev(
        "agent.start",
        node=node,
        parent=parent,
        ancestry=ancestry,
        depth=len(ancestry),
        task=task,
        namespace="router",
        backbone="chat",
        max_iter=10,
        drive=drive,
        parent_cell=parent_cell,
        dr_run="x",
    )


def cell_start(node, k, code="x = 1", origin="think"):
    return ev("cell.start", node=node, cell=k, code=code, origin=origin)


def cell_end(node, k, code="x = 1", output="1", interrupted=False):
    return ev(
        "cell.end", node=node, cell=k, code=code, output=output, interrupted=interrupted
    )


def usage(node, tokens_in=100, tokens_out=20, cost=0.001, source="table"):
    return ev(
        "usage",
        node=node,
        call="think",
        model="m",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
        cost_source=source,
        context_window=1000,
    )


def agent_end(
    node,
    status="done",
    answer="CS is heavy.",
    detail=None,
    stopped_by=None,
    collateral=False,
):
    return ev(
        "agent.end",
        node=node,
        status=status,
        dr_status=status,
        iter=2,
        answer=answer,
        detail=detail,
        stopped_by=stopped_by,
        collateral=collateral,
    )


def feed(encoder, *events):
    out = []
    for event in events:
        out.extend(encoder.feed(event))
    return out


def native(replay=False, carry=NO_COST):
    return Encoder(root=ROOT, run=R, mode="native", replay=replay, carry=carry)


def flat():
    return Encoder(root=ROOT, run=R, mode="flat")


def with_child(encoder):
    """A prompt in flight, the root in its first cell, child n2 announced in it."""
    feed(
        encoder,
        run_start(),
        ev("prompt.start", prompt=1, text="q", task="q", decomposition=None),
        agent_start(1),
        cell_start(1, 1),
    )
    return feed(encoder, agent_start(2, 1, parent_cell=1))


@pytest.mark.parametrize(
    ("after", "notice"),
    [
        (None, None),
        ("build_failed", None),
        ("stopped", texts.FRESH_AFTER_STOP),
        ("failed", texts.FRESH_AFTER_ERROR),
        ("crashed", texts.FRESH_AFTER_ERROR),
        ("lost", texts.FRESH_AFTER_RESTART),
        ("closed", texts.FRESH_AFTER_CLOSE),
    ],
)
def test_a_run_starts_with_the_notice_its_predecessors_end_calls_for(after, notice):
    updates = native().feed(run_start(after))
    expected = (
        []
        if notice is None
        else [
            (
                ROOT,
                {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": notice + "\n\n"},
                },
            )
        ]
    )
    assert updates == expected


def test_a_child_is_announced_on_its_parent_under_the_spawning_cell_then_given_its_task():
    announce, task = with_child(native())
    assert announce == (
        ROOT,
        {
            "sessionUpdate": "subagent_update",
            "sessionId": S(2),
            "title": "Summarize the workload of the CS department.",
            "capabilities": {"cancel": {}},
            "state": {"state": "running"},
            "_meta": {"openhands": {"parentToolCallId": C(1, 1)}, "deep_reasoner": DR2},
        },
    )
    assert task == (
        ROOT,
        {
            "sessionUpdate": "session_message",
            "messageId": f"{S(2)}-t1",
            "senderSessionId": ROOT,
            "recipientSessionId": S(2),
            "content": [
                {"type": "text", "text": "Summarize the workload of the CS department."}
            ],
        },
    )


def test_a_long_task_is_cut_in_the_title_and_sent_whole_as_description():
    encoder = native()
    task = "word " * 40 + "\nsecond line"
    feed(encoder, run_start(), agent_start(1), cell_start(1, 1))
    (_, announce), _ = encoder.feed(agent_start(2, 1, parent_cell=1, task=task))
    assert announce["title"] == ("word " * 40)[:120].rstrip() + " …"
    assert announce["description"] == task


def test_a_replayed_announcement_offers_no_cancel():
    (_, announce), _ = with_child(native(replay=True))
    assert "capabilities" not in announce


def test_a_child_driven_again_is_re_announced_running_with_its_drive():
    encoder = native()
    with_child(encoder)
    feed(encoder, agent_end(2), cell_end(1, 1), cell_start(1, 2))
    announce, task = encoder.feed(
        agent_start(2, 1, drive=2, parent_cell=2, task="Again.")
    )
    assert announce == (
        ROOT,
        {
            "sessionUpdate": "subagent_update",
            "sessionId": S(2),
            "title": "Again.",
            "state": {"state": "running"},
            "_meta": {
                "openhands": {"parentToolCallId": C(1, 2)},
                "deep_reasoner": {**DR2, "drive": 2},
            },
        },
    )
    assert task[1]["messageId"] == f"{S(2)}-t2"


def test_thoughts_go_to_their_agents_session_and_in_flat_only_the_roots():
    encoder, flat_encoder = native(), flat()
    with_child(encoder)
    with_child(flat_encoder)
    thought = ev("thought", node=2, text="Look first.")
    assert encoder.feed(thought) == [
        (
            S(2),
            {
                "sessionUpdate": "agent_thought_chunk",
                "content": {"type": "text", "text": "Look first."},
            },
        )
    ]
    assert flat_encoder.feed(thought) == []
    assert flat_encoder.feed(ev("thought", node=1, text="Root.")) == [
        (
            ROOT,
            {
                "sessionUpdate": "agent_thought_chunk",
                "content": {"type": "text", "text": "Root."},
            },
        )
    ]


def test_a_cell_is_a_tool_call_titled_by_its_first_line_and_completed_by_its_output():
    encoder = native()
    with_child(encoder)
    ((session, call),) = encoder.feed(cell_start(2, 1, code="xs = [1]\nprint(xs)"))
    assert (session, call) == (
        S(2),
        {
            "sessionUpdate": "tool_call",
            "toolCallId": C(2, 1),
            "title": "Run xs = [1] …",
            "kind": "execute",
            "status": "in_progress",
            "rawInput": {"command": "xs = [1]\nprint(xs)"},
            "_meta": {
                "deep_reasoner": {
                    "run": R,
                    "node": 2,
                    "parent": 1,
                    "depth": 2,
                    "cell": 1,
                    "origin": "think",
                }
            },
        },
    )
    ((session, done),) = encoder.feed(
        cell_end(2, 1, code="xs = [1]\nprint(xs)", output="[1]")
    )
    assert (session, done) == (
        S(2),
        {
            "sessionUpdate": "tool_call_update",
            "toolCallId": C(2, 1),
            "status": "completed",
            "content": [
                {"type": "content", "content": {"type": "text", "text": "[1]"}}
            ],
            "rawOutput": "[1]",
        },
    )


def test_an_inferred_cell_gets_its_title_and_code_when_it_ends():
    encoder = native()
    feed(encoder, run_start(), agent_start(1))
    ((_, call),) = encoder.feed(cell_start(1, 1, code="", origin="inferred"))
    assert (call["title"], call["rawInput"]) == ("Run …", {"command": ""})
    ((_, done),) = encoder.feed(cell_end(1, 1, code="r = subagent('x')", output="ok"))
    assert (done["title"], done["rawInput"]) == (
        "Run r = subagent('x')",
        {"command": "r = subagent('x')"},
    )


def test_an_interrupted_cell_fails_and_says_the_agent_stopped():
    encoder = native()
    feed(encoder, run_start(), agent_start(1), cell_start(1, 1))
    ((_, done),) = encoder.feed(cell_end(1, 1, output="", interrupted=True))
    assert done["status"] == "failed"
    assert done["content"] == [
        {
            "type": "content",
            "content": {
                "type": "text",
                "text": texts.cell_interrupted("the agent stopped"),
            },
        }
    ]


def test_flat_cells_and_cards_are_on_the_root_labelled_by_their_path():
    encoder = flat()
    ((session, card),) = with_child(encoder)
    assert (session, card) == (
        ROOT,
        {
            "sessionUpdate": "tool_call",
            "toolCallId": f"{S(2)}-a1",
            "title": "#1 › #2 · Summarize the workload of the CS department.",
            "kind": "other",
            "status": "in_progress",
            "rawInput": {"task": "Summarize the workload of the CS department."},
            "_meta": {"openhands": {"parentToolCallId": C(1, 1)}, "deep_reasoner": DR2},
        },
    )
    ((session, call),) = encoder.feed(cell_start(2, 1))
    assert (session, call["title"], call["toolCallId"]) == (
        ROOT,
        "#1 › #2 › Run x = 1",
        C(2, 1),
    )


def test_usage_rolls_up_to_every_ancestor_and_flushes_once_per_change():
    encoder = native()
    with_child(encoder)
    assert feed(encoder, usage(1, cost=0.002), usage(2, cost=0.001)) == []
    flushed = dict(encoder.flush_usage())
    assert flushed[S(2)] == {
        "sessionUpdate": "usage_update",
        "used": 120,
        "size": 1000,
        "cost": {"amount": pytest.approx(0.001), "currency": "USD"},
        "_meta": {
            "deep_reasoner": {
                "cost_source": "table",
                "tokens_in": 100,
                "tokens_out": 20,
                "unknown_calls": 0,
            }
        },
    }
    assert flushed[ROOT]["cost"]["amount"] == pytest.approx(0.003)
    assert flushed[ROOT]["_meta"]["deep_reasoner"]["tokens_in"] == 200
    assert encoder.flush_usage() == []


def test_a_call_without_a_price_makes_the_cost_unknown_not_zero():
    encoder = native()
    with_child(encoder)
    feed(encoder, usage(2, cost=None, source=None), usage(2))
    flushed = dict(encoder.flush_usage())
    assert "cost" not in flushed[S(2)]
    assert flushed[S(2)]["_meta"]["deep_reasoner"]["unknown_calls"] == 1
    assert "cost" not in flushed[ROOT]
    assert encoder.root_cost.complete is False


def test_flat_sends_usage_only_on_the_root():
    encoder = flat()
    with_child(encoder)
    encoder.feed(usage(2))
    assert [sid for sid, _ in encoder.flush_usage()] == [ROOT]


def test_an_accepted_stop_is_acknowledged_on_the_childs_own_session():
    encoder = native()
    with_child(encoder)
    accepted = ev(
        "stop.accepted",
        node=2,
        mode="interim",
        accepted=True,
        reason=None,
        backbone="chat",
    )
    refused = ev(
        "stop.accepted",
        node=2,
        mode="interim",
        accepted=False,
        reason="ended",
        backbone="chat",
    )
    assert encoder.feed(accepted) == [
        (
            S(2),
            {
                "sessionUpdate": "agent_thought_chunk",
                "content": {
                    "type": "text",
                    "text": texts.stop_requested("interim", "chat"),
                },
            },
        )
    ]
    assert encoder.feed(refused) == []


@pytest.mark.parametrize(
    ("end", "message", "reason", "outcome"),
    [
        (agent_end(2), "CS is heavy.", "end_turn", {"status": "done"}),
        (
            agent_end(2, "exhausted", answer="Agent failed."),
            "Agent failed.",
            "max_turn_requests",
            {"status": "exhausted"},
        ),
        (
            agent_end(2, "failed", answer=None, detail="ValueError: boom"),
            "Failed: ValueError: boom",
            "end_turn",
            {"status": "failed", "detail": "ValueError: boom"},
        ),
        (
            agent_end(
                2,
                "stopped",
                answer=None,
                detail="StoppedByUser: stopped #2.",
                stopped_by=2,
            ),
            None,
            "cancelled",
            {
                "status": "stopped",
                "detail": "StoppedByUser: stopped #2.",
                "stopped_by": 2,
            },
        ),
        (
            agent_end(
                2,
                "stopped",
                answer=None,
                detail="CancelledError: ",
                stopped_by=3,
                collateral=True,
            ),
            None,
            "cancelled",
            {
                "status": "stopped",
                "detail": "CancelledError: ",
                "stopped_by": 3,
                "collateral": True,
            },
        ),
    ],
)
def test_a_child_ends_with_its_answer_its_cost_then_idle_on_its_parent(
    end, message, reason, outcome
):
    encoder = native()
    with_child(encoder)
    encoder.feed(usage(2))
    updates = encoder.feed(end)
    if message is not None:
        sent = updates.pop(0)
        assert sent == (
            S(2),
            {
                "sessionUpdate": "session_message",
                "messageId": f"{S(2)}-r1",
                "senderSessionId": S(2),
                "recipientSessionId": ROOT,
                "content": [{"type": "text", "text": message}],
            },
        )
    (cost_session, cost), (session, idle) = updates
    assert (cost_session, cost["sessionUpdate"]) == (S(2), "usage_update")
    assert (session, idle) == (
        ROOT,
        {
            "sessionUpdate": "subagent_update",
            "sessionId": S(2),
            "state": {"state": "idle", "stopReason": reason},
            "_meta": {
                "openhands": {"parentToolCallId": C(1, 1)},
                "deep_reasoner": {**DR2, **outcome},
            },
        },
    )
    assert encoder.child(S(2)) == ChildRef(node=2, running=False)


@pytest.mark.parametrize(
    ("end", "status", "text"),
    [
        (agent_end(2), "completed", "CS is heavy."),
        (
            agent_end(2, "failed", answer=None, detail="ValueError: boom"),
            "failed",
            "Failed: ValueError: boom",
        ),
        (
            agent_end(
                2,
                "stopped",
                answer=None,
                detail="StoppedByUser: stopped #2.",
                stopped_by=2,
            ),
            "failed",
            "StoppedByUser: stopped #2.",
        ),
    ],
)
def test_a_flat_childs_card_closes_with_its_outcome(end, status, text):
    encoder = flat()
    with_child(encoder)
    ((session, card),) = encoder.feed(end)
    assert session == ROOT
    assert (card["toolCallId"], card["status"]) == (f"{S(2)}-a1", status)
    assert card["content"] == [
        {"type": "content", "content": {"type": "text", "text": text}}
    ]
    assert card["_meta"]["deep_reasoner"]["status"] == end.status


@pytest.mark.parametrize(
    ("end", "text", "outcome"),
    [
        (
            ev("prompt.end", prompt=1, outcome="answered", answer="42", detail=None),
            "42",
            "answered",
        ),
        (
            ev(
                "prompt.end",
                prompt=1,
                outcome="exhausted",
                answer="Agent failed.",
                detail=None,
            ),
            "Agent failed.",
            "exhausted",
        ),
        (
            ev(
                "prompt.end",
                prompt=1,
                outcome="failed",
                answer=None,
                detail="ValueError: x",
            ),
            texts.root_failed("ValueError: x"),
            "failed",
        ),
        (
            ev(
                "prompt.end",
                prompt=1,
                outcome="build_failed",
                answer=None,
                detail="ValueError: k",
            ),
            texts.build_failed("ValueError: k"),
            "build_failed",
        ),
    ],
)
def test_a_prompt_ends_with_the_closing_message_and_the_roots_usage(end, text, outcome):
    encoder = native()
    feed(
        encoder,
        run_start(),
        ev("prompt.start", prompt=1, text="q", task="q", decomposition=None),
        agent_start(1),
    )
    message, (session, cost) = encoder.feed(end)
    assert message == closing_message(ROOT, text, run=R, prompt=1, outcome=outcome)
    assert (session, cost["sessionUpdate"]) == (ROOT, "usage_update")
    assert encoder.prompt_in_flight is False


def test_a_run_stopped_in_flight_ends_every_running_agent_deepest_first():
    encoder = native()
    with_child(encoder)
    feed(
        encoder,
        cell_start(2, 1),
        agent_start(4, 2, parent_cell=1),
        agent_start(5, 2, parent_cell=1),
    )
    updates = encoder.feed(ev("run.end", reason="stopped", exit_code=-15, detail=None))
    stopped = texts.cell_interrupted("the run was stopped")
    shape = [
        (
            sid,
            u["sessionUpdate"],
            u.get("toolCallId") or u.get("sessionId"),
            u.get("state"),
        )
        for sid, u in updates
    ]
    idle = {"state": "idle", "stopReason": "cancelled"}
    assert shape == [
        (S(2), "subagent_update", S(4), idle),
        (S(2), "subagent_update", S(5), idle),
        (S(2), "tool_call_update", C(2, 1), None),
        (ROOT, "subagent_update", S(2), idle),
        (ROOT, "tool_call_update", C(1, 1), None),
        (ROOT, "agent_message_chunk", None, None),
        (ROOT, "usage_update", None, None),
    ]
    assert updates[2][1]["content"][0]["content"]["text"] == stopped
    assert updates[0][1]["_meta"]["deep_reasoner"]["status"] == "stopped"
    assert updates[5] == closing_message(
        ROOT, texts.ROOT_STOPPED, run=R, prompt=1, outcome="stopped"
    )


def test_a_crashed_run_leaves_children_idle_without_a_reason():
    encoder = native()
    with_child(encoder)
    updates = encoder.feed(
        ev("run.end", reason="crashed", exit_code=1, detail="/h/runs/r/worker.log")
    )
    idle = next(u for _, u in updates if u["sessionUpdate"] == "subagent_update")
    assert idle["state"] == {"state": "idle"}
    assert idle["_meta"]["deep_reasoner"]["status"] == "crashed"
    assert updates[-2] == closing_message(
        ROOT,
        texts.crashed(1, "/h/runs/r/worker.log"),
        run=R,
        prompt=1,
        outcome="crashed",
    )


def test_a_flat_run_stopped_in_flight_fails_cards_and_cells():
    encoder = flat()
    with_child(encoder)
    updates = encoder.feed(ev("run.end", reason="stopped", exit_code=-15, detail=None))
    ids = [
        (u["sessionUpdate"], u.get("toolCallId"), u.get("status")) for _, u in updates
    ]
    assert ids[:2] == [
        ("tool_call_update", f"{S(2)}-a1", "failed"),
        ("tool_call_update", C(1, 1), "failed"),
    ]


@pytest.mark.parametrize("reason", ["failed", "build_failed", "closed", "stopped"])
def test_a_run_ending_between_prompts_sends_nothing(reason):
    encoder = native()
    feed(
        encoder,
        run_start(),
        ev("prompt.start", prompt=1, text="q", task="q", decomposition=None),
        agent_start(1),
        ev("prompt.end", prompt=1, outcome="answered", answer="a", detail=None),
    )
    assert encoder.feed(ev("run.end", reason=reason, exit_code=0, detail=None)) == []


def test_a_lost_run_replays_with_a_closing_message_and_nothing_for_its_children():
    encoder = native(replay=True)
    with_child(encoder)
    assert encoder.feed(ev("run.end", reason="lost", exit_code=None, detail=None)) == [
        closing_message(ROOT, texts.REPLAY_LOST, run=R, prompt=1, outcome="lost")
    ]


def test_a_replay_shows_what_the_user_typed():
    prompt = ev(
        "prompt.start", prompt=1, text="/triage go", task="go", decomposition="triage"
    )
    assert native().feed(prompt) == []
    assert native(replay=True).feed(prompt) == [
        (
            ROOT,
            {
                "sessionUpdate": "user_message_chunk",
                "content": {"type": "text", "text": "/triage go"},
            },
        )
    ]


def test_the_roots_cost_continues_from_the_conversations_earlier_runs():
    encoder = native(carry=CostLedger(usd=0.5, tokens_in=10, tokens_out=5))
    feed(encoder, run_start(), agent_start(1), usage(1, cost=0.25))
    assert encoder.root_cost == CostLedger(
        usd=0.75, complete=True, tokens_in=110, tokens_out=25
    )
    _, root = encoder.root_usage()
    assert root["cost"]["amount"] == pytest.approx(0.75)


def test_a_root_without_a_run_reports_the_conversations_cost():
    _, update = idle_root_usage(ROOT, CostLedger(usd=0.0089, tokens_in=3, tokens_out=4))
    assert update == {
        "sessionUpdate": "usage_update",
        "used": 0,
        "size": 0,
        "cost": {"amount": 0.0089, "currency": "USD"},
        "_meta": {
            "deep_reasoner": {
                "cost_source": None,
                "tokens_in": 3,
                "tokens_out": 4,
                "unknown_calls": 0,
            }
        },
    }


SNAPSHOT = CatalogSnapshot(
    namespaces=("root", "router"),
    default_namespace="router",
    commands={
        "router": (
            CommandEntry(
                "summarize-then-rank",
                "summarize then rank",
                "comparing many courses",
                "what to compare",
            ),
        )
    },
)


def test_commands_carry_their_decomposition_and_namespace():
    assert commands_update(ROOT, SNAPSHOT.commands["router"], "router") == (
        ROOT,
        {
            "sessionUpdate": "available_commands_update",
            "availableCommands": [
                {
                    "name": "summarize-then-rank",
                    "description": "comparing many courses",
                    "input": {"hint": "what to compare"},
                    "_meta": {
                        "deep_reasoner": {
                            "decomposition": "summarize then rank",
                            "namespace": "router",
                        }
                    },
                }
            ],
        },
    )


def test_the_namespace_option_offers_every_namespace_until_fixed():
    assert namespace_option(SNAPSHOT, "router", fixed=False) == {
        "id": "namespace",
        "name": "Namespace",
        "type": "select",
        "currentValue": "router",
        "description": texts.NAMESPACE_OPEN,
        "options": [
            {"value": "root", "name": "root"},
            {"value": "router", "name": "router"},
        ],
    }
    fixed = namespace_option(SNAPSHOT, "router", fixed=True)
    assert (fixed["options"], fixed["description"]) == (
        [{"value": "router", "name": "router"}],
        texts.NAMESPACE_FIXED_NOTE,
    )
    assert config_update(ROOT, [fixed]) == (
        ROOT,
        {"sessionUpdate": "config_option_update", "configOptions": [fixed]},
    )
