"""One ACP root session: its namespace, its commands, its prompts and its runs (§4.2)."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import structlog
from acp import RequestError

from deep_reasoning.acp import ids, texts
from deep_reasoning.acp.catalog import Catalog, CatalogSnapshot, CommandEntry
from deep_reasoning.acp.costs import CostLedger, PriceTable
from deep_reasoning.acp.encoder import (
    Encoder,
    Update,
    closing_message,
    commands_update,
    config_update,
    idle_root_usage,
    namespace_option,
)
from deep_reasoning.acp.route import ModelRoute
from deep_reasoning.acp.runlog import (
    Home,
    PromptEnd,
    RunEnd,
    RunEndReason,
    RunLog,
    SessionIndex,
    detail_of,
)
from deep_reasoning.acp.supervisor import RunHandle
from deep_reasoning.acp.wire import ClientMode, Outbox

logger = structlog.get_logger(__name__)

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
STOP_REASONS: dict[str, Literal["end_turn", "max_turn_requests", "cancelled"]] = {
    "answered": "end_turn",
    "exhausted": "max_turn_requests",
    "failed": "end_turn",
    "build_failed": "end_turn",
    "crashed": "end_turn",
    "rejected": "end_turn",
    "stopped": "cancelled",
    "closed": "cancelled",
}
INVALID_PARAMS = -32602
INVALID_REQUEST = -32600
INTERNAL_ERROR = -32603


def refusal(code: int, sentence: str, name: str) -> RequestError:
    """A JSON-RPC error whose message is the §5.6 sentence, verbatim (§5.5)."""
    return RequestError(code, sentence, {"deep_reasoner": {"error": name}})


@dataclass(frozen=True)
class PromptResult:
    stop_reason: Literal["end_turn", "max_turn_requests", "cancelled"]
    run: str | None
    outcome: PromptOutcome


@dataclass(frozen=True)
class AgentContext:
    """What every session of one connection shares."""

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
    cost: CostLedger = field(default_factory=CostLedger)  # all finished runs
    last_end: RunEndReason | None = None  # picks the next run's fresh-run notice
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)  # kept for D4
    run: RunHandle | None = None  # the live run, if any
    source: dict[str, Any] = field(default_factory=dict)  # the index's: what runs load
    created: datetime = field(default_factory=lambda: datetime.now(UTC))
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)  # prompt, options, load
    prompting: bool = False
    prompts_in_run: int = 0

    def offer(self, namespace: str) -> None:
        """The menu of a namespace, until the conversation starts."""
        self.namespace = namespace
        self.commands = {c.name: c for c in self.snapshot.commands.get(namespace, ())}
        self.advertised |= set(self.commands)

    def menu(self) -> Update:
        """The current menu as an update; empty once the conversation has started."""
        return commands_update(self.id, list(self.commands.values()), self.namespace)

    def options(self) -> list[dict[str, Any]]:
        """The session's config options: the namespace option, narrowed once started."""
        return [namespace_option(self.snapshot, self.namespace, fixed=self.started)]

    def set_namespace(self, value: str) -> list[dict[str, Any]]:
        """The options after the change. Raises RequestError (§5.5)."""
        if value not in self.snapshot.namespaces:
            sentence = texts.unknown_namespace(value, list(self.snapshot.namespaces))
            raise refusal(INVALID_PARAMS, sentence, "UNKNOWN_NAMESPACE")
        if self.started and value != self.namespace:
            sentence = texts.namespace_fixed(self.namespace)
            raise refusal(INVALID_PARAMS, sentence, "NAMESPACE_FIXED")
        if not self.started:
            self.offer(value)
        return self.options()

    async def prompt(self, text: str, dropped: Sequence[str] = ()) -> PromptResult:
        """§4.2's seven steps. dropped: the client's text blocks after the user's own,
        recorded with the prompt and never part of its task."""
        if self.prompting:
            raise refusal(INVALID_REQUEST, texts.PROMPT_BUSY, "PROMPT_BUSY")
        self.prompting = True
        try:
            async with self.lock:
                return await self._prompt(text, list(dropped))
        finally:
            self.prompting = False

    async def _prompt(self, text: str, dropped: list[str]) -> PromptResult:
        token = (
            text.split(maxsplit=1)[0] if text.startswith("/") and text.strip() else ""
        )
        name = token[1:]
        command = self.commands.get(name)
        if command is None and self.started and name in self.advertised:
            return await self._reply(texts.late_decomposition(name), "rejected")
        task = text[len(token) :].strip() if command else text
        if command is not None and not task:
            return await self._reply(
                texts.command_needs_task(name, command.hint), "rejected"
            )
        if not self.started:
            await self._start_conversation()
        if self.run is None:
            decomposition = command.decomposition if command else None
            if (failure := await self._start_run(decomposition)) is not None:
                return failure
        run_id = self.run.run_id
        self.prompts_in_run += 1
        ended = await self.run.prompt(
            self.prompts_in_run,
            text,
            task,
            command.decomposition if command else None,
            dropped,
        )
        outcome = ended.outcome if isinstance(ended, PromptEnd) else ended.reason
        return PromptResult(STOP_REASONS[outcome], run_id, outcome)

    async def _start_conversation(self) -> None:
        """The menu goes away and the namespace is fixed, before the run starts."""
        self.started = True
        self.commands = {}
        await self.ctx.outbox.update(*self.menu())
        await self.ctx.outbox.update(*config_update(self.id, self.options()))
        self.save_index()

    async def _start_run(self, decomposition: str | None) -> PromptResult | None:
        """A fresh run; the reply when it could not be started (nothing ran)."""
        run_id = ids.new_run_id()
        run_dir = self.ctx.home.run_dir(run_id)
        try:
            source = await asyncio.to_thread(
                self.ctx.catalog.materialize, self.namespace, run_dir=run_dir
            )
        except Exception as exc:
            logger.exception("dr_acp.materialize_failed", session=self.id)
            return await self._reply(texts.build_failed(detail_of(exc)), "build_failed")
        library = source.versions.get("library")
        self.source = (
            {"kind": "library", "library": library}
            if library
            else {"kind": "config", "config_path": str(source.config_path)}
        )
        self.run = await RunHandle.start(
            run_id=run_id,
            session=self,
            source=source,
            after=self.last_end,
            decomposition=decomposition,
            home=self.ctx.home,
            route=self.ctx.route,
            outbox=self.ctx.outbox,
            mode=self.ctx.client.mode,
            heartbeat_s=self.ctx.heartbeat_s,
        )
        self.runs.append(run_id)
        self.prompts_in_run = 0
        self.save_index()
        return None

    async def _reply(self, text: str, outcome: PromptOutcome) -> PromptResult:
        """Answered without a run: nothing in any run log, so it does not replay."""
        message = closing_message(self.id, text, run=None, prompt=None, outcome=outcome)
        await self.ctx.outbox.update(*message)
        usage = (
            self.run.encoder.root_usage()
            if self.run
            else idle_root_usage(self.id, self.cost)
        )
        await self.ctx.outbox.update(*usage)
        return PromptResult(STOP_REASONS[outcome], None, outcome)

    async def stop_root(self) -> None:
        """Ends the live run if a prompt is in flight; the REPL survives between prompts."""
        if self.run is not None and self.run.encoder.prompt_in_flight:
            await self.run.kill("stopped")

    def stop_child(self, child_session_id: str) -> bool:
        """Stops the child's branch if it is running; False if the live run has no
        child of that id."""
        child = self.run.encoder.child(child_session_id) if self.run else None
        if child is not None and child.running:
            self.run.stop_node(child.node)
        return child is not None

    async def close(self, grace_s: float = 2.0) -> None:
        if self.run is not None:
            await self.run.close(grace_s)

    def on_run_end(self, reason: RunEndReason) -> None:
        """The run has ended: keep its cost, and forget it."""
        self.cost = self.run.encoder.root_cost
        self.last_end = reason
        self.run = None
        self.save_index()

    async def replay(self) -> None:
        """Every run of the session, from its log (§5.7); a run that never ended is lost."""
        carry = CostLedger()
        for run_id in self.runs:
            events = list(RunLog.read(self.ctx.home, run_id))
            if not any(isinstance(ev, RunEnd) for ev in events):
                lost = RunEnd(reason="lost", exit_code=None, detail=None)
                events.append(RunLog.open(self.ctx.home, run_id).append(lost))
            encoder = Encoder(
                root=self.id,
                run=run_id,
                mode=self.ctx.client.mode,
                replay=True,
                carry=carry,
            )
            for ev in events:
                for update in encoder.feed(ev):
                    await self.ctx.outbox.update(*update)
            carry = encoder.root_cost
            self.last_end = next(
                ev.reason for ev in reversed(events) if isinstance(ev, RunEnd)
            )
        self.cost = carry
        self.save_index()

    def save_index(self) -> None:
        SessionIndex(
            session=self.id,
            cwd=str(self.cwd),
            namespace=self.namespace,
            started=self.started,
            source=self.source,
            runs=self.runs,
            cost=self.cost,
            last_end=self.last_end,
            created=self.created,
        ).save(self.ctx.home)
