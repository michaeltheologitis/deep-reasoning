"""The run tree rebuilt from a client's updates alone (§8.2)."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from deep_reasoning.acp import ids
from deep_reasoning.acp.runlog import Mode
from deep_reasoning.acp.testing.client import (
    field as one_line,
)
from deep_reasoning.acp.testing.client import (
    first_text,
    outcome_phrase,
)

OUTPUT = 40
_RUN = re.compile(rf"({ids.RUN_ID})-")
_CARD = re.compile(rf"({ids.RUN_ID})-n(\d+)-a\d+")


@dataclass
class CellNode:
    tool_call_id: str
    short: str  # "c2.1"
    title: str
    status: str  # the latest: "in_progress", "completed" or "failed"
    output: str  # the latest content text; "" before any
    agents: list["AgentNode"] = field(default_factory=list)


@dataclass
class MessageNode:
    outcome: str  # the closing message's _meta.deep_reasoner.outcome
    prompt: int | None
    text: str


@dataclass
class AgentNode:
    session_id: str  # the child's session; the root session for the root
    short: str  # "n2"; "root" for the root
    node: int | None  # _meta.deep_reasoner.node
    drive: int
    title: str  # the announcement's title; "" for the root
    outcome: str | None  # the outcome phrase; None for the root
    cost_usd: float | None  # the session's cost when this drive ended; None if unknown
    items: list[CellNode | MessageNode] = field(default_factory=list)


@dataclass
class RunNode:
    root_session_id: str
    run: str
    mode: Mode  # "flat" when this run's sub-agents came as cards
    root: AgentNode
    cost_usd: float | None  # the root's at the run's end: all runs so far


def _cost(usd: float | None) -> str:
    return f"{usd:.4f} USD"


def _label(item: CellNode | MessageNode | AgentNode) -> str:
    if isinstance(item, MessageNode):
        return f"{item.outcome}  {one_line(item.text)}"
    if isinstance(item, CellNode):
        output = one_line(item.output, OUTPUT, output=True)
        return f"{item.short}  {one_line(item.title)}  {item.status}" + (
            f" → {output}" if output else ""
        )
    drive = f" (drive {item.drive})" if item.drive > 1 else ""
    cost = f" · {_cost(item.cost_usd)}" if item.cost_usd is not None else ""
    return f"{item.short}{drive}  {one_line(item.title)}  {item.outcome}{cost}"


def _draw(lines: list[str], items: list[Any], prefix: str) -> None:
    for i, item in enumerate(items):
        last = i == len(items) - 1
        lines.append(prefix + ("└─ " if last else "├─ ") + _label(item))
        below = (
            item.agents if isinstance(item, CellNode) else getattr(item, "items", [])
        )
        _draw(lines, below, prefix + ("   " if last else "│  "))


@dataclass
class Tree:
    runs: list[RunNode]  # in order of each run's first update

    def __str__(self) -> str:
        blocks = []
        for run in self.runs:
            cost = _cost(run.cost_usd) if run.cost_usd is not None else "cost unknown"
            lines = [f"root {run.root_session_id} · run {run.run} · {cost}"]
            _draw(lines, run.root.items, "")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)


def _run_of(update: Mapping[str, Any]) -> str | None:
    """The run an update names: in its _meta, or in the id it carries; None for none."""
    meta = (update.get("_meta") or {}).get("deep_reasoner") or {}
    if "run" in meta:
        return meta["run"]
    for key in ("toolCallId", "sessionId", "messageId"):
        match = _RUN.match(str(update.get(key, "")))
        if match:
            return match.group(1)
    return None


def _amount(update: Mapping[str, Any]) -> float | None:
    cost = update.get("cost")
    return cost["amount"] if cost else None


class _Rebuild:
    """One pass over the updates, in arrival order."""

    def __init__(self, updates: list[tuple[str, Mapping[str, Any]]]) -> None:
        self.announced = {
            u["sessionId"]
            for _, u in updates
            if u.get("sessionUpdate") == "subagent_update"
        }
        self.runs: dict[str, RunNode] = {}
        self.cells: dict[str, CellNode] = {}
        self.drives: dict[str, AgentNode] = {}  # a child's session -> its latest drive
        self.cards: dict[str, AgentNode] = {}
        self.current_run: dict[str, str] = {}  # root session -> its latest run
        self.last_cost: dict[str, float | None] = {}
        for session, update in updates:
            self.take(session, update)

    def run_node(self, root: str, run: str) -> RunNode:
        if run not in self.runs:
            agent = AgentNode(root, "root", None, 1, "", None, None)
            self.runs[run] = RunNode(root, run, "native", agent, None)
        return self.runs[run]

    def take(self, session: str, update: Mapping[str, Any]) -> None:
        kind = update.get("sessionUpdate")
        if kind == "subagent_update":
            self.subagent(update)
        elif kind == "tool_call_update":
            self.call_update(update)
        elif session in self.announced:
            self.child_update(session, kind, update)
        elif kind == "usage_update":
            if session in self.current_run:
                self.runs[self.current_run[session]].cost_usd = _amount(update)
        elif (run := _run_of(update)) is not None:
            self.current_run[session] = run
            self.root_update(self.run_node(session, run), kind, update)

    def cell(self, update: Mapping[str, Any]) -> CellNode:
        call = update["toolCallId"]
        cell = CellNode(
            call, ids.short(call), update.get("title", ""), update.get("status", ""), ""
        )
        self.cells[call] = cell
        return cell

    def call_update(self, update: Mapping[str, Any]) -> None:
        call = update["toolCallId"]
        if call in self.cards:
            agent = self.cards[call]
            agent.outcome = outcome_phrase(update.get("_meta"), agent.node)
            return
        cell = self.cells.get(call)
        if cell is None:
            return
        cell.status = update.get("status", cell.status)
        cell.title = update.get("title", cell.title)
        if update.get("content"):
            cell.output = first_text(update["content"])

    def child_update(self, session: str, kind: str, update: Mapping[str, Any]) -> None:
        if kind == "tool_call" and session in self.drives:
            self.drives[session].items.append(self.cell(update))
        elif kind == "usage_update":
            self.last_cost[session] = _amount(update)

    def subagent(self, update: Mapping[str, Any]) -> None:
        child = update["sessionId"]
        meta = update.get("_meta") or {}
        state = (update.get("state") or {}).get("state")
        if state == "idle" and child in self.drives:
            agent = self.drives[child]
            agent.outcome = outcome_phrase(meta, agent.node)
            agent.cost_usd = self.last_cost.get(child)
            return
        if state != "running":
            return
        outcome = meta.get("deep_reasoner") or {}
        known = self.drives.get(child)
        title = update.get("title") or (known.title if known else "")
        agent = AgentNode(
            child,
            ids.short(child),
            outcome.get("node"),
            outcome.get("drive", 1),
            title,
            "running",
            None,
        )
        self.drives[child] = agent
        spawning = (meta.get("openhands") or {}).get("parentToolCallId")
        if spawning in self.cells:
            self.cells[spawning].agents.append(agent)

    def root_update(self, run: RunNode, kind: str, update: Mapping[str, Any]) -> None:
        outcome = (update.get("_meta") or {}).get("deep_reasoner") or {}
        if kind == "agent_message_chunk":
            text = first_text(update.get("content"))
            run.root.items.append(
                MessageNode(outcome["outcome"], outcome.get("prompt"), text)
            )
        elif kind == "tool_call" and update.get("kind") == "other":
            self.card(run, update, outcome)
        elif kind == "tool_call":
            cell = self.cell(update)
            if outcome.get("parent") is None:
                run.root.node = outcome.get("node")
                run.root.items.append(cell)
                return
            owner = self.drives.get(ids.child_session_id(run.run, outcome["node"]))
            if owner is not None:
                owner.items.append(cell)

    def card(
        self, run: RunNode, update: Mapping[str, Any], outcome: Mapping[str, Any]
    ) -> None:
        run.mode = "flat"
        call = update["toolCallId"]
        child = ids.child_session_id(run.run, int(_CARD.fullmatch(call).group(2)))
        title = update.get("title", "").split(" · ", 1)[-1]
        agent = AgentNode(
            child,
            ids.short(child),
            outcome.get("node"),
            outcome.get("drive", 1),
            title,
            "running",
            None,
        )
        self.cards[call] = agent
        self.drives[child] = agent
        spawning = ((update.get("_meta") or {}).get("openhands") or {}).get(
            "parentToolCallId"
        )
        if spawning in self.cells:
            self.cells[spawning].agents.append(agent)


def tree(updates: Iterable[tuple[str, Mapping[str, Any]]]) -> Tree:
    """Any mix of root sessions and runs, as a Printer recorded them."""
    return Tree(list(_Rebuild(list(updates)).runs.values()))
