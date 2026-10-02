"""The run tree rebuilt from a client's updates alone (§8.2)."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from deep_reasoning.acp.runlog import Mode


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


@dataclass
class Tree:
    runs: list[RunNode]  # in order of each run's first update

    def __str__(self) -> str:
        raise NotImplementedError


def tree(updates: Iterable[tuple[str, Mapping[str, Any]]]) -> Tree:
    raise NotImplementedError
