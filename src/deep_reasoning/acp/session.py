"""One ACP root session: its namespace, its commands, its prompts and its runs (§4.2)."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from deep_reasoning.acp.catalog import Catalog, CatalogSnapshot, CommandEntry
from deep_reasoning.acp.costs import CostLedger, PriceTable
from deep_reasoning.acp.route import ModelRoute
from deep_reasoning.acp.runlog import Home, RunEndReason
from deep_reasoning.acp.supervisor import RunHandle
from deep_reasoning.acp.wire import ClientMode, Outbox

PromptOutcome = Literal[
    "answered",
    "exhausted",
    "failed",
    "build_failed",
    "stopped",
    "crashed",
    "closed",
    "rejected",
]


@dataclass(frozen=True)
class PromptResult:
    stop_reason: Literal["end_turn", "max_turn_requests", "cancelled"]
    run: str | None
    outcome: PromptOutcome


@dataclass(frozen=True)
class AgentContext:
    """What every session of one connection shares, from DrAcpAgent."""

    catalog: Catalog
    home: Home
    route: ModelRoute
    outbox: Outbox
    prices: PriceTable
    client: ClientMode
    heartbeat_s: float


@dataclass
class Session:
    id: str  # "s-" + 16 hex
    cwd: Path
    snapshot: CatalogSnapshot
    namespace: str
    ctx: AgentContext
    started: bool = False  # set by the first accepted prompt; fixes the namespace
    commands: dict[str, CommandEntry] = field(default_factory=dict)
    advertised: set[str] = field(default_factory=set)  # every command name ever offered
    runs: list[str] = field(default_factory=list)  # run ids, oldest first
    cost: CostLedger = field(
        default_factory=CostLedger
    )  # the root's cumulative cost over all finished runs
    last_end: RunEndReason | None = None  # picks the next run's fresh-run notice
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)  # kept for D4
    run: RunHandle | None = None  # the live run, if any
    lock: asyncio.Lock = field(
        default_factory=asyncio.Lock
    )  # prompt, options, load, close

    async def prompt(self, text: str) -> PromptResult:
        """§4.2's seven steps."""
        raise NotImplementedError

    def options(self) -> list[dict[str, Any]]:
        """The session's config options: the namespace option, narrowed once started."""
        raise NotImplementedError

    def set_namespace(self, value: str) -> list[dict[str, Any]]:
        """The options after the change. Raises RequestError (§5.5)."""
        raise NotImplementedError

    async def stop_root(self) -> None:
        raise NotImplementedError

    def stop_child(self, child_session_id: str) -> None:
        raise NotImplementedError

    async def close(self, grace_s: float = 2.0) -> None:
        raise NotImplementedError

    def on_run_end(self, reason: RunEndReason) -> None:
        """Called by the pump when it feeds run.end: take the run's cost and forget it."""
        raise NotImplementedError
