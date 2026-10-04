"""RunEvents -> ACP session updates (§5.2 native, §5.3 flat, §5.7 replay).

Pure: no I/O, no clock. One Encoder per run, and one per run in a replay.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from deep_reasoning.acp import ids, texts
from deep_reasoning.acp.catalog import CatalogSnapshot, CommandEntry
from deep_reasoning.acp.costs import NO_COST, CostLedger
from deep_reasoning.acp.runlog import (
    AgentEnd,
    AgentStart,
    CellEnd,
    CellStart,
    McpStatus,
    Mode,
    PromptEnd,
    PromptStart,
    RunEnd,
    RunEvent,
    RunStart,
    StopAccepted,
    Thought,
    Usage,
)

# (sessionId, the "update" object of a session/update notification)
Update = tuple[str, dict[str, Any]]

TITLE_MAX = 120
DESCRIPTION_MAX = 2000
STOP_REASONS = {
    "done": "end_turn",
    "exhausted": "max_turn_requests",
    "failed": "end_turn",
    "stopped": "cancelled",
}
CLOSING_TEXT = {
    "answered": lambda end: end.answer or "",
    "exhausted": lambda end: end.answer or "",
    "failed": lambda end: texts.root_failed(end.detail or ""),
    "build_failed": lambda end: texts.build_failed(end.detail or ""),
}


@dataclass(frozen=True)
class ChildRef:
    node: int
    running: bool


@dataclass
class _Tally:
    usd: float = 0.0
    unknown_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    sources: set[str] = field(default_factory=set)

    def add(self, ev: Usage) -> None:
        self.tokens_in += ev.tokens_in
        self.tokens_out += ev.tokens_out
        if ev.cost_usd is None:
            self.unknown_calls += 1
            return
        self.usd += ev.cost_usd
        self.sources.add(ev.cost_source or "table")

    @property
    def source(self) -> str | None:
        if len(self.sources) > 1:
            return "mixed"
        return next(iter(self.sources), None)


@dataclass
class _Agent:
    node: int
    parent: int | None
    ancestry: tuple[int, ...]
    namespace: str
    backbone: str
    task: str
    drive: int
    parent_cell: int | None
    running: bool = True
    open_cells: dict[int, str] = field(
        default_factory=dict
    )  # k -> the code at its start
    total: _Tally = field(default_factory=_Tally)  # its own calls and its descendants'
    used: int = 0  # the tokens of its latest think call
    window: int = 0


def _text(text: str) -> dict[str, Any]:
    return {"type": "text", "text": text}


def _content(text: str) -> list[dict[str, Any]]:
    return [{"type": "content", "content": _text(text)}]


def _title(task: str) -> tuple[str, bool]:
    """The task's first line, at most TITLE_MAX characters, " …" when cut."""
    first = task.strip().split("\n", 1)[0]
    if len(first) > TITLE_MAX or "\n" in task.strip():
        return f"{first[:TITLE_MAX].rstrip()} …", True
    return first, False


def _cell_title(code: str) -> str:
    if not code:
        return "Run …"
    first, *rest = code.split("\n")
    return f"Run {first}" + (" …" if rest else "")


def closing_message(
    root: str, text: str, *, run: str | None, prompt: int | None, outcome: str
) -> Update:
    """§5.2's CM: the root agent_message_chunk that ends a turn or a run."""
    meta = {"deep_reasoner": {"run": run, "prompt": prompt, "outcome": outcome}}
    return (
        root,
        {"sessionUpdate": "agent_message_chunk", "content": _text(text), "_meta": meta},
    )


def _usage_update(
    used: int, size: int, tally: _Tally, carry: CostLedger = NO_COST
) -> dict[str, Any]:
    update: dict[str, Any] = {
        "sessionUpdate": "usage_update",
        "used": used,
        "size": size,
    }
    if tally.unknown_calls == 0 and carry.complete:
        update["cost"] = {"amount": carry.usd + tally.usd, "currency": "USD"}
    update["_meta"] = {
        "deep_reasoner": {
            "cost_source": tally.source,
            "tokens_in": carry.tokens_in + tally.tokens_in,
            "tokens_out": carry.tokens_out + tally.tokens_out,
            "unknown_calls": tally.unknown_calls,
        }
    }
    return update


def idle_root_usage(root: str, cost: CostLedger) -> Update:
    """The root's usage_update while no run is live: the conversation's cost so far."""
    return root, _usage_update(0, 0, _Tally(), cost)


def commands_update(
    root: str, commands: Sequence[CommandEntry], namespace: str
) -> Update:
    """available_commands_update for a namespace's menu (§5.5's command shape)."""
    entries = [
        {
            "name": c.name,
            "description": c.description,
            "input": {"hint": c.hint},
            "_meta": {
                "deep_reasoner": {
                    "decomposition": c.decomposition,
                    "namespace": namespace,
                }
            },
        }
        for c in commands
    ]
    return root, {
        "sessionUpdate": "available_commands_update",
        "availableCommands": entries,
    }


def namespace_option(
    snapshot: CatalogSnapshot, namespace: str, *, fixed: bool
) -> dict[str, Any]:
    """The namespace select option (§5.5); fixed: only the current value is offered."""
    values = (namespace,) if fixed else snapshot.namespaces
    return {
        "id": "namespace",
        "name": "Namespace",
        "type": "select",
        "currentValue": namespace,
        "description": texts.NAMESPACE_FIXED_NOTE if fixed else texts.NAMESPACE_OPEN,
        "options": [{"value": v, "name": v} for v in values],
    }


def config_update(root: str, options: list[dict[str, Any]]) -> Update:
    """config_option_update carrying the full options."""
    return root, {"sessionUpdate": "config_option_update", "configOptions": options}


class Encoder:
    def __init__(
        self,
        *,
        root: str,
        run: str,
        mode: Mode,
        replay: bool = False,
        carry: CostLedger = NO_COST,
    ) -> None:
        self._root = root
        self._run = run
        self._mode = mode
        self._replay = replay
        self._carry = carry
        self._agents: dict[int, _Agent] = {}
        self._root_node: int | None = None
        self._prompt: int | None = None
        self._in_flight = False
        self._dirty: set[int] = set()
        self._child_id = re.compile(rf"{re.escape(run)}-n(\d+)")

    # ── the public surface ────────────────────────────────────────────────────

    def feed(self, ev: RunEvent) -> list[Update]:
        """The updates one RunEvent produces: §5.2 (native), §5.3 (flat)."""
        match ev:
            case RunStart():
                return self._run_start(ev)
            case PromptStart():
                return self._prompt_start(ev)
            case AgentStart():
                return self._agent_start(ev)
            case Thought():
                return self._thought(ev)
            case CellStart():
                return self._cell_start(ev)
            case CellEnd():
                return self._cell_end(ev)
            case Usage():
                self._usage(ev)
                return []
            case StopAccepted():
                return self._stop_accepted(ev)
            case AgentEnd():
                return self._agent_end(ev)
            case McpStatus():
                return self._mcp_status(ev)
            case PromptEnd():
                return self._prompt_end(ev)
            case RunEnd():
                return self._run_end(ev)
        return []

    def flush_usage(self) -> list[Update]:
        """A usage_update for each session whose totals changed since the last flush."""
        if self._replay:
            return []
        dirty, self._dirty = self._dirty, set()
        if self._mode == "flat":
            dirty &= {self._root_node}
        return [self._usage_of(node) for node in sorted(dirty)]

    def root_usage(self) -> Update:
        """The root's usage_update, always."""
        if self._root_node is None:
            return idle_root_usage(self._root, self._carry)
        self._dirty.discard(self._root_node)
        return self._usage_of(self._root_node)

    def child(self, session_id: str) -> ChildRef | None:
        match = self._child_id.fullmatch(session_id)
        agent = match and self._agents.get(int(match.group(1)))
        if not agent or agent.node == self._root_node:
            return None
        return ChildRef(node=agent.node, running=agent.running)

    @property
    def prompt_in_flight(self) -> bool:
        """A prompt.start was fed and neither its prompt.end nor a run.end yet."""
        return self._in_flight

    @property
    def root_cost(self) -> CostLedger:
        """carry plus this run's root total."""
        if self._root_node is None:
            return self._carry
        total = self._agents[self._root_node].total
        return CostLedger(
            usd=self._carry.usd + total.usd,
            complete=self._carry.complete and total.unknown_calls == 0,
            tokens_in=self._carry.tokens_in + total.tokens_in,
            tokens_out=self._carry.tokens_out + total.tokens_out,
        )

    # ── sessions, ids and metadata ────────────────────────────────────────────

    def _session(self, node: int) -> str:
        return (
            self._root
            if node == self._root_node
            else ids.child_session_id(self._run, node)
        )

    def _cell_session(self, node: int) -> str:
        return self._root if self._mode == "flat" else self._session(node)

    def _meta(self, agent: _Agent) -> dict[str, Any]:
        meta: dict[str, Any] = {}
        if agent.parent is not None and agent.parent_cell is not None:
            spawning = ids.cell_id(self._run, agent.parent, agent.parent_cell)
            meta["openhands"] = {"parentToolCallId": spawning}
        meta["deep_reasoner"] = {
            "run": self._run,
            "node": agent.node,
            "parent": agent.parent,
            "depth": len(agent.ancestry),
            "namespace": agent.namespace,
            "backbone": agent.backbone,
            "drive": agent.drive,
        }
        return meta

    def _path(self, agent: _Agent) -> str:
        return " › ".join(f"#{n}" for n in agent.ancestry)

    def _usage_of(self, node: int) -> Update:
        agent = self._agents[node]
        carry = self._carry if node == self._root_node else NO_COST
        return self._session(node), _usage_update(
            agent.used, agent.window, agent.total, carry
        )

    def _closing(self, text: str, outcome: str) -> Update:
        return closing_message(
            self._root, text, run=self._run, prompt=self._prompt, outcome=outcome
        )

    # ── one method per RunEvent ───────────────────────────────────────────────

    def _run_start(self, ev: RunStart) -> list[Update]:
        notice = texts.fresh_run_notice(ev.after)
        if notice is None:
            return []
        message = {
            "sessionUpdate": "agent_message_chunk",
            "content": _text(notice + "\n\n"),
        }
        return [(self._root, message)]

    def _mcp_status(self, ev: McpStatus) -> list[Update]:
        """D4: a root notice for each MCP server not bound, ahead of the first answer."""
        notices = [texts.mcp_notice(server) for server in ev.servers]
        return [
            (
                self._root,
                {"sessionUpdate": "agent_message_chunk", "content": _text(n + "\n\n")},
            )
            for n in notices
            if n is not None
        ]

    def _prompt_start(self, ev: PromptStart) -> list[Update]:
        self._prompt = ev.prompt
        self._in_flight = True
        if not self._replay:
            return []
        return [
            (
                self._root,
                {"sessionUpdate": "user_message_chunk", "content": _text(ev.text)},
            )
        ]

    def _agent_start(self, ev: AgentStart) -> list[Update]:
        agent = self._agents.get(ev.node)
        if agent is None:
            agent = _Agent(
                node=ev.node,
                parent=ev.parent,
                ancestry=tuple(ev.ancestry),
                namespace=ev.namespace,
                backbone=ev.backbone,
                task=ev.task,
                drive=ev.drive,
                parent_cell=ev.parent_cell,
            )
            self._agents[ev.node] = agent
        agent.drive, agent.task, agent.parent_cell = ev.drive, ev.task, ev.parent_cell
        agent.running = True
        if ev.parent is None:
            self._root_node = ev.node
            return []
        title, cut = _title(ev.task)
        if self._mode == "flat":
            card = {
                "sessionUpdate": "tool_call",
                "toolCallId": ids.card_id(self._run, ev.node, ev.drive),
                "title": f"{self._path(agent)} · {title}",
                "kind": "other",
                "status": "in_progress",
                "rawInput": {"task": ev.task},
                "_meta": self._meta(agent),
            }
            return [(self._root, card)]
        announce: dict[str, Any] = {
            "sessionUpdate": "subagent_update",
            "sessionId": self._session(ev.node),
            "title": title,
        }
        if ev.drive == 1:
            if cut:
                announce["description"] = ev.task[:DESCRIPTION_MAX]
            if not self._replay:
                announce["capabilities"] = {"cancel": {}}
        announce |= {"state": {"state": "running"}, "_meta": self._meta(agent)}
        parent = self._session(ev.parent)
        task = {
            "sessionUpdate": "session_message",
            "messageId": ids.task_message_id(self._run, ev.node, ev.drive),
            "senderSessionId": parent,
            "recipientSessionId": self._session(ev.node),
            "content": [_text(ev.task)],
        }
        return [(parent, announce), (parent, task)]

    def _thought(self, ev: Thought) -> list[Update]:
        if self._mode == "flat" and ev.node != self._root_node:
            return []
        thought = {"sessionUpdate": "agent_thought_chunk", "content": _text(ev.text)}
        return [(self._session(ev.node), thought)]

    def _cell_start(self, ev: CellStart) -> list[Update]:
        agent = self._agents[ev.node]
        agent.open_cells[ev.cell] = ev.code
        title = _cell_title(ev.code)
        if self._mode == "flat" and ev.node != self._root_node:
            title = f"{self._path(agent)} › {title}"
        call = {
            "sessionUpdate": "tool_call",
            "toolCallId": ids.cell_id(self._run, ev.node, ev.cell),
            "title": title,
            "kind": "execute",
            "status": "in_progress",
            "rawInput": {"command": ev.code},
            "_meta": {
                "deep_reasoner": {
                    "run": self._run,
                    "node": ev.node,
                    "parent": agent.parent,
                    "depth": len(agent.ancestry),
                    "cell": ev.cell,
                    "origin": ev.origin,
                }
            },
        }
        return [(self._cell_session(ev.node), call)]

    def _cell_end(self, ev: CellEnd) -> list[Update]:
        agent = self._agents[ev.node]
        code_at_start = agent.open_cells.pop(ev.cell, "")
        update: dict[str, Any] = {
            "sessionUpdate": "tool_call_update",
            "toolCallId": ids.cell_id(self._run, ev.node, ev.cell),
        }
        if ev.interrupted:
            update |= {
                "status": "failed",
                "content": _content(texts.cell_interrupted("the agent stopped")),
            }
        else:
            update |= {
                "status": "completed",
                "content": _content(ev.output),
                "rawOutput": ev.output,
            }
        if not code_at_start and ev.code:
            title = _cell_title(ev.code)
            if self._mode == "flat" and ev.node != self._root_node:
                title = f"{self._path(agent)} › {title}"
            update |= {"title": title, "rawInput": {"command": ev.code}}
        return [(self._cell_session(ev.node), update)]

    def _usage(self, ev: Usage) -> None:
        owner = self._agents[ev.node]
        for node in owner.ancestry:
            self._agents[node].total.add(ev)
            self._dirty.add(node)
        if ev.call == "think":
            owner.used = ev.tokens_in + ev.tokens_out
            owner.window = ev.context_window or 0

    def _stop_accepted(self, ev: StopAccepted) -> list[Update]:
        if not ev.accepted or self._mode == "flat":
            return []
        backbone = ev.backbone or self._agents[ev.node].backbone
        text = texts.stop_requested(ev.mode, backbone)
        return [
            (
                self._session(ev.node),
                {"sessionUpdate": "agent_thought_chunk", "content": _text(text)},
            )
        ]

    def _close_cells(self, agent: _Agent, reason: str) -> list[Update]:
        closed = [
            (
                self._cell_session(agent.node),
                {
                    "sessionUpdate": "tool_call_update",
                    "toolCallId": ids.cell_id(self._run, agent.node, k),
                    "status": "failed",
                    "content": _content(texts.cell_interrupted(reason)),
                },
            )
            for k in sorted(agent.open_cells)
        ]
        agent.open_cells.clear()
        return closed

    def _agent_end(self, ev: AgentEnd) -> list[Update]:
        agent = self._agents[ev.node]
        agent.running = False
        updates = self._close_cells(agent, "the agent stopped")
        if ev.node == self._root_node:
            return updates
        outcome: dict[str, Any] = {"status": ev.status}
        if ev.detail is not None:
            outcome["detail"] = ev.detail
        if ev.stopped_by is not None:
            outcome["stopped_by"] = ev.stopped_by
        if ev.collateral:
            outcome["collateral"] = True
        message = ev.answer if ev.status in ("done", "exhausted") else None
        if ev.status == "failed":
            message = texts.child_failed(ev.detail or "")
        if self._mode == "flat":
            status = "completed" if ev.status in ("done", "exhausted") else "failed"
            text = message if message is not None else (ev.detail or "")
            return [*updates, self._card_update(agent, status, text, outcome)]
        if message is not None:
            answer = {
                "sessionUpdate": "session_message",
                "messageId": ids.answer_message_id(self._run, ev.node, agent.drive),
                "senderSessionId": self._session(ev.node),
                "recipientSessionId": self._session(agent.parent),
                "content": [_text(message)],
            }
            updates.append((self._session(ev.node), answer))
        updates.append(self._usage_of(ev.node))
        self._dirty.discard(ev.node)
        state = {"state": "idle", "stopReason": STOP_REASONS[ev.status]}
        updates.append(self._idle(agent, state, outcome))
        return updates

    def _idle(
        self, agent: _Agent, state: dict[str, Any], outcome: dict[str, Any]
    ) -> Update:
        meta = self._meta(agent)
        meta["deep_reasoner"] |= outcome
        idle = {
            "sessionUpdate": "subagent_update",
            "sessionId": self._session(agent.node),
            "state": state,
            "_meta": meta,
        }
        return self._session(agent.parent), idle

    def _card_update(
        self, agent: _Agent, status: str, text: str, outcome: dict[str, Any]
    ) -> Update:
        card = {
            "sessionUpdate": "tool_call_update",
            "toolCallId": ids.card_id(self._run, agent.node, agent.drive),
            "status": status,
            "content": _content(text),
            "_meta": {
                "deep_reasoner": {"run": self._run, "node": agent.node, **outcome}
            },
        }
        return self._root, card

    def _prompt_end(self, ev: PromptEnd) -> list[Update]:
        self._in_flight = False
        closing = self._closing(CLOSING_TEXT[ev.outcome](ev), ev.outcome)
        return [closing, self.root_usage()]

    def _run_end(self, ev: RunEnd) -> list[Update]:
        if ev.reason == "lost":
            return [self._closing(texts.REPLAY_LOST, "lost")]
        if not self._in_flight or ev.reason in ("failed", "build_failed"):
            return []
        self._in_flight = False
        crashed = ev.reason == "crashed"
        reason = "the run crashed" if crashed else "the run was stopped"
        outcome = {"status": "crashed" if crashed else "stopped"}
        state = (
            {"state": "idle"}
            if crashed
            else {"state": "idle", "stopReason": "cancelled"}
        )
        running = sorted(
            (
                a
                for a in self._agents.values()
                if a.running and a.node != self._root_node
            ),
            key=lambda a: (-len(a.ancestry), a.node),
        )
        updates: list[Update] = []
        for agent in running:
            agent.running = False
            updates.extend(self._close_cells(agent, reason))
            if self._mode == "flat":
                updates.append(
                    self._card_update(
                        agent, "failed", texts.cell_interrupted(reason), outcome
                    )
                )
            else:
                updates.append(self._idle(agent, state, outcome))
        if self._root_node is not None:
            updates.extend(self._close_cells(self._agents[self._root_node], reason))
        if crashed:
            updates.append(
                self._closing(texts.crashed(ev.exit_code, ev.detail or ""), "crashed")
            )
        else:
            updates.append(self._closing(texts.ROOT_STOPPED, ev.reason))
        updates.append(self.root_usage())
        return updates
