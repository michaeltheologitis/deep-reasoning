"""The live tier: real runs on gpt-6-luna through dr-acp's public interface.

Run with `uv run pytest -m live`; skipped without OPENAI_API_KEY. A few cents per run.
The config is docs/configs/advising: four courses in two departments, and one program,
`compare departments`, that gives each department to a sub-agent and asks each
department to give each of its courses to one more.
"""

import asyncio
import os
from pathlib import Path

import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.testing.tree import tree
from tests.acp.harness import REPO, dr_acp, run, run_ids, scripted_env
from tests.acp.scenarios import acp_tree, deep_reasoner_tree, tree_evidence

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not set"
    ),
]

ADVISING = REPO / "docs" / "configs" / "advising" / "main.yaml"
QUESTION = (
    "/compare-departments Which department is lighter for a first-year student, "
    "CS or STAT?"
)


def with_key() -> dict[str, str]:
    return scripted_env(OPENAI_API_KEY=os.environ["OPENAI_API_KEY"])


def costs_in_log(client, run_id: str) -> list[float | None]:
    return [e.cost_usd for e in client.run_log(run_id) if e.kind == "usage"]


def test_live_the_stream_rebuilds_deep_reasoners_tree_and_the_root_pays_for_all(
    home: Path, work: Path
):
    async def body():
        async with dr_acp(ADVISING, home, env=with_key()) as client:
            root = await client.open_session(work)
            response = await client.ask(root, QUESTION)
            return client, root, response

    client, root, response = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    (run_id,) = run_ids(client.printer.updates)
    rebuilt = tree(client.printer.updates)
    run_dir = home / "runs" / run_id
    agents, own = acp_tree(rebuilt), deep_reasoner_tree(run_dir)
    assert agents == own, tree_evidence(agents, own, run_dir)
    assert len(agents) >= 3, "the program gives each department to a sub-agent"
    answer = next(
        u["content"]["text"]
        for u in reversed(client.updates_on(root))
        if u["sessionUpdate"] == "agent_message_chunk"
    )
    assert "STAT" in answer
    calls = costs_in_log(client, run_id)
    assert None not in calls, "every gpt-6-luna call has a price"
    root_cost = rebuilt.runs[0].cost_usd
    assert root_cost == pytest.approx(sum(calls))
    children = [
        s.field_meta["deep_reasoner"] for s in client.printer.subagents.values()
    ]
    assert {c["status"] for c in children} <= {"done", "exhausted"}, children
    child_costs = [
        a.cost_usd for a in _agents(rebuilt.runs[0].root) if a.short != "root"
    ]
    assert all(0 < c < root_cost for c in child_costs)


def _agents(agent):
    yield agent
    for item in agent.items:
        for child in getattr(item, "agents", []):
            yield from _agents(child)


def test_live_stopping_a_department_stops_it_and_its_course_agents(
    home: Path, work: Path
):
    async def body():
        async with dr_acp(ADVISING, home, env=with_key()) as client:
            root = await client.open_session(work)
            turn = asyncio.create_task(client.ask(root, QUESTION))
            course = await client.printer.wait_until(
                lambda p: next(
                    (
                        a
                        for a in p.subagents.values()
                        if a.field_meta["deep_reasoner"]["depth"] == 3
                    ),
                    None,
                ),
                timeout=180,
            )
            department = client.printer.subagents[course.parent_session_id]
            await client.conn.cancel(session_id=department.session_id)
            response = await turn
            (run_id,) = run_ids(client.printer.updates)
            return client, department, response, client.run_log(run_id)

    client, department, response, log = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    target = department.field_meta["deep_reasoner"]["node"]
    accepted = next(e for e in log if e.kind == "stop.accepted")
    assert (accepted.node, accepted.accepted) == (target, True)
    branch = [
        a
        for a in client.printer.subagents.values()
        if a.session_id == department.session_id
        or a.parent_session_id == department.session_id
    ]
    assert len(branch) >= 2
    for agent in branch:
        assert (agent.state, agent.stop_reason) == ("idle", "cancelled")
        assert agent.field_meta["deep_reasoner"]["status"] == "stopped"
    nodes = {a.field_meta["deep_reasoner"]["node"] for a in branch}
    late_calls = [
        e for e in log if e.kind == "usage" and e.node in nodes and e.t > accepted.t
    ]
    assert len(late_calls) <= len(nodes), "at most the call each had in flight"
    thoughts = [
        u["content"]["text"]
        for u in client.updates_on(department.session_id)
        if u["sessionUpdate"] == "agent_thought_chunk"
    ]
    assert texts.stop_requested("dean", "chat") in thoughts


def test_live_without_the_key_the_run_fails_before_any_call_and_says_which(
    home: Path, work: Path
):
    async def body():
        async with dr_acp(ADVISING, home, env=scripted_env()) as client:
            root = await client.open_session(work)
            response = await client.ask(root, QUESTION)
            return client, root, response

    client, root, response = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "build_failed"
    closing = next(
        u
        for u in client.updates_on(root)
        if u["sessionUpdate"] == "agent_message_chunk"
    )
    detail = (
        "ValueError: Missing API key. Set `OPENAI_API_KEY` (preferred) or "
        "`OPENAI_API_KEY`."
    )
    assert closing["content"]["text"] == texts.build_failed(detail)
    assert costs_in_log(client, response.field_meta["deep_reasoner"]["run"]) == []
