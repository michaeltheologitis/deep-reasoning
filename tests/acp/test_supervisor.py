"""A live run's worker: root Stop (E3), a worker that dies (E2), the heartbeat (§4.2, §6.4)."""

import asyncio
import time

from deep_reasoning.acp import texts
from deep_reasoning.acp.recap import Turn, recap_of
from deep_reasoning.acp.runlog import RecapNote
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from tests.acp.harness import dr_acp, run, run_ids
from tests.acp.scenarios import (
    BY_NAME,
    FIRST_QUESTION,
    answering_from_the_recap,
    repl,
    scripted,
)

CHILDREN = [f"K{i}" for i in range(20)]
PLAN = {
    "Spin.": [repl("while True: pass")],
    "Fan out and spin.": [
        repl(
            f"r = run_all([anext(subagent().send(f'Spin {{k}}.')) for k in {CHILDREN!r}])"
        )
    ],
    **{f"Spin {k}.": [repl("while True: pass")] for k in CHILDREN},
    "Die.": [repl("import os", "os._exit(1)")],
    "Sleep.": [repl("import time", "time.sleep(2)"), repl("FinalAnswer('rested')")],
    "Again.": [repl("FinalAnswer('fresh')")],
    "Which course is lightest?": [repl("FinalAnswer('STAT101')")],
}
ONE_TURN = RecapNote(turns=1, left_out=0, shortened=False)


async def stop_root_when(client, root, text, ready):
    """Send text, wait until ready(printer), stop the root; how long the answer took."""
    turn = asyncio.create_task(client.ask(root, text))
    await client.printer.wait_until(ready, timeout=60)
    started = time.monotonic()
    await client.conn.cancel(session_id=root)
    response = await turn
    return response, time.monotonic() - started


def test_root_stop_in_a_busy_cell_answers_cancelled_within_two_seconds(
    tmp_path, home, work
):
    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                response, took = await stop_root_when(
                    client,
                    root,
                    "Spin.",
                    lambda p: any(
                        u["sessionUpdate"] == "tool_call" for _, u in p.updates
                    ),
                )
                stopped = client.updates_on(root)
                (run_id,) = run_ids(client.printer.updates)
                log = client.run_log(run_id)
                seen = len(stopped)
                await client.ask(root, "Again.")
                notice = client.updates_on(root)[seen]
        return response, took, stopped, log, notice

    response, took, stopped, log, notice = run(body())
    assert took < 2.0
    assert response.stop_reason == "cancelled"
    assert response.field_meta["deep_reasoner"]["outcome"] == "stopped"
    assert (log[-1].kind, log[-1].reason) == ("run.end", "stopped")
    cell, closing, usage = stopped[-3:]
    assert (cell["sessionUpdate"], cell["status"]) == ("tool_call_update", "failed")
    assert cell["content"][0]["content"]["text"] == texts.cell_interrupted(
        "the run was stopped"
    )
    assert closing["content"]["text"] == texts.ROOT_STOPPED
    assert closing["_meta"]["deep_reasoner"]["outcome"] == "stopped"
    assert usage["sessionUpdate"] == "usage_update"
    assert notice["content"]["text"] == (
        texts.fresh_run_notice("stopped", ONE_TURN) + "\n\n"
    )


def test_root_stop_under_twenty_spinning_children_ends_each_within_two_seconds(
    tmp_path, home, work
):
    def all_announced(printer):
        return len(printer.subagents) == len(CHILDREN)

    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                response, took = await stop_root_when(
                    client, root, "Fan out and spin.", all_announced
                )
        return response, took, client.printer.subagents

    response, took, subagents = run(body())
    assert took < 2.0
    assert response.stop_reason == "cancelled"
    assert {(a.state, a.stop_reason) for a in subagents.values()} == {
        ("idle", "cancelled")
    }
    assert {a.field_meta["deep_reasoner"]["status"] for a in subagents.values()} == {
        "stopped"
    }


def test_a_worker_that_dies_mid_prompt_is_reported_crashed_and_the_next_prompt_is_fresh(
    tmp_path, home, work
):
    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                crashed = await client.ask(root, "Die.")
                closing = client.updates_on(root)[-2]
                seen = len(client.updates_on(root))
                fresh = await client.ask(root, "Again.")
                notice = client.updates_on(root)[seen]
                log = client.run_log(crashed.field_meta["deep_reasoner"]["run"])
        return crashed, closing, fresh, notice, log

    crashed, closing, fresh, notice, log = run(body())
    assert crashed.stop_reason == "end_turn"
    assert crashed.field_meta["deep_reasoner"]["outcome"] == "crashed"
    assert (log[-1].kind, log[-1].reason, log[-1].exit_code) == (
        "run.end",
        "crashed",
        1,
    )
    worker_log = (
        home / "runs" / crashed.field_meta["deep_reasoner"]["run"] / "worker.log"
    )
    assert closing["content"]["text"] == texts.crashed(1, str(worker_log))
    assert notice["content"]["text"] == (
        texts.fresh_run_notice("crashed", ONE_TURN) + "\n\n"
    )
    assert fresh.field_meta["deep_reasoner"]["outcome"] == "answered"


def test_a_long_cell_keeps_the_root_sending_usage_on_the_heartbeat(
    tmp_path, home, work
):
    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home, args=("--heartbeat", "0.5")) as client:
                root = await client.open_session(work)
                await client.ask(root, "Sleep.")
                return client.updates_on(root)

    updates = run(body())
    kinds = [u["sessionUpdate"] for u in updates]
    start = kinds.index("tool_call")
    end = kinds.index("tool_call_update")
    assert kinds[start:end].count("usage_update") >= 2


def spinning(printer) -> bool:
    """The spinning cell has started; the earlier prompt's cells are tool calls too."""
    return any(
        u["sessionUpdate"] == "tool_call"
        and u["rawInput"]["command"].endswith("while True: pass")
        for _, u in printer.updates
    )


def test_after_a_root_stop_the_next_message_is_given_the_earlier_messages_and_answers(
    tmp_path, home, work
):
    async def body():
        async with FakeOpenAI(answering_from_the_recap(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                await client.ask(root, "Which course is lightest?")
                await stop_root_when(client, root, "Spin.", spinning)
                seen, called = len(client.updates_on(root)), len(model.calls)
                await client.ask(root, FIRST_QUESTION)
                notice = client.updates_on(root)[seen]
                _, fresh = run_ids(client.printer.updates)
                return notice, client.run_log(fresh), model.calls[called].messages

    notice, log, first_call = run(body())
    [answer] = [e.answer for e in log if e.kind == "prompt.end"]
    assert answer == "Which course is lightest?"
    assert [m["role"] for m in first_call] == ["system", "user", "user"]
    earlier = [
        Turn(1, "root", "Which course is lightest?", "answered", "STAT101", None),
        Turn(2, "root", "Spin.", "stopped", None, None),
    ]
    assert first_call[1]["content"] == recap_of(earlier, "root").text
    assert first_call[2]["content"] == FIRST_QUESTION
    [root_start] = [e for e in log if e.kind == "agent.start" and e.parent is None]
    assert root_start.task == FIRST_QUESTION
    given = RecapNote(turns=2, left_out=0, shortened=False)
    assert (
        notice["content"]["text"] == texts.fresh_run_notice("stopped", given) + "\n\n"
    )
