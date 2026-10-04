"""The structlog processor that turns deep_reasoner's events into RunEvents (§6.1).

It runs on every thread that logs (the root on the main thread, sub-agents on _run_sync
worker threads), holds one lock for its state and its writes, returns the event dict
unchanged, and raises only StoppedByUser (§6.3).
"""

import ast
import json
import os
import re
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from deep_reasoner.v2.messages import NoCodeBlock, code

from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.worker.stop import StoppedByUser

TEXT_CAP = 8 * 1024 * 1024
FINAL_ANSWER = "FinalAnswer: "
BACKBONES = {"DeepReasoner": "chat", "ClaudeDeepReasoner": "claude_code"}
_REPL_BLOCK = re.compile(r"<repl>.*?(?:</repl>|$)", re.DOTALL)
_THINK_TAG = re.compile(r"</?think>")
_OBSERVATION = re.compile(r"\A<observation>\n?(.*?)\n?</observation>\Z", re.DOTALL)


def cap(text: str) -> str:
    """At most TEXT_CAP bytes: the head and the tail, the middle elided."""
    data = text.encode()
    if len(data) <= TEXT_CAP:
        return text
    half = TEXT_CAP // 2
    head = data[:half].decode(errors="ignore")
    tail = data[-half:].decode(errors="ignore")
    return f"{head}\n… {len(data) - TEXT_CAP} bytes elided …\n{tail}"


def source_of(reply: str) -> str | None:
    """The <repl> block deep_reasoner would run from this reply, if it has one."""
    try:
        return code(reply).source
    except NoCodeBlock:
        return None


def thought_of(reply: str) -> str:
    """The reply without its <repl> block and <think> tags."""
    return _THINK_TAG.sub("", _REPL_BLOCK.sub("", reply)).strip()


def unquote(answer_repr: str) -> str:
    """A FinalAnswer repr, unquoted when it is a Python string literal."""
    try:
        value = ast.literal_eval(answer_repr)
    except (ValueError, SyntaxError, MemoryError, RecursionError):
        return answer_repr
    return value if isinstance(value, str) else answer_repr


def final_answer_of(output: str) -> str | None:
    """The repr after the last line that starts with "FinalAnswer: ", to the end."""
    if output.startswith(FINAL_ANSWER):
        found = output
    else:
        at = output.rfind("\n" + FINAL_ANSWER)
        if at < 0:
            return None
        found = output[at + 1 :]
    return found[len(FINAL_ANSWER) :].rstrip("\n")


class EventSink:
    """The worker's end of the event pipe."""

    def __init__(self, fd: int) -> None:
        self._fd = fd

    def emit(self, ev: Mapping[str, Any]) -> None:
        """One JSON line, under the recorder's lock."""
        data = memoryview((json.dumps(ev, default=str) + "\n").encode())
        while data:
            data = data[os.write(self._fd, data) :]


@dataclass
class _Agent:
    node: int
    parent: int | None
    ancestry: tuple[int, ...]  # agent nodes, root first, ending in node
    backbone: str
    max_iter: int | None
    drive: int
    opened_in: tuple[int, int | None] | None  # (parent, parent's cell) of this drive
    started_at: int  # the recorder's clock when this drive started
    ended_at: int | None = None
    open_cell: int | None = None
    open_code: str = ""
    cells: int = 0
    answer: str | None = None  # the FinalAnswer repr this drive kept
    raised_for: int | None = None  # the target whose StoppedByUser this drive raised


@dataclass(frozen=True)
class _Target:
    node: int
    drive: int  # the target's drive when the stop was accepted
    mode: Literal["dean", "interim"]
    accepted_at: int


class Recorder:
    """Installed ahead of deep_reasoner's LogProcessor."""

    def __init__(self, sink: EventSink, prices: PriceTable) -> None:
        self._sink = sink
        self._prices = prices
        self._lock = threading.RLock()
        self._agents: dict[int, _Agent] = {}
        self._targets: dict[int, _Target] = {}
        self._clock = 0
        self._puppeteer: list[str] = []
        self._muted = False
        self._handlers: dict[str, Callable[[dict[str, Any]], None]] = {
            "agent.start": self._agent_start,
            "agent.turn": self._agent_turn,
            "agent.loop": self._agent_loop,
            "llm.call": self._llm_call,
            "claude.call": self._claude_call,
            "repl.execute": self._repl_execute,
            "agent.end": self._agent_end,
        }

    def __call__(
        self, logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        handler = self._handlers.get(str(event_dict.get("event")))
        if handler is not None:
            with self._lock:
                handler(event_dict)
        return event_dict

    def set_puppeteer(self, turns: Sequence[str]) -> None:
        """The main decomposition's turns, each opening one cell of the root's first drive."""
        with self._lock:
            self._puppeteer = list(turns)

    def note_stop(self, node: int, mode: Literal["dean", "interim"]) -> None:
        """Record a running agent as a stop target (§6.3), and emit stop.accepted saying
        whether it was one. An interim target's branch raises at its next agent.turn."""
        with self._lock:
            agent = self._agents.get(node)
            reason = None
            if agent is None:
                reason = "no such agent in this run"
            elif agent.ended_at is not None:
                reason = "the agent has already ended"
            else:
                self._clock += 1
                self._targets[node] = _Target(node, agent.drive, mode, self._clock)
            self.emit(
                "stop.accepted",
                node=node,
                mode=mode,
                accepted=reason is None,
                reason=reason,
                backbone=agent.backbone if agent else None,
            )

    def holding(self) -> threading.RLock:
        """The recorder's lock, for a step no event may interleave with."""
        return self._lock

    def running(self, node: int) -> bool:
        """The agent is known and its current drive has not ended."""
        with self._lock:
            agent = self._agents.get(node)
            return agent is not None and agent.ended_at is None

    def emit(self, kind: str, **fields: Any) -> None:
        """Send one RunEvent unless muted; under the lock, so lines from different
        threads never interleave."""
        with self._lock:
            if not self._muted:
                self._sink.emit({"kind": kind, **fields})

    def mute(self) -> None:
        """Send nothing more: the front is ending the run and describes its end itself."""
        with self._lock:
            self._muted = True

    # ── deep_reasoner's events ────────────────────────────────────────────────

    def _owner(self, event_dict: dict[str, Any]) -> _Agent | None:
        """The agent itself, else the deepest known agent in the event's ancestry."""
        node = event_dict.get("node_id")
        if node in self._agents:
            return self._agents[node]
        for ancestor in reversed(tuple(event_dict.get("ancestry") or ())):
            if ancestor in self._agents:
                return self._agents[ancestor]
        return None

    def _working_for(self, event_dict: dict[str, Any], kind: str) -> _Agent | None:
        """The agent itself; or, for a fork, the agent whose own LLM (kind llm) or REPL
        (kind repl) logs as a node directly under it, outside any cell of it."""
        if event_dict.get("kind") == "agent":
            return self._agents.get(event_dict.get("node_id"))
        ancestry = tuple(event_dict.get("ancestry") or ())
        parent = self._agents.get(ancestry[-2]) if len(ancestry) > 1 else None
        if event_dict.get("kind") != kind or parent is None:
            return None
        return parent if kind == "repl" or parent.open_cell is None else None

    def _open_cell(self, agent: _Agent, code_: str, origin: str) -> None:
        agent.cells += 1
        agent.open_cell, agent.open_code = agent.cells, code_
        self.emit(
            "cell.start",
            node=agent.node,
            cell=agent.cells,
            code=cap(code_),
            origin=origin,
        )

    def _close_cell(
        self, agent: _Agent, code_: str, output: str, interrupted: bool
    ) -> None:
        self.emit(
            "cell.end",
            node=agent.node,
            cell=agent.open_cell,
            code=cap(code_),
            output=cap(output),
            interrupted=interrupted,
        )
        agent.open_cell, agent.open_code = None, ""

    def _agent_start(self, event_dict: dict[str, Any]) -> None:
        node = event_dict["node_id"]
        ancestry = tuple(event_dict.get("ancestry") or (node,))
        agents = (*(a for a in ancestry[:-1] if a in self._agents), node)
        parent = self._agents.get(agents[-2]) if len(agents) > 1 else None
        if parent is not None and parent.open_cell is None:
            self._open_cell(parent, "", "inferred")
        self._clock += 1
        opened_in = (parent.node, parent.open_cell) if parent else None
        agent = self._agents.get(node)
        if agent is None:
            backbone = str(event_dict.get("backbone"))
            agent = _Agent(
                node=node,
                parent=parent.node if parent else None,
                ancestry=agents,
                backbone=BACKBONES.get(backbone, backbone),
                max_iter=event_dict.get("max_iter"),
                drive=1,
                opened_in=opened_in,
                started_at=self._clock,
            )
            self._agents[node] = agent
        else:
            agent.drive += 1
            agent.opened_in, agent.started_at, agent.ended_at = (
                opened_in,
                self._clock,
                None,
            )
            agent.answer, agent.raised_for = None, None
            agent.max_iter = event_dict.get("max_iter", agent.max_iter)
        self.emit(
            "agent.start",
            node=node,
            parent=agent.parent,
            ancestry=list(agent.ancestry),
            depth=len(agent.ancestry),
            task=cap(str(event_dict.get("task") or "")),
            namespace=event_dict.get("namespace") or "root",
            backbone=agent.backbone,
            max_iter=agent.max_iter,
            drive=agent.drive,
            parent_cell=opened_in[1] if opened_in else None,
            dr_run=event_dict.get("run"),
        )

    def _agent_turn(self, event_dict: dict[str, Any]) -> None:
        agent = self._agents.get(event_dict.get("node_id"))
        if agent is None:
            return
        self._raise_if_stopped(agent)
        if agent.parent is None and agent.drive == 1 and self._puppeteer:
            turn = self._puppeteer.pop(0)
            self._open_cell(agent, source_of(turn) or "", "puppeteered")

    def _agent_loop(self, event_dict: dict[str, Any]) -> None:
        agent = self._working_for(event_dict, "llm")
        if agent is None or agent.open_cell is not None:
            return
        messages = event_dict.get("messages") or [{}]
        reply = str(messages[-1].get("content") or "")
        if thought := thought_of(reply):
            self.emit("thought", node=agent.node, text=cap(thought))
        source = source_of(reply)
        if source is not None:
            self._open_cell(agent, source, "think")

    def _llm_call(self, event_dict: dict[str, Any]) -> None:
        owner = self._owner(event_dict)
        if owner is None:
            return
        model = event_dict.get("model")
        estimate = self._prices.estimate(model, event_dict.get("usage") or {})
        self.emit(
            "usage",
            node=owner.node,
            call="think" if self._working_for(event_dict, "llm") else "tool",
            model=model,
            tokens_in=estimate.tokens_in,
            tokens_out=estimate.tokens_out,
            cost_usd=estimate.usd,
            cost_source=estimate.source,
            context_window=estimate.context_window,
        )

    def _claude_call(self, event_dict: dict[str, Any]) -> None:
        owner = self._owner(event_dict)
        if owner is None:
            return
        usage = event_dict.get("usage") or {}
        cost = event_dict.get("cost_usd")
        self.emit(
            "usage",
            node=owner.node,
            call="claude",
            model=event_dict.get("model"),
            tokens_in=int(usage.get("input_tokens") or 0),
            tokens_out=int(usage.get("output_tokens") or 0),
            cost_usd=cost,
            cost_source="claude" if cost is not None else None,
            context_window=None,
        )
        if response := str(event_dict.get("response") or "").strip():
            self.emit("thought", node=owner.node, text=cap(response))

    def _repl_execute(self, event_dict: dict[str, Any]) -> None:
        agent = self._working_for(event_dict, "repl")
        if agent is None:
            return
        source = str(event_dict.get("source") or "")
        observation = str(event_dict.get("observation") or "")
        match = _OBSERVATION.match(observation)
        output = match.group(1) if match else observation
        if agent.open_cell is None:
            self._open_cell(agent, source, "inferred")
        self._close_cell(agent, source, output, interrupted=False)
        if (answer := final_answer_of(output)) is not None:
            agent.answer = answer

    def _agent_end(self, event_dict: dict[str, Any]) -> None:
        agent = self._agents.get(event_dict.get("node_id"))
        if agent is None:
            return
        if agent.open_cell is not None:
            self._close_cell(agent, agent.open_code, "", interrupted=True)
        self._clock += 1
        agent.ended_at = self._clock
        dr_status = str(event_dict.get("status"))
        detail = event_dict.get("detail")
        status, stopped_by, collateral = self._classify(agent, dr_status, detail or "")
        answer = None
        if status == "done" and agent.answer is not None:
            answer = unquote(agent.answer)
        elif status == "exhausted":
            answer = f"Agent failed to produce a final answer within {agent.max_iter} iterations."
        self.emit(
            "agent.end",
            node=agent.node,
            status=status,
            dr_status=dr_status,
            iter=event_dict.get("iter"),
            answer=cap(answer) if answer is not None else None,
            detail=cap(detail) if detail is not None else None,
            stopped_by=stopped_by,
            collateral=collateral,
        )

    # ── stop (§6.3) ───────────────────────────────────────────────────────────

    def _armed(self, target: _Target) -> bool:
        """A target stays armed until a new drive of it starts; ending does not disarm."""
        return self._agents[target.node].drive == target.drive

    def _nearest_target(self, agent: _Agent) -> _Target | None:
        for node in reversed(agent.ancestry):
            target = self._targets.get(node)
            if target is not None and self._armed(target):
                return target
        return None

    def _branch(self, target: _Target) -> tuple[int, ...]:
        """Every other agent under the target running when it was accepted, or since."""
        return tuple(
            sorted(
                a.node
                for a in self._agents.values()
                if a.node != target.node
                and target.node in a.ancestry
                and (a.ended_at is None or a.ended_at > target.accepted_at)
            )
        )

    def _siblings(self, target: _Target) -> tuple[int, ...]:
        """The other agents running now that were opened in the target's parent cell."""
        opened_in = self._agents[target.node].opened_in
        return tuple(
            sorted(
                a.node
                for a in self._agents.values()
                if a.node != target.node
                and a.ended_at is None
                and a.opened_in == opened_in
            )
        )

    def _raise_if_stopped(self, agent: _Agent) -> None:
        """Interim: an armed target at the agent or above it ends this drive now."""
        target = self._nearest_target(agent)
        if target is None or target.mode != "interim":
            return
        siblings = self._siblings(target) if agent.node == target.node else ()
        agent.raised_for = target.node
        raise StoppedByUser(target.node, self._branch(target), siblings)

    def _classify(
        self, agent: _Agent, dr_status: str, detail: str
    ) -> tuple[str, int | None, bool]:
        """(status, stopped_by, collateral), by §6.3's table."""
        nearest = self._nearest_target(agent)
        if dr_status == "stopped":
            return "stopped", nearest.node if nearest else None, False
        if dr_status != "failed":
            return dr_status, None, False
        if detail.startswith("StoppedByUser"):
            return (
                "stopped",
                agent.raised_for or (nearest.node if nearest else None),
                False,
            )
        if detail.startswith("CancelledError"):
            if nearest is not None:
                return "stopped", nearest.node, False
            for target in self._targets.values():
                beside = self._agents[target.node].opened_in == agent.opened_in
                if self._armed(target) and beside and target.node != agent.node:
                    return "stopped", target.node, True
        return "failed", None, False
