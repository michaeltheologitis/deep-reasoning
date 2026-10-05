"""C1's two DOM reads of the sub-agent tree, in Python for E12 (D5 §7.5, C1 A.9): the same
in-page scripts as the Canvas fork's tests/e2e/mock-llm/utils/acp-subagents.ts, against
SUB-011's test ids; and the same tree read from a run's log."""

import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from deep_reasoning.acp.encoder import Encoder
from deep_reasoning.acp.runlog import Home, RunLog
from deep_reasoning.acp.testing.tree import AgentNode, CellNode, tree

# One sub-agent as the chat nests it: C1's SubagentLink.
Link = dict[str, Any]

COLLAPSED_TOGGLES = (
    '[data-testid="subagent-block-toggle"][aria-expanded="false"], '
    '[data-testid="subagent-row-toggle"][aria-expanded="false"]'
)
EXPAND_S = 30.0

CLICK_COLLAPSED = """(selector) => {
    const collapsed = [...document.querySelectorAll(selector)];
    collapsed.forEach((toggle) => toggle.click());
    return collapsed.length;
}"""

READ_RENDERED = """() => {
    const ROW = '[data-testid="subagent-row"]';
    const CELL = '[data-testid="acp-tool-call"]';
    const UNPLACED = '[data-testid="subagent-unplaced"]';
    const nearest = (element, selector) =>
        element.parentElement?.closest(selector) ?? null;
    const rows = [...document.querySelectorAll(ROW)];
    const cells = [...document.querySelectorAll(CELL)];
    return rows.map((row) => {
        const parentRow = nearest(row, ROW);
        const cell = nearest(row, CELL);
        const inParent = cell && (!parentRow || parentRow.contains(cell));
        return {
            sessionId: row.getAttribute("data-acp-session-id") ?? "",
            parentSessionId: parentRow
                ? parentRow.getAttribute("data-acp-session-id")
                : (nearest(row, UNPLACED)?.getAttribute(
                      "data-missing-parent-session-id") ?? null),
            parentToolCallId: inParent
                ? cell.getAttribute("data-acp-tool-call-id") : null,
            toolCallIds: cells
                .filter((candidate) => nearest(candidate, ROW) === row)
                .map((candidate) => candidate.getAttribute("data-acp-tool-call-id"))
                .filter((id) => id !== null)
                .sort(),
        };
    });
}"""


def expand_all_subagents(page: Page) -> None:
    """C1's expandAllSubagents: click every collapsed block and row until none is left."""
    deadline = time.monotonic() + EXPAND_S
    while page.evaluate(CLICK_COLLAPSED, COLLAPSED_TOGGLES):
        assert time.monotonic() < deadline, "sub-agents kept collapsing"
        page.wait_for_timeout(200)


def read_rendered_subagent_tree(page: Page) -> list[Link]:
    """C1's readRenderedSubagentTree: the tree as the DOM nests it, by session."""
    return sorted(page.evaluate(READ_RENDERED), key=lambda link: link["sessionId"])


def recorded_subagent_tree(
    home: Path, run_id: str
) -> tuple[list[Link], dict[str, float | None]]:
    """The same tree from the run's log, as session/load replays it, with each
    sub-agent's cost when it ended (the latest it reported)."""
    encoder = Encoder(root="root", run=run_id, mode="native", replay=True)
    updates = [u for ev in RunLog.read(Home(home), run_id) for u in encoder.feed(ev)]
    [run] = tree(updates).runs
    links: list[Link] = []
    costs: dict[str, float | None] = {}

    def visit(agent: AgentNode, parent: str | None) -> None:
        cells = [item for item in agent.items if isinstance(item, CellNode)]
        for cell in cells:
            for child in cell.agents:
                own = [i.tool_call_id for i in child.items if isinstance(i, CellNode)]
                links.append(
                    {
                        "sessionId": child.session_id,
                        "parentSessionId": parent,
                        "parentToolCallId": cell.tool_call_id,
                        "toolCallIds": sorted(set(own)),
                    }
                )
                costs[child.session_id] = child.cost_usd
                visit(child, child.session_id)

    visit(run.root, None)
    return sorted(links, key=lambda link: link["sessionId"]), costs


def subagent_cost(amount: float) -> str:
    """C1's formatSubagentCost for USD: four decimals."""
    return f"${amount:.4f}"
