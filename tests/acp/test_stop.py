"""Stop on one sub-agent: its branch stops at its next turn, through the interim and
through (a fake of) Dean's stop(node_id) (E3, §6.3)."""

import asyncio
import threading
import traceback
from collections import Counter

import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.acp.worker.recorder import EventSink, Recorder
from deep_reasoning.acp.worker.stop import (
    DeanStop,
    InterimStop,
    StoppedByUser,
    resolve_stop_adapter,
)
from tests.acp.harness import dr_acp, run, run_ids, scripted_env
from tests.acp.scenarios import BY_NAME, attributed_task, repl, scripted, task_and_turn

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
SIBLING_TASKS = {f"Survey {d}." for d in DEPARTMENTS[1:]}


def holding_the_siblings(respond):
    """D0's siblings get their first answer only at the root's next turn, once run_all
    has ended: each is still awaiting its model when D0's StoppedByUser ends run_all.
    An openai call cancelled mid-response can swallow the cancellation and run on to an
    answer (httpx 0.28, httpcore 1.0, anyio 4), and a sibling the message names would
    then end done, not stopped with it."""
    root_moved_on = threading.Event()

    def held(messages):
        task, turn = task_and_turn(messages)
        if task == "Compare departments." and turn > 0:
            root_moved_on.set()
        elif task in SIBLING_TASKS:
            root_moved_on.wait(timeout=60)
        return respond(messages)

    return held


def stop_the_department(env, respond):
    """Ask, stop D0 once one of its course agents is announced, and collect the evidence."""

    async def body(tmp_path, home, work):
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
                return (
                    client,
                    root,
                    department,
                    response,
                    client.run_log(run_id),
                    model.calls,
                )

    return body


def by_task(subagents):
    return {a.title: a for a in subagents.values()}


def evidence_common(client, root, department, response, log, calls):
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    accepted = next(e for e in log if e.kind == "stop.accepted")
    assert accepted.accepted
    assert any(e.kind == "stop.request" and e.node == accepted.node for e in log)
    late = Counter(
        attributed_task(c.messages)
        for c in calls
        if c.started > accepted.t and attributed_task(c.messages) in BRANCH_TASKS
    )
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


def test_interim_stops_the_branch_at_its_next_turn_and_names_the_siblings_it_took(
    tmp_path, home, work
):
    respond = holding_the_siblings(scripted(PLAN))
    client, root, department, response, log, calls = run(
        stop_the_department(scripted_env(), respond)(tmp_path, home, work)
    )
    agents, d0 = evidence_common(client, root, department, response, log, calls)
    output = root_cell_output(client, root)
    assert "deep_reasoning.acp.worker.stop.StoppedByUser: stopped #" in output
    collateral = sorted(
        a.field_meta["deep_reasoner"]["node"]
        for a in agents.values()
        if a.field_meta["deep_reasoner"].get("collateral")
    )
    for node in collateral:
        assert (
            agents_by_node(agents)[node].field_meta["deep_reasoner"]["stopped_by"]
            == d0["node"]
        )
    assert output.rstrip().endswith(
        texts.stopped_by_user(
            d0["node"], tuple(sorted(course_nodes(agents))), tuple(collateral)
        )
    )
    assert texts.stop_requested("interim", "chat") in department_thoughts(
        client, department
    )


def test_dean_stop_ends_the_branch_and_the_parent_keeps_every_siblings_result(
    tmp_path, home, work
):
    env = scripted_env(DR_ACP_STOP_API="tests.acp.fakes.dean_stop:stop")
    client, root, department, response, log, calls = run(
        stop_the_department(env, scripted(PLAN))(tmp_path, home, work)
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


def agents_by_node(agents):
    return {a.field_meta["deep_reasoner"]["node"]: a for a in agents.values()}


def course_nodes(agents):
    return [agents[f"Read {c}."].field_meta["deep_reasoner"]["node"] for c in COURSES]


def department_thoughts(client, department):
    return [
        u["content"]["text"]
        for u in client.updates_on(department.session_id)
        if u["sessionUpdate"] == "agent_thought_chunk"
    ]


@pytest.mark.parametrize(
    ("branch", "siblings", "sentence"),
    [
        ((), (), "stopped #2."),
        ((4, 5), (), "stopped #2 and its branch (#4, #5)."),
        (
            (4,),
            (3,),
            "stopped #2 and its branch (#4). Its running sibling #3 in this run_all was stopped with it (A3).",
        ),
        (
            (),
            (3, 6),
            "stopped #2. Its running siblings #3, #6 in this run_all were stopped with it (A3).",
        ),
    ],
)
def test_stopped_by_user_says_what_stopped_with_it(branch, siblings, sentence):
    error = StoppedByUser(2, branch, siblings)
    assert str(error) == sentence
    assert (error.target, error.branch, error.siblings) == (2, branch, siblings)


def test_a_cell_shows_stopped_by_user_under_its_qualified_name():
    try:
        raise StoppedByUser(2, (4, 5), ())
    except StoppedByUser:
        last = traceback.format_exc().rstrip().splitlines()[-1]
    assert (
        last
        == "deep_reasoning.acp.worker.stop.StoppedByUser: stopped #2 and its branch (#4, #5)."
    )


def test_the_adapter_is_the_interim_unless_a_stop_api_is_named(tmp_path):
    with open(tmp_path / "events", "wb") as out:
        recorder = Recorder(EventSink(out.fileno()), PriceTable({}))
        assert isinstance(resolve_stop_adapter(recorder, None), InterimStop)
        dean = resolve_stop_adapter(recorder, "builtins:abs")
    assert isinstance(dean, DeanStop)
    assert dean.mode == "dean"
