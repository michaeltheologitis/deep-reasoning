"""Printer, from hand-written update streams (§8.2)."""

import asyncio

import pytest
from acp.schema import SessionNotification

from deep_reasoning.acp.testing.client import UNSTABLE_UPDATES, Printer, outcome_phrase
from tests.acp import streams as s


async def feed(printer, updates):
    for session, update in updates:
        if update["sessionUpdate"] in UNSTABLE_UPDATES:
            await printer.unstable_update(session, update)
        else:
            model = SessionNotification.model_validate(
                {"sessionId": session, "update": update}
            ).update
            await printer.session_update(session, model)


def printed(updates):
    printer = Printer()
    asyncio.run(feed(printer, updates))
    return printer


def test_updates_are_kept_as_they_were_on_the_wire():
    assert printed(s.native_run()).updates == s.native_run()


def test_commands_are_kept_per_root_session():
    def menu(*names):
        return {
            "sessionUpdate": "available_commands_update",
            "availableCommands": [{"name": n, "description": "d"} for n in names],
        }

    printer = printed(
        [(s.ROOT, menu("a", "b")), (s.OTHER_ROOT, menu("c")), (s.ROOT, menu())]
    )
    assert printer.commands[s.ROOT] == []
    assert [c.name for c in printer.commands[s.OTHER_ROOT]] == ["c"]


def test_subagents_are_keyed_by_full_id_and_hold_their_latest_update():
    printer = printed(s.native_run())
    n2 = printer.subagents[s.N2]
    assert (n2.session_id, n2.parent_session_id) == (s.N2, s.ROOT)
    assert (n2.title, n2.state, n2.stop_reason) == (
        "Summarize the CS department.",
        "idle",
        "end_turn",
    )
    assert n2.field_meta["deep_reasoner"]["status"] == "done"
    asyncio.run(feed(printer, [s.announce(s.ROOT, s.R2, 2, 1, 1, "Again.")]))
    assert printer.subagents[s.N2] == n2
    assert len(printer.subagents) == 3


def test_wait_until_returns_the_first_result_that_is_not_none_or_false():
    async def body():
        printer = Printer()
        waiting = asyncio.create_task(
            printer.wait_until(lambda p: p.commands.get(s.ROOT), timeout=5)
        )
        await asyncio.sleep(0)
        await feed(
            printer,
            [
                (
                    s.ROOT,
                    {
                        "sessionUpdate": "available_commands_update",
                        "availableCommands": [],
                    },
                )
            ],
        )
        arrived = await waiting
        with pytest.raises(TimeoutError):
            await printer.wait_until(lambda p: False, timeout=0.05)
        return arrived

    assert asyncio.run(body()) == []


@pytest.mark.parametrize(
    ("meta", "phrase"),
    [
        (None, "running"),
        ({"status": "done"}, "done"),
        ({"status": "exhausted"}, "exhausted"),
        (
            {"status": "failed", "detail": "ValueError: " + "x" * 50},
            "failed: ValueError: " + "x" * 27 + "…",
        ),
        ({"status": "stopped", "node": 2}, "stopped"),
        ({"status": "stopped", "node": 2, "stopped_by": 2}, "stopped"),
        ({"status": "stopped", "node": 4, "stopped_by": 2}, "stopped by #2"),
        (
            {"status": "stopped", "node": 3, "stopped_by": 2, "collateral": True},
            "stopped with #2",
        ),
        ({"status": "crashed"}, "crashed"),
    ],
)
def test_outcome_phrases(meta, phrase):
    wrapped = None if meta is None else {"deep_reasoner": meta}
    node = None if meta is None else meta.get("node")
    assert outcome_phrase(wrapped, node) == phrase
