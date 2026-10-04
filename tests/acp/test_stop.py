"""Stop on one sub-agent: its branch stops at its next turn, through deep_reasoner's
stop(node_id) (E3, §6.3)."""

import asyncio
from collections import Counter

from deep_reasoning.acp import texts
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from tests.acp.harness import dr_acp, run, run_ids, scripted_env
from tests.acp.scenarios import BY_NAME, repl, scripted, task_and_turn

DEPARTMENTS = [f"D{i}" for i in range(20)]
COURSES = ["D0a", "D0b"]
PLAN = {
    "Compare departments.": [
        repl(
            f"found = run_all({{d: anext(subagent().send(f'Survey {{d}}.')) for d in {DEPARTMENTS!r}}})",
            "print(found)",
        ),
        repl("FinalAnswer('compared')"),
    ],
    "Survey D0.": [
        repl(
            f"found = run_all({{c: anext(subagent().send(f'Read {{c}}.')) for c in {COURSES!r}}})",
            "print(found)",
        ),
        repl("FinalAnswer(found)"),
    ],
    **{
        f"Survey {d}.": [repl(f"print({d!r})"), repl(f"FinalAnswer('{d} surveyed')")]
        for d in DEPARTMENTS[1:]
    },
    **{
        f"Read {c}.": [repl(f"print({c!r})")] * 5 + [repl(f"FinalAnswer('{c} read')")]
        for c in COURSES
    },
}
BRANCH_TASKS = {"Survey D0.", *(f"Read {c}." for c in COURSES)}


async def stop_the_department(env, respond, tmp_path, home, work):
    """Ask, stop D0 once one of its course agents is announced, and collect the evidence."""
    async with FakeOpenAI(respond, latency_s=0.2) as model:
        config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
        async with dr_acp(config, home, env=env) as client:
            root = await client.open_session(work)
            turn = asyncio.create_task(client.ask(root, "Compare departments."))
            course = await client.printer.wait_until(
                lambda p: next(
                    (
                        a
                        for a in p.subagents.values()
                        if a.field_meta["deep_reasoner"]["depth"] == 3
                    ),
                    None,
                ),
                timeout=60,
            )
            department = client.printer.subagents[course.parent_session_id]
            await client.conn.cancel(session_id=department.session_id)
            response = await turn
            (run_id,) = run_ids(client.printer.updates)
            log = client.run_log(run_id)
            return client, root, department, response, log, model.calls


def by_task(subagents):
    return {a.title: a for a in subagents.values()}


def evidence_common(client, root, department, response, log, calls):
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    accepted = next(e for e in log if e.kind == "stop.accepted")
    assert accepted.accepted
    assert any(e.kind == "stop.request" and e.node == accepted.node for e in log)
    tasks = [task_and_turn(c.messages)[0] for c in calls if c.started > accepted.t]
    late = Counter(task for task in tasks if task in BRANCH_TASKS)
    # A turn that began before the stop may still make its call; no later turn may.
    assert all(n <= 1 for n in late.values()), late
    agents = by_task(client.printer.subagents)
    for title in BRANCH_TASKS:
        assert (agents[title].state, agents[title].stop_reason) == ("idle", "cancelled")
        assert agents[title].field_meta["deep_reasoner"]["status"] == "stopped"
    d0 = agents["Survey D0."].field_meta["deep_reasoner"]
    assert d0.get("stopped_by", d0["node"]) == d0["node"]
    for course in COURSES:
        assert (
            agents[f"Read {course}."].field_meta["deep_reasoner"]["stopped_by"]
            == d0["node"]
        )
    return agents, d0


def root_cell_output(client, root):
    first = next(
        u for u in client.updates_on(root) if u["sessionUpdate"] == "tool_call_update"
    )
    return first["content"][0]["content"]["text"]


def test_dean_stop_ends_the_branch_and_the_parent_keeps_every_siblings_result(
    tmp_path, home, work
):
    client, root, department, response, log, calls = run(
        stop_the_department(scripted_env(), scripted(PLAN), tmp_path, home, work)
    )
    agents, d0 = evidence_common(client, root, department, response, log, calls)
    siblings = [
        a
        for title, a in agents.items()
        if title.startswith("Survey D") and title != "Survey D0."
    ]
    assert {a.field_meta["deep_reasoner"]["status"] for a in siblings} == {"done"}
    output = root_cell_output(client, root)
    assert f"Stopped(node={d0['node']})" in output
    for d in DEPARTMENTS[1:]:
        assert f"{d} surveyed" in output
    assert texts.stop_requested("dean", "chat") in department_thoughts(
        client, department
    )


def department_thoughts(client, department):
    return [
        u["content"]["text"]
        for u in client.updates_on(department.session_id)
        if u["sessionUpdate"] == "agent_thought_chunk"
    ]
