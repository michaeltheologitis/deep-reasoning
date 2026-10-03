"""The ACP surface end to end: dr-acp spawned over stdio, read by an ACP Python client.

E1 (tree fidelity), session/load replay, session/close, cancel routing.
"""

import asyncio
import json
import signal

import acp
import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.agent import user_text
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.acp.testing.tree import MessageNode, tree
from tests.acp.golden import as_tree, normalized, play, read_golden, streams
from tests.acp.harness import (
    BRIDGE_EXTENSION,
    BRIDGE_SYSTEM_SUFFIX,
    BRIDGE_USER_SUFFIX,
    dr_acp,
    eventually,
    run,
    run_ids,
)
from tests.acp.scenarios import (
    BY_NAME,
    SCENARIOS,
    acp_tree,
    deep_reasoner_tree,
    repl,
    scripted,
)

MODES = pytest.mark.parametrize("native", [True, False], ids=["native", "flat"])


def responses(lines: list[bytes]) -> list[tuple[int, dict]]:
    return [(i, m) for i, m in enumerate(map(json.loads, lines)) if "id" in m]


def assert_wire_order(lines: list[bytes], root: str) -> None:
    """§5.4: a child's announcement names a cell already sent on its parent's session,
    nothing reaches a child's session before its announcement, and every prompt
    response follows a root usage_update."""
    sent_calls: dict[str, set[str]] = {}
    announced: set[str] = set()
    last_root_update = None
    for message in map(json.loads, lines):
        if message.get("method") == "session/update":
            session, update = (
                message["params"]["sessionId"],
                message["params"]["update"],
            )
            kind = update["sessionUpdate"]
            assert session == root or session in announced, (
                f"{kind} before announcement"
            )
            if kind == "tool_call":
                sent_calls.setdefault(session, set()).add(update["toolCallId"])
            if kind == "subagent_update" and update["sessionId"] not in announced:
                parent_call = update["_meta"]["openhands"]["parentToolCallId"]
                assert parent_call in sent_calls.get(session, set())
                announced.add(update["sessionId"])
            if session == root:
                last_root_update = kind
        elif "stopReason" in message.get("result", {}):
            assert last_root_update == "usage_update"


@MODES
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_tree_rebuilt_from_the_stream_is_deep_reasoners_own(scenario, native, tmp_path):
    played = run(play(scenario, native, tmp_path))
    client, root = played.client, played.root
    assert tuple(played.outcomes) == scenario.outcomes
    (run_id,) = run_ids(client.printer.updates)
    rebuilt = tree(client.printer.updates)
    assert acp_tree(rebuilt) == deep_reasoner_tree(tmp_path / "home" / "runs" / run_id)
    if native:
        assert_wire_order(client.lines, root)
    else:
        assert {sid for sid, _ in client.printer.updates} == {root}
        kinds = {u["sessionUpdate"] for _, u in client.printer.updates}
        assert not kinds & {
            "subagent_update",
            "session_message",
            "session_message_chunk",
        }
    if len(acp_tree(rebuilt)) > 1:
        assert [r.mode for r in rebuilt.runs] == ["native" if native else "flat"]


@MODES
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_each_stream_matches_its_golden_recording(scenario, native, tmp_path):
    """Re-record with `uv run python -m tests.acp.golden record`, and review the diff."""
    played = run(play(scenario, native, tmp_path))
    sent = normalized(played.client.lines, tmp_path)
    golden = read_golden(scenario, native)
    assert streams(sent) == streams(golden)
    assert as_tree(sent) == as_tree(golden)


def test_initialize_advertises_load_close_and_http_and_sse_mcp(tmp_path, home):
    config = BY_NAME["linear"].write_config(
        tmp_path / "config", "http://127.0.0.1:9/v1"
    )

    async def body():
        async with dr_acp(config, home) as client:
            pass
        return client

    client = run(body())
    (_, init), *_ = responses(client.lines)
    assert init["result"] == {
        "protocolVersion": 1,
        "agentCapabilities": {
            "loadSession": True,
            "promptCapabilities": {
                "image": False,
                "audio": False,
                "embeddedContext": False,
            },
            "mcpCapabilities": {"http": True, "sse": True},
            "sessionCapabilities": {"close": {}},
        },
        "agentInfo": {"name": "dr-acp", "title": "deep_reasoner", "version": "0.1.0"},
        "authMethods": [],
    }


HANG = repl("import time", "time.sleep(60)")
REPLAY_PLAN = {
    "Summarize two courses.": BY_NAME["fanout2"].plan["Summarize two courses."],
    "Summarize C1.": BY_NAME["fanout2"].plan["Summarize C1."],
    "Summarize C2.": BY_NAME["fanout2"].plan["Summarize C2."],
    "Wait a minute.": [HANG],
    "What next?": [repl("FinalAnswer('next')")],
}


def test_load_replays_every_run_and_marks_a_killed_one_lost(tmp_path, home, work):
    """dr-acp killed mid-run, then session/load on a new one: the replayed tree equals the
    live one (a lost run gains its closing message), the response comes after the whole
    replay, nothing about children follows it, and the next prompt starts fresh."""

    async def body():
        async with FakeOpenAI(scripted(REPLAY_PLAN)) as model:
            config = BY_NAME["fanout2"].write_config(
                tmp_path / "config", model.base_url
            )
            async with dr_acp(config, home) as first:
                root = await first.open_session(work)
                await first.ask(root, "Summarize two courses.")
                hung = asyncio.create_task(first.ask(root, "Wait a minute."))
                await first.printer.wait_until(lambda p: _hung_cells(p, root) == 1)
                await first.conn.cancel(session_id=root)
                assert (await hung).stop_reason == "cancelled"
                await first.ask(root, "What next?")
                lost = asyncio.create_task(first.ask(root, "Wait a minute."))
                await first.printer.wait_until(lambda p: _hung_cells(p, root) == 2)
                first.proc.send_signal(signal.SIGKILL)
                await first.proc.wait()
                with pytest.raises(ConnectionError):
                    await lost
            async with dr_acp(config, home) as second:
                await second.conn.load_session(
                    cwd=str(work), session_id=root, mcp_servers=[]
                )
                replayed = list(second.printer.updates)
                after = await second.ask(root, "What next?")
        return first, second, root, replayed, after

    first, second, _, replayed, after = run(body())
    live = tree(first.printer.updates)
    again = tree(replayed)
    assert len(again.runs) == 2
    assert again.runs[0] == live.runs[0]
    lost = again.runs[1]
    assert lost.root.items[-1] == MessageNode(
        outcome="lost", prompt=2, text=texts.REPLAY_LOST
    )
    lost.root.items.pop()
    assert lost == live.runs[1]
    user_texts = [
        u["content"]["text"]
        for _, u in replayed
        if u["sessionUpdate"] == "user_message_chunk"
    ]
    assert user_texts == [
        "Summarize two courses.",
        "Wait a minute.",
        "What next?",
        "Wait a minute.",
    ]
    load_at = next(
        i for i, m in responses(second.lines) if "configOptions" in m["result"]
    )
    later = [json.loads(line) for line in second.lines[load_at + 1 :]]
    assert not any(
        m.get("params", {}).get("update", {}).get("sessionUpdate") == "subagent_update"
        for m in later
    )
    assert after.field_meta["deep_reasoner"]["outcome"] == "answered"
    _, notice = second.printer.updates[len(replayed)]
    assert notice["content"]["text"] == texts.FRESH_AFTER_RESTART + "\n\n"


def _hung_cells(printer, root: str) -> int:
    """How many of the root's cells are the hanging one."""
    return sum(
        u["sessionUpdate"] == "tool_call"
        and u["rawInput"]["command"].endswith("time.sleep(60)")
        for sid, u in printer.updates
        if sid == root
    )


def test_load_of_an_unknown_session_is_invalid_params_naming_it(tmp_path, home, work):
    config = BY_NAME["linear"].write_config(
        tmp_path / "config", "http://127.0.0.1:9/v1"
    )

    async def body():
        async with dr_acp(config, home) as client:
            with pytest.raises(Exception) as caught:
                await client.conn.load_session(
                    cwd=str(work), session_id="s-0000", mcp_servers=[]
                )
        return caught.value

    error = run(body())
    assert (error.code, str(error)) == (-32602, texts.unknown_session("s-0000"))
    assert error.data == {"deep_reasoner": {"error": "UNKNOWN_SESSION"}}


def test_close_ends_the_live_run_closed_and_load_then_starts_fresh(
    tmp_path, home, work
):
    plan = {
        "Count to three.": [repl("FinalAnswer(3)")],
        "And again.": [repl("FinalAnswer(4)")],
    }

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                await client.ask(root, "Count to three.")
                await client.conn.close_session(session_id=root)
                (run_id,) = run_ids(client.printer.updates)
                ended = client.run_log(run_id)[-1]
                await client.conn.load_session(
                    cwd=str(work), session_id=root, mcp_servers=[]
                )
                seen = len(client.printer.updates)
                await client.ask(root, "And again.")
                notice = client.printer.updates[seen][1]
        return ended, notice

    ended, notice = run(body())
    assert (ended.kind, ended.reason) == ("run.end", "closed")
    assert notice["content"]["text"] == texts.FRESH_AFTER_CLOSE + "\n\n"


def test_cancel_with_an_unknown_id_is_ignored_and_logged(tmp_path, home, work):
    config = BY_NAME["linear"].write_config(
        tmp_path / "config", "http://127.0.0.1:9/v1"
    )

    async def body():
        async with dr_acp(config, home) as client:
            await client.open_session(work)
            await client.conn.cancel(session_id="n3")
            await eventually(
                lambda: (
                    "session/cancel for unknown session 'n3' ignored"
                    in client.stderr_text()
                )
            )

    run(body())


def test_unknown_unstable_methods_answer_method_not_found(tmp_path, home, work):
    config = BY_NAME["linear"].write_config(
        tmp_path / "config", "http://127.0.0.1:9/v1"
    )

    async def body():
        async with dr_acp(config, home) as client:
            root = await client.open_session(work)
            with pytest.raises(Exception) as caught:
                await client.conn.fork_session(session_id=root, cwd=str(work))
        return caught.value

    assert run(body()).code == -32601


def test_the_task_is_the_users_own_text_and_not_what_openhands_appends():
    """The bridge's layout: the user's text, their images, the turn's extensions, and on
    the first prompt its system suffix."""
    blocks = [
        acp.text_block("Which department is lighter?"),
        acp.image_block(data="aGk=", mime_type="image/png"),
        acp.text_block(BRIDGE_EXTENSION),
        acp.text_block(BRIDGE_USER_SUFFIX),
        acp.text_block(BRIDGE_SYSTEM_SUFFIX),
    ]
    assert user_text(blocks) == (
        "Which department is lighter?",
        [BRIDGE_EXTENSION, BRIDGE_USER_SUFFIX, BRIDGE_SYSTEM_SUFFIX],
    )


def test_resource_links_join_the_users_text_on_lines_of_their_own():
    blocks = [
        acp.text_block("Summarize these."),
        acp.resource_link_block(name="cv", uri="file:///cv.pdf"),
        acp.text_block(BRIDGE_SYSTEM_SUFFIX),
        acp.resource_link_block(name="notes", uri="file:///notes.md"),
    ]
    assert user_text(blocks) == (
        "Summarize these.\nfile:///cv.pdf\nfile:///notes.md",
        [BRIDGE_SYSTEM_SUFFIX],
    )
