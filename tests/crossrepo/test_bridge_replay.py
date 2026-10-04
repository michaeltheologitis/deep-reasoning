"""E5's second half: each of D1's native recordings, replayed by S1's scripted agent into
the SDK fork's agent-server, is stored as the same tree D1's tree() reads from the
recording (D5 §7.5, S1 §5.1 guarantee 2)."""

import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

from deep_reasoning.acp.testing.tree import AgentNode, CellNode, Tree
from tests.acp.golden import GOLDEN, as_tree, read_golden
from tests.acp.scenarios import BY_NAME
from tests.crossrepo.agent_server import agent_server, sdk_checkout

RECORDINGS = sorted(
    p.name.removesuffix(".native.jsonl") for p in GOLDEN.glob("*.native.jsonl")
)
SETTLE_S = 1.0  # stored events count unchanged this long: the replay has landed
TIMEOUT_S = 120.0

# One session's place in the tree: its parent session (None: the root), the cell that
# spawned it (None for the root), and its own cells in order.
Node = tuple[str | None, str | None, tuple[str, ...]]
Shape = dict[str | None, Node]


def recorded_shape(tree: Tree) -> Shape:
    """D1's tree as sessions: the root is None, as the bridge stores it."""
    shape: Shape = {}
    cells: dict[str | None, list[str]] = {}

    def visit(agent: AgentNode, session: str | None) -> None:
        for item in agent.items:
            if not isinstance(item, CellNode):
                continue
            cells.setdefault(session, []).append(item.tool_call_id)
            for child in item.agents:
                shape[child.session_id] = (session, item.tool_call_id, ())
                visit(child, child.session_id)

    for run in tree.runs:
        visit(run.root, None)
    shape.setdefault(None, (None, None, ()))
    return {
        session: (parent, spawning, tuple(dict.fromkeys(cells.get(session, []))))
        for session, (parent, spawning, _) in shape.items()
    }


def stored_shape(events: Iterable[Mapping[str, Any]]) -> Shape:
    """The tree the stored events describe, read by S1's persisted contract: the latest
    ACPSubagentEvent per child, and each session's ACPToolCallEvents."""
    latest: dict[str, Mapping[str, Any]] = {}
    cells: dict[str | None, list[str]] = {}
    for event in events:
        if event["kind"] == "ACPSubagentEvent":
            latest[event["acp_session_id"]] = event
        elif event["kind"] == "ACPToolCallEvent":
            cells.setdefault(event.get("acp_session_id"), []).append(
                event["tool_call_id"]
            )
    shape: Shape = {None: (None, None, tuple(dict.fromkeys(cells.get(None, []))))}
    for child, snapshot in latest.items():
        shape[child] = (
            snapshot.get("parent_session_id"),
            snapshot.get("parent_tool_call_id"),
            tuple(dict.fromkeys(cells.get(child, []))),
        )
    return shape


def stored_events(server, conversation: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    page = None
    while True:
        query = "?limit=100" + (f"&page_id={page}" if page else "")
        found = server.request(
            "GET", f"/api/conversations/{conversation}/events/search{query}"
        )
        events += found["items"]
        page = found.get("next_page_id")
        if not page:
            return events


def replay(server, recording: Path, prompts: Iterable[str], work: Path) -> list[Any]:
    """One conversation whose ACP agent plays the recording; one message per recorded
    prompt; the events once they have settled."""
    agent = {
        "kind": "ACPAgent",
        "acp_command": [
            server.python,
            str(server.checkout / "tests" / "fixtures" / "acp" / "scripted_agent.py"),
            "--transcript",
            str(recording),
        ],
        "acp_subagents": True,
    }
    work.mkdir()
    conversation = server.request(
        "POST",
        "/api/conversations",
        {
            "agent": agent,
            "workspace": {"kind": "LocalWorkspace", "working_dir": str(work)},
        },
    )["id"]
    deadline = time.monotonic() + TIMEOUT_S
    for text in prompts:
        server.request(
            "POST",
            f"/api/conversations/{conversation}/events",
            {"role": "user", "content": [{"type": "text", "text": text}], "run": True},
        )
        time.sleep(0.2)
        while (
            status := server.request("GET", f"/api/conversations/{conversation}")[
                "execution_status"
            ]
        ) not in ("finished", "error", "stuck"):
            assert time.monotonic() < deadline, f"still {status}"
            time.sleep(0.1)
        assert status == "finished", status
    events, settled_at = stored_events(server, conversation), time.monotonic()
    while time.monotonic() - settled_at < SETTLE_S:
        time.sleep(0.2)
        again = stored_events(server, conversation)
        if len(again) != len(events):
            events, settled_at = again, time.monotonic()
    return events


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    with agent_server(
        sdk_checkout(), tmp_path_factory.mktemp("agent-server")
    ) as running:
        yield running


def test_the_recorded_shape_places_every_child_under_its_cell():
    shape = recorded_shape(as_tree(read_golden(BY_NAME["depth3"], native=True)))
    run = "00000000-000000-000000"
    assert shape == {
        None: (None, None, (f"{run}-n1-c1", f"{run}-n1-c2")),
        f"{run}-n2": (None, f"{run}-n1-c1", (f"{run}-n2-c1", f"{run}-n2-c2")),
        f"{run}-n3": (f"{run}-n2", f"{run}-n2-c1", (f"{run}-n3-c1",)),
    }
    assert len(RECORDINGS) == 10


@pytest.mark.crossrepo
@pytest.mark.parametrize("name", RECORDINGS)
def test_each_native_recording_is_stored_as_the_tree_it_records(server, tmp_path, name):
    scenario = BY_NAME[name]
    recording = GOLDEN / f"{name}.native.jsonl"
    events = replay(server, recording, scenario.prompts, tmp_path / "work")
    assert stored_shape(events) == recorded_shape(
        as_tree(read_golden(scenario, native=True))
    )
