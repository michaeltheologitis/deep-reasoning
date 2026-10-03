"""The connection: the initialize tap, the single send path, and shutdown (§4.2)."""

import asyncio
import signal
import time
from importlib.metadata import version

import pytest
from acp._transport import memory_transport_pair
from acp.connection import Connection

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.acp.wire import ClientMode, Outbox
from tests.acp.harness import close_stdin, dr_acp, run, run_ids
from tests.acp.scenarios import BY_NAME, repl, scripted


def test_installed_acp_is_the_pinned_0_12_1():
    assert version("agent-client-protocol") == "0.12.1"


@pytest.mark.parametrize(
    ("params", "flat", "mode"),
    [
        ({"clientCapabilities": {"subagents": {}}}, False, "native"),
        ({"clientCapabilities": {"subagents": {"cancel": {}}}}, False, "native"),
        ({"clientCapabilities": {"subagents": {}}}, True, "flat"),
        ({"clientCapabilities": {"subagents": None}}, False, "flat"),
        ({"clientCapabilities": {"subagents": True}}, False, "flat"),
        ({"clientCapabilities": {}}, False, "flat"),
        ({}, False, "flat"),
    ],
)
def test_native_mode_needs_a_subagents_object_and_no_flat_flag(params, flat, mode):
    client = ClientMode(flat=flat)
    client.decide({"protocolVersion": 1, **params})
    assert client.mode == mode


def test_outbox_sends_raw_updates_in_order_and_drops_them_once_the_client_is_gone():
    async def body():
        ours, theirs = memory_transport_pair()
        conn = Connection(lambda *a: None, ours)
        outbox = Outbox(conn)
        await outbox.update(
            "s-1", {"sessionUpdate": "subagent_update", "sessionId": "r-n2"}
        )
        await outbox.update("s-1", {"sessionUpdate": "agent_message_chunk"})
        quiet = outbox.seconds_since_last_send
        received = [await theirs.receive(), await theirs.receive()]
        await conn.close()
        await outbox.update("s-1", {"sessionUpdate": "agent_message_chunk"})
        return received, quiet

    received, quiet = run(body())
    assert [m["params"] for m in received] == [
        {
            "sessionId": "s-1",
            "update": {"sessionUpdate": "subagent_update", "sessionId": "r-n2"},
        },
        {"sessionId": "s-1", "update": {"sessionUpdate": "agent_message_chunk"}},
    ]
    assert quiet < 1.0


def test_the_flat_flag_wins_over_a_client_that_advertises_subagents(
    tmp_path, home, work
):
    scenario = BY_NAME["fanout2"]

    async def body():
        async with FakeOpenAI(scenario.responder()) as model:
            config = scenario.write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home, args=("--flat",)) as client:
                root = await client.open_session(work)
                await client.ask(root, scenario.prompts[0])
                return client, root

    client, root = run(body())
    assert {sid for sid, _ in client.printer.updates} == {root}
    cards = [u for _, u in client.printer.updates if u.get("kind") == "other"]
    assert len(cards) == 2


HANG = {"Wait.": [repl("import time", "time.sleep(60)")]}


@pytest.mark.parametrize("how", ["stdin closed", "SIGTERM"])
def test_shutdown_closes_a_live_run_within_1_4_seconds_and_exits_0(
    how, tmp_path, home, work
):
    async def body():
        async with FakeOpenAI(scripted(HANG)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                asyncio.create_task(client.ask(root, "Wait."))
                await client.printer.wait_until(
                    lambda p: any(
                        u["sessionUpdate"] == "tool_call" for _, u in p.updates
                    )
                )
                asked = time.time()
                if how == "SIGTERM":
                    client.proc.send_signal(signal.SIGTERM)
                else:
                    await close_stdin(client.proc)
                code = await asyncio.wait_for(client.proc.wait(), 5)
                (run_id,) = run_ids(client.printer.updates)
                return asked, code, client.run_log(run_id)[-1]

    asked, code, ended = run(body())
    assert code == 0
    assert (ended.kind, ended.reason) == ("run.end", "closed")
    assert ended.t - asked < 1.4
