"""One conversation: its menu, its namespace, how a prompt is parsed, and how a run that
could not start or failed is answered (E11, §4.2)."""

import asyncio

import acp
import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from tests.acp.harness import (
    BRIDGE_EXTENSION,
    BRIDGE_SYSTEM_SUFFIX,
    BRIDGE_USER_SUFFIX,
    dr_acp,
    run,
    run_ids,
    scripted_env,
    write_config,
)
from tests.acp.scenarios import BASE_CONFIG, repl, scripted

PROGRAM = repl("FinalAnswer(task.upper())")


def decomposition(name: str) -> dict:
    """A program over `task`, the REPL name a main decomposition binds. Its user turn is
    literal: deep_reasoner renders a namespace's decompositions into every agent's
    prompt, where a {{ task }} would be undefined."""
    return {
        "name": name,
        "messages": [
            {"role": "user", "content": "Shout the task."},
            {"role": "assistant", "content": PROGRAM},
        ],
    }


def menu_config(tmp_path, base_url="http://127.0.0.1:9/v1", **over):
    config = {
        **BASE_CONFIG,
        "client": {**BASE_CONFIG["client"], "base_url": base_url},
        "entry_namespace": "router",
        "decompositions": [decomposition("triage")],
        "namespaces": {
            "router": {"decompositions": [decomposition("summarize then rank")]},
            "advising": {"decompositions": [decomposition("compare departments")]},
        },
        **over,
    }
    return write_config(tmp_path / "config" / "main.yaml", config)


def names(printer, root):
    return [c.name for c in printer.commands[root]]


def kinds(updates):
    return [u["sessionUpdate"] for u in updates]


def test_menu_follows_the_namespace_and_the_first_prompt_fixes_both(
    tmp_path, home, work
):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            first_menu = names(client.printer, root)
            first_raw = client.updates_on(root)[-1]
            options = await client.conn.set_config_option(
                config_id="namespace", session_id=root, value="advising"
            )
            second_menu = names(client.printer, root)
            seen = len(client.updates_on(root))
            response = await client.ask(root, "/compare-departments which is lighter")
            after = client.updates_on(root)[seen:]
            (run_id,) = run_ids(client.printer.updates)
            start = client.run_log(run_id)[0]
        return first_menu, first_raw, options, second_menu, response, after, start

    first_menu, first_raw, options, second_menu, response, after, start = run(body())
    assert first_menu == ["triage", "summarize-then-rank"]
    assert first_raw["availableCommands"][1] == {
        "name": "summarize-then-rank",
        "description": "Open with the 'summarize then rank' decomposition",
        "input": {"hint": "the task"},
        "_meta": {
            "deep_reasoner": {
                "decomposition": "summarize then rank",
                "namespace": "router",
            }
        },
    }
    assert second_menu == ["triage", "compare-departments"]
    (option,) = options.config_options
    assert option.current_value == "advising"
    assert [o.value for o in option.options] == ["root", "advising", "router"]
    assert kinds(after[:2]) == ["available_commands_update", "config_option_update"]
    assert after[0]["availableCommands"] == []
    (narrowed,) = after[1]["configOptions"]
    assert narrowed["options"] == [{"value": "advising", "name": "advising"}]
    assert narrowed["description"] == texts.NAMESPACE_FIXED_NOTE
    assert after[-2]["content"]["text"] == "WHICH IS LIGHTER"
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    assert (start.namespace, start.decomposition) == ("advising", "compare departments")


def test_a_decomposition_after_the_first_message_is_answered_and_nothing_runs(
    tmp_path, home, work
):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            await client.ask(root, "/triage first")
            (run_id,) = run_ids(client.printer.updates)
            logged = len(client.run_log(run_id))
            seen = len(client.updates_on(root))
            response = await client.ask(root, "/triage again")
            after = client.updates_on(root)[seen:]
            assert len(client.run_log(run_id)) == logged
        return response, after

    response, after = run(body())
    assert kinds(after) == ["agent_message_chunk", "usage_update"]
    assert after[0]["content"]["text"] == texts.late_decomposition("triage")
    assert after[0]["_meta"] == {
        "deep_reasoner": {"run": None, "prompt": None, "outcome": "rejected"}
    }
    assert response.stop_reason == "end_turn"
    assert response.field_meta == {
        "deep_reasoner": {"run": None, "outcome": "rejected"}
    }


def test_a_command_without_a_task_is_rejected_and_the_session_stays_open(
    tmp_path, home, work
):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            response = await client.ask(root, "/triage")
            reply = client.updates_on(root)[-2]
            await client.conn.set_config_option(
                config_id="namespace", session_id=root, value="advising"
            )
        return response, reply

    response, reply = run(body())
    assert reply["content"]["text"] == texts.command_needs_task("triage", "the task")
    assert response.field_meta["deep_reasoner"]["outcome"] == "rejected"


@pytest.mark.parametrize(
    ("config_id", "value", "error", "message"),
    [
        (
            "namespace",
            "nowhere",
            "UNKNOWN_NAMESPACE",
            texts.unknown_namespace("nowhere", ["root", "advising", "router"]),
        ),
        ("model", "big", "UNKNOWN_OPTION", texts.unknown_option("model")),
    ],
)
def test_a_bad_option_is_refused_with_its_sentence(
    config_id, value, error, message, tmp_path, home, work
):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            with pytest.raises(acp.RequestError) as caught:
                await client.conn.set_config_option(
                    config_id=config_id, session_id=root, value=value
                )
        return caught.value

    refused = run(body())
    assert (refused.code, str(refused)) == (-32602, message)
    assert refused.data == {"deep_reasoner": {"error": error}}


def test_the_namespace_is_fixed_once_the_conversation_started(tmp_path, home, work):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            await client.ask(root, "/triage first")
            same = await client.conn.set_config_option(
                config_id="namespace", session_id=root, value="router"
            )
            with pytest.raises(acp.RequestError) as caught:
                await client.conn.set_config_option(
                    config_id="namespace", session_id=root, value="advising"
                )
        return same, caught.value

    same, refused = run(body())
    assert [o.value for o in same.config_options[0].options] == ["router"]
    assert (refused.code, str(refused)) == (-32602, texts.namespace_fixed("router"))
    assert refused.data == {"deep_reasoner": {"error": "NAMESPACE_FIXED"}}


def test_a_path_is_a_task_and_a_resource_link_joins_it(tmp_path, home, work):
    plan = {"/home/user/notes": [repl("FinalAnswer(task)")]}

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            config = menu_config(tmp_path, model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                await client.conn.prompt(
                    session_id=root,
                    prompt=[
                        acp.text_block("/home/user/notes is a path"),
                        acp.resource_link_block(name="cv", uri="file:///cv.pdf"),
                    ],
                )
                (run_id,) = run_ids(client.printer.updates)
                return client.run_log(run_id)

    prompt = next(e for e in run(body()) if e.kind == "prompt.start")
    assert prompt.text == "/home/user/notes is a path\nfile:///cv.pdf"
    assert (prompt.task, prompt.decomposition) == (prompt.text, None)


def test_a_second_prompt_while_one_runs_is_refused_as_busy(tmp_path, home, work):
    plan = {"Wait.": [repl("import time", "time.sleep(60)")]}

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            config = menu_config(tmp_path, model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                waiting = asyncio.create_task(client.ask(root, "Wait."))
                await client.printer.wait_until(
                    lambda p: any(
                        u["sessionUpdate"] == "tool_call" for _, u in p.updates
                    )
                )
                with pytest.raises(acp.RequestError) as caught:
                    await client.ask(root, "Hello?")
                await client.conn.cancel(session_id=root)
                await waiting
        return caught.value

    refused = run(body())
    assert (refused.code, str(refused)) == (-32600, texts.PROMPT_BUSY)
    assert refused.data == {"deep_reasoner": {"error": "PROMPT_BUSY"}}


def test_a_missing_key_fails_the_build_names_the_variable_and_leaves_no_notice(
    tmp_path, home, work
):
    config = menu_config(
        tmp_path,
        client={
            "base_url": "https://models.example.invalid/v1",
            "api_key_env": "DR_ACP_TEST_ABSENT_KEY",
        },
    )

    async def body():
        async with dr_acp(config, home, env=scripted_env()) as client:
            root = await client.open_session(work)
            first = await client.ask(root, "Hello.")
            seen = len(client.updates_on(root))
            second = await client.ask(root, "Hello again.")
            next_update = client.updates_on(root)[seen]
            run_id = first.field_meta["deep_reasoner"]["run"]
            return (
                client.updates_on(root),
                first,
                second,
                next_update,
                client.run_log(run_id),
            )

    updates, first, second, next_update, log = run(body())
    detail = "ValueError: Missing API key. Set `DR_ACP_TEST_ABSENT_KEY` (preferred) or `OPENAI_API_KEY`."
    closing = next(u for u in updates if u["sessionUpdate"] == "agent_message_chunk")
    assert closing["content"]["text"] == texts.build_failed(detail)
    assert first.field_meta["deep_reasoner"]["outcome"] == "build_failed"
    assert first.field_meta["deep_reasoner"]["run"] is not None
    assert (log[-1].kind, log[-1].reason) == ("run.end", "build_failed")
    assert next_update["content"]["text"] == texts.build_failed(detail)
    assert second.field_meta["deep_reasoner"]["outcome"] == "build_failed"


def test_a_failed_drive_ends_the_run_and_the_next_prompt_says_so(tmp_path, home, work):
    plan = {"Fail.": [repl("FinalAnswer(1)")], "Again.": [repl("FinalAnswer(2)")]}
    responder = scripted(plan, failing=frozenset({("Fail.", 0)}))

    async def body():
        async with FakeOpenAI(responder) as model:
            config = menu_config(tmp_path, model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                failed = await client.ask(root, "Fail.")
                closing = client.updates_on(root)[-2]
                seen = len(client.updates_on(root))
                answered = await client.ask(root, "Again.")
                notice = client.updates_on(root)[seen]
                log = client.run_log(failed.field_meta["deep_reasoner"]["run"])
        return failed, closing, answered, notice, log

    failed, closing, answered, notice, log = run(body())
    assert (failed.stop_reason, failed.field_meta["deep_reasoner"]["outcome"]) == (
        "end_turn",
        "failed",
    )
    assert closing["content"]["text"].startswith("The run failed: InternalServerError")
    assert closing["_meta"]["deep_reasoner"]["outcome"] == "failed"
    assert (log[-1].kind, log[-1].reason) == ("run.end", "failed")
    assert notice["content"]["text"] == texts.FRESH_AFTER_ERROR + "\n\n"
    assert answered.field_meta["deep_reasoner"]["outcome"] == "answered"


def test_a_config_that_cannot_be_materialized_answers_build_failed_without_a_run(
    tmp_path, home, work
):
    config = menu_config(tmp_path)

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            config.unlink()
            response = await client.ask(root, "Hello.")
            return response, client.updates_on(root)[-2]

    response, closing = run(body())
    assert response.field_meta == {
        "deep_reasoner": {"run": None, "outcome": "build_failed"}
    }
    assert closing["content"]["text"].startswith(
        "Could not start the run: FileNotFoundError"
    )
    assert closing["_meta"]["deep_reasoner"] == {
        "run": None,
        "prompt": None,
        "outcome": "build_failed",
    }


def test_what_openhands_appends_to_a_prompt_never_reaches_the_task_and_is_logged(
    tmp_path, home, work
):
    plan = {"Count to three.": [repl("FinalAnswer(3)")]}
    appended = [BRIDGE_EXTENSION, BRIDGE_USER_SUFFIX, BRIDGE_SYSTEM_SUFFIX]

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            config = menu_config(tmp_path, model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                blocks = [acp.text_block(t) for t in ["Count to three.", *appended]]
                response = await client.conn.prompt(session_id=root, prompt=blocks)
                (run_id,) = run_ids(client.printer.updates)
                return response, client.run_log(run_id), model.calls

    response, log, calls = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    prompt = next(e for e in log if e.kind == "prompt.start")
    assert (prompt.text, prompt.task, prompt.dropped) == (
        "Count to three.",
        "Count to three.",
        appended,
    )
    sent_to_the_model = " ".join(str(m["content"]) for c in calls for m in c.messages)
    for text in appended:
        assert text not in sent_to_the_model
