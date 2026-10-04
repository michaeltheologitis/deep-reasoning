"""STAND-IN for DR4 on deep_reasoner d7334ae. Not counted, not for merge.

DR4 asks deep_reasoner for a typed event stream, `async for ev in reasoner.events(task)`,
and `reasoner.stop(node_id)`. This module patches both onto d7334ae by adapting today's
structlog events, so that dr-acp's recorder can be rewritten against them and the payoff
measured. Everything here is what deep_reasoner would do natively at its own log sites;
the reconstruction dr-acp's recorder does today moves here, not away.

Importing it installs the patches.
"""

import ast
import asyncio
import contextvars
import inspect
import re
import sys
import textwrap
import threading
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

import structlog
from deep_reasoner.v2.agent import DeepReasoner, DeepReasonerAgentBase
from deep_reasoner.v2.claude_reasoner import ClaudeDeepReasoner
from deep_reasoner.v2.messages import NoCodeBlock, code

# ── DR4's events (deep_reasoner.v2.events in Dean's version) ───────────────────


@dataclass(frozen=True)
class AgentStarted:
    """Each drive of an agent, before its first model call."""

    node_id: int
    parent_id: int | None  # the agent in whose cell this one was started
    parent_cell: int | None  # that cell
    namespace: str
    backbone: Literal["chat", "claude_code"]
    task: str
    max_iter: int | None
    run: str | None


@dataclass(frozen=True)
class ModelCalled:
    """A model call that returned, on the agent that pays for it."""

    node_id: int
    call: Literal["think", "tool", "claude"]
    model: str | None
    usage: Mapping[str, Any]
    cost_usd: float | None  # what the provider or Claude reported, else None


@dataclass(frozen=True)
class Thought:
    node_id: int
    text: str  # a reply without its code block; a Claude session's response


@dataclass(frozen=True)
class CellStarted:
    node_id: int
    cell: int  # per agent, from 1, across its drives
    source: str
    origin: Literal["think", "scripted"]


@dataclass(frozen=True)
class CellEnded:
    node_id: int
    cell: int
    source: str
    output: str  # what the cell printed, unwrapped
    interrupted: bool  # unwound before it finished


@dataclass(frozen=True)
class AgentEnded:
    node_id: int
    status: Literal["done", "exhausted", "failed", "stopped"]
    iter: int | None
    answer: Any  # FinalAnswer's value; the exhaustion sentence; None otherwise
    detail: str | None
    stopped_by: int | None


Event = AgentStarted | ModelCalled | Thought | CellStarted | CellEnded | AgentEnded


@dataclass(frozen=True)
class Stopped:
    """What a stopped agent answers its parent's cell."""

    node: int


# ── the reconstruction (deep_reasoner knows all of this where it logs) ────────

BACKBONES = {"DeepReasoner": "chat", "ClaudeDeepReasoner": "claude_code"}
_REPL_BLOCK = re.compile(r"<repl>.*?(?:</repl>|$)", re.DOTALL)
_THINK_TAG = re.compile(r"</?think>")
_OBSERVATION = re.compile(r"\A<observation>\n?(.*?)\n?</observation>\Z", re.DOTALL)


def _source_of(reply: str) -> str | None:
    try:
        return code(reply).source
    except NoCodeBlock:
        return None


@dataclass
class _Agent:
    node: int
    open_cell: int | None = None
    open_source: str = ""
    cells: int = 0
    running: bool = True


@dataclass
class _Run:
    """One reasoner's tree, across its drives."""

    put: Callable[[Event], None] | None = None
    agents: dict[int, _Agent] = field(default_factory=dict)
    stopped: set[int] = field(default_factory=set)
    loop: asyncio.AbstractEventLoop | None = None


_RUN: contextvars.ContextVar[_Run | None] = contextvars.ContextVar(
    "dr4_standin_run", default=None
)
_LOCK = threading.RLock()


def _emit(run: _Run, ev: Event) -> None:
    if run.put is not None:
        run.put(ev)


def _cell_start(run: _Run, agent: _Agent, source: str, origin: str) -> None:
    agent.cells += 1
    agent.open_cell, agent.open_source = agent.cells, source
    _emit(run, CellStarted(agent.node, agent.cells, source, origin))  # type: ignore[arg-type]


def _cell_end(
    run: _Run, agent: _Agent, source: str, output: str, interrupted: bool
) -> None:
    _emit(run, CellEnded(agent.node, agent.open_cell, source, output, interrupted))  # type: ignore[arg-type]
    agent.open_cell, agent.open_source = None, ""


def _owner(run: _Run, ev: dict[str, Any]) -> _Agent | None:
    node = ev.get("node_id")
    if node in run.agents:
        return run.agents[node]
    for ancestor in reversed(tuple(ev.get("ancestry") or ())):
        if ancestor in run.agents:
            return run.agents[ancestor]
    return None


def _working_for(run: _Run, ev: dict[str, Any], kind: str) -> _Agent | None:
    """The agent; or, for a fork, the agent whose own LLM or REPL logs on a node
    directly under it, outside any cell of it."""
    if ev.get("kind") == "agent":
        return run.agents.get(ev.get("node_id"))
    ancestry = tuple(ev.get("ancestry") or ())
    parent = run.agents.get(ancestry[-2]) if len(ancestry) > 1 else None
    if ev.get("kind") != kind or parent is None:
        return None
    return parent if kind == "repl" or parent.open_cell is None else None


def _tap(logger: Any, method_name: str, ev: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: today's events into DR4's, for the run in this context."""
    run = _RUN.get()
    if run is None:
        return ev
    with _LOCK:
        name = ev.get("event")
        if name == "agent.start":
            _agent_start(run, ev)
        elif name == "agent.loop":
            agent = _working_for(run, ev, "llm")
            if agent is not None and agent.open_cell is None:
                reply = str((ev.get("messages") or [{}])[-1].get("content") or "")
                if thought := _THINK_TAG.sub("", _REPL_BLOCK.sub("", reply)).strip():
                    _emit(run, Thought(agent.node, thought))
                if (source := _source_of(reply)) is not None:
                    _cell_start(run, agent, source, "think")
        elif name == "llm.call" and (owner := _owner(run, ev)):
            usage = ev.get("usage") or {}
            call = "think" if _working_for(run, ev, "llm") else "tool"
            _emit(
                run,
                ModelCalled(
                    owner.node, call, ev.get("model"), usage, usage.get("cost")
                ),
            )
        elif name == "claude.call" and (owner := _owner(run, ev)):
            usage = ev.get("usage") or {}
            _emit(
                run,
                ModelCalled(
                    owner.node, "claude", ev.get("model"), usage, ev.get("cost_usd")
                ),
            )
            if response := str(ev.get("response") or "").strip():
                _emit(run, Thought(owner.node, response))
        elif name == "repl.execute":
            agent = _working_for(run, ev, "repl")
            if agent is not None:
                source = str(ev.get("source") or "")
                observation = str(ev.get("observation") or "")
                match = _OBSERVATION.match(observation)
                if agent.open_cell is None:
                    _cell_start(run, agent, source, "think")
                output = match.group(1) if match else observation
                _cell_end(run, agent, source, output, interrupted=False)
    return ev


def _agent_start(run: _Run, ev: dict[str, Any]) -> None:
    node = ev["node_id"]
    ancestry = tuple(ev.get("ancestry") or (node,))
    agents = [a for a in ancestry[:-1] if a in run.agents]
    parent = run.agents[agents[-1]] if agents else None
    if parent is not None and parent.open_cell is None:
        _cell_start(run, parent, "", "think")
    agent = run.agents.setdefault(node, _Agent(node))
    agent.running = True
    backbone = str(ev.get("backbone"))
    _emit(
        run,
        AgentStarted(
            node_id=node,
            parent_id=parent.node if parent else None,
            parent_cell=parent.open_cell if parent else None,
            namespace=ev.get("namespace") or "root",
            backbone=BACKBONES.get(backbone, backbone),  # type: ignore[arg-type]
            task=str(ev.get("task") or ""),
            max_iter=ev.get("max_iter"),
            run=ev.get("run"),
        ),
    )


# ── stop(node_id): EXP-42 points 1-6, as the fake in tests/acp/fakes did at b2a74e0 ──


class _Stop(BaseException):
    """Unwinds one stopped drive; never reaches a cell."""


def _node(agent: DeepReasonerAgentBase) -> tuple[int, tuple[int, ...]]:
    """The node the agent logs as. Not agent._node: a fork captures it after its LLM's
    node is bound, and node_id is a shared counter, so it reads the LLM's id."""
    values = agent._log_vars
    return values["node_id"], tuple(values["ancestry"])


def _stopped_by(run: _Run, ancestry: tuple[int, ...]) -> int | None:
    return next((n for n in reversed(ancestry) if n in run.stopped), None)


_note_drive = DeepReasonerAgentBase._note_drive


def _patched_note_drive(self: DeepReasonerAgentBase, event: str, **fields: Any) -> None:
    run = _RUN.get()
    if run is None:
        return _note_drive(self, event, **fields)
    node, ancestry = _node(self)
    with _LOCK:
        if event == "agent.start":
            run.stopped.discard(node)  # a new drive of a stopped agent runs
        stopped_by = _stopped_by(run, ancestry)
    if event == "agent.turn" and stopped_by is not None:
        raise _Stop(node)
    stopped = event == "agent.end" and str(fields.get("detail", "")).startswith("_Stop")
    if stopped:
        fields = {k: v for k, v in fields.items() if k != "detail"} | {
            "status": "stopped"
        }
    _note_drive(self, event, **fields)
    if event != "agent.end":
        return
    with _LOCK:
        agent = run.agents.get(node)
        if agent is not None:
            agent.running = False
            if agent.open_cell is not None:
                _cell_end(run, agent, agent.open_source, "", interrupted=True)
        status = fields["status"]
        _emit(
            run,
            AgentEnded(
                node_id=node,
                status=status,
                iter=fields.get("iter"),
                answer=self.final_answer if status in ("done", "exhausted") else None,
                detail=fields.get("detail"),
                stopped_by=stopped_by if stopped else None,
            ),
        )


def _answer_stopped(self: DeepReasonerAgentBase) -> Stopped:
    self._done = True
    self.final_answer = Stopped(_node(self)[0])
    return self.final_answer


def _stoppable_anext() -> Callable[..., Any]:
    """__anext__ as Dean would change it: a stopped drive answers Stopped(node).

    Recompiled from its own source, at its own file, lines and columns, with the body
    wrapped in `try: ... except _Stop: return _answer_stopped(self)`: a wrapper function
    would add a frame to every traceback through a drive, and a child's traceback is what
    its parent's cell prints (the goldens hold them)."""
    lines, first = inspect.getsourcelines(DeepReasonerAgentBase.__anext__)
    indent = len(lines[0]) - len(lines[0].lstrip())
    tree = ast.parse(textwrap.dedent("".join(lines)))
    for node in ast.walk(tree):
        if hasattr(node, "col_offset"):
            node.col_offset += indent
            if node.end_col_offset is not None:
                node.end_col_offset += indent
    ast.increment_lineno(tree, first - 1)
    function = tree.body[0]
    guard = ast.parse(
        "try:\n    pass\nexcept _DR4_Stop:\n    return _dr4_answer_stopped(self)"
    )
    for node in ast.walk(guard):
        if hasattr(node, "lineno"):
            node.lineno = node.end_lineno = function.lineno
            node.col_offset, node.end_col_offset = indent, indent + 1
    guard.body[0].body = function.body
    function.body = guard.body
    module = sys.modules[DeepReasonerAgentBase.__module__]
    module.__dict__.update(_DR4_Stop=_Stop, _dr4_answer_stopped=_answer_stopped)
    namespace: dict[str, Any] = {}
    exec(compile(tree, module.__file__, "exec"), module.__dict__, namespace)  # noqa: S102
    anext_ = namespace["__anext__"]
    anext_.__qualname__ = DeepReasonerAgentBase.__anext__.__qualname__
    return anext_


def _scripting(record_turn: Callable[..., None]) -> Callable[..., None]:
    """A backbone's record_turn that first opens a supplied turn's cell."""

    def patched(
        self: DeepReasonerAgentBase, text: str, *, puppeteered: bool = False
    ) -> None:
        run = _RUN.get()
        if run is not None and puppeteered:
            with _LOCK:
                agent = run.agents[_node(self)[0]]
                block = code(text, start=self._code_start, end=self._code_end)
                _cell_start(run, agent, block.source, "scripted")
        record_turn(self, text, puppeteered=puppeteered)

    return patched


# ── events() and stop() ───────────────────────────────────────────────────────

_DONE = object()


def _ensure_tap() -> None:
    """Put the tap right after merge_contextvars, so it sees node_id and ancestry."""
    processors = list(structlog.get_config()["processors"])
    if _tap not in processors:
        structlog.configure(processors=[processors[0], _tap, *processors[1:]])


def _run_of(reasoner: DeepReasonerAgentBase) -> _Run:
    run = reasoner.__dict__.get("_dr4_run")
    if run is None:
        run = reasoner.__dict__["_dr4_run"] = _Run()
        run.loop = asyncio.new_event_loop()
        threading.Thread(target=run.loop.run_forever, daemon=True).start()
    return run


async def events(self: DeepReasonerAgentBase, task: Any = None) -> AsyncIterator[Event]:
    """Drive *task* on the reasoner's own loop and thread; yield its tree's events.

    The caller's loop stays free while a cell runs. Ends after the root's AgentEnded;
    raises what the drive raised. Closing it early stops the root.
    """
    run = _run_of(self)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Any] = asyncio.Queue()
    _ensure_tap()

    def put(ev: Any) -> None:
        loop.call_soon_threadsafe(queue.put_nowait, ev)

    run.put = put
    context = contextvars.copy_context()
    context.run(_RUN.set, run)
    drive = context.run(asyncio.run_coroutine_threadsafe, self.acall(task), run.loop)
    drive.add_done_callback(lambda _: put(_DONE))
    try:
        while (ev := await queue.get()) is not _DONE:
            yield ev
        drive.result()
    finally:
        if not drive.done() and getattr(self, "_log_vars", None):
            self.stop(_node(self)[0])


def stop(self: DeepReasonerAgentBase, node_id: int) -> bool:
    """Stop that agent and its descendants at their next turn; thread-safe. False when
    the agent is not running in this reasoner's tree."""
    run = _run_of(self)
    with _LOCK:
        agent = run.agents.get(node_id)
        if agent is None or not agent.running:
            return False
        run.stopped.add(node_id)
        return True


DeepReasonerAgentBase._note_drive = _patched_note_drive
DeepReasonerAgentBase.__anext__ = _stoppable_anext()
for _backbone in (DeepReasoner, ClaudeDeepReasoner):
    _backbone.record_turn = _scripting(_backbone.record_turn)
DeepReasonerAgentBase.events = events
DeepReasonerAgentBase.stop = stop

__all__ = [
    "AgentEnded",
    "AgentStarted",
    "CellEnded",
    "CellStarted",
    "Event",
    "ModelCalled",
    "Stopped",
    "Thought",
]
