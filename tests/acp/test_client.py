"""Printer and its lines, from hand-written update streams (§8.2)."""

import asyncio

import pytest
from acp.schema import SessionNotification

from deep_reasoning.acp import texts
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


def test_each_update_is_one_line_in_the_designs_format():
    assert printed(s.native_run()).lines == [
        "root     tool_call          c1.1 execute  Run found = run_all(...) …",
        "root     subagent_update    n2  'Summarize the CS department.'  running",
        "root     session_message    → n2  'Summarize the CS department.'",
        "root     subagent_update    n3  'Summarize the STAT department.'  running",
        "n2       tool_call          c2.1 execute  Run print(cs)",
        "n2       tool_call_update   c2.1 completed  ['CS101', 'CS102']",
        "n2       usage_update       0.0004 USD",
        "n2       session_message    → root  'CS is heavy.'",
        "n2       usage_update       0.0037 USD",
        "root     subagent_update    n2  idle end_turn",
        "n3       usage_update       cost unknown",
        "root     subagent_update    n3  idle end_turn  (failed: ValueError: the catalog has no STAT sec…)",
        "root     tool_call_update   c1.1 completed  {'CS': 'CS is heavy.'}",
        "root     tool_call          c1.2 execute  Run FinalAnswer('STAT is lighter.')",
        "root     tool_call_update   c1.2 completed  FinalAnswer: 'STAT is lighter.'",
        "root     agent_message      STAT is lighter.",
        "root     usage_update       0.0089 USD",
    ]


def test_updates_are_kept_as_they_were_on_the_wire():
    assert printed(s.native_run()).updates == s.native_run()


def test_messages_are_shown_whole_wrapped_under_their_column():
    printer = printed([s.notice(s.ROOT, texts.FRESH_AFTER_STOP)])
    assert printer.lines == [
        (
            "root     agent_message      Starting a fresh run: the previous one was stopped, so its variables and\n"
            "                            sub-agents are gone."
        )
    ]


def test_menus_options_and_long_fields():
    commands = {
        "sessionUpdate": "available_commands_update",
        "availableCommands": [
            {
                "name": "compare-departments",
                "description": "d",
                "input": {"hint": "the task"},
            }
        ],
    }
    options = {
        "sessionUpdate": "config_option_update",
        "configOptions": [
            {
                "id": "namespace",
                "name": "Namespace",
                "type": "select",
                "currentValue": "advising",
                "options": [{"value": "advising", "name": "advising"}],
            }
        ],
    }
    thought = {
        "sessionUpdate": "agent_thought_chunk",
        "content": s.text(
            "First I identify  the CS\ncourses, then I'll ask a separate sub-agent."
        ),
    }
    lines = printed([(s.ROOT, commands), (s.ROOT, options), (s.N2, thought)]).lines
    assert lines == [
        "root     available_commands_update  ['compare-departments']",
        "root     config_option_update  namespace = advising (fixed)",
        "n2       agent_thought      First I identify the CS courses, then I'll ask a separate s…",
    ]


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


def test_subagents_are_keyed_by_full_id_and_findable_by_an_unambiguous_short_one():
    printer = printed(s.native_run())
    n2 = printer.subagents["n2"]
    assert n2 is printer.subagents[s.N2]
    assert (n2.session_id, n2.short, n2.parent_session_id) == (s.N2, "n2", s.ROOT)
    assert (n2.title, n2.state, n2.stop_reason) == (
        "Summarize the CS department.",
        "idle",
        "end_turn",
    )
    assert n2.field_meta["deep_reasoner"]["status"] == "done"
    asyncio.run(feed(printer, [s.announce(s.ROOT, s.R2, 2, 1, 1, "Again.")]))
    with pytest.raises(KeyError, match=s.R2):
        printer.subagents["n2"]
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


def test_show_prints_what_arrived_since_the_last_show(capsys):
    printer = printed(s.native_run()[:2])
    printer.show()
    assert capsys.readouterr().out.splitlines() == printer.lines
    asyncio.run(feed(printer, s.native_run()[2:3]))
    printer.show()
    assert capsys.readouterr().out.splitlines() == printer.lines[2:]


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
