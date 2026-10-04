"""deep_reasoner's events -> RunEvents (§6.1).

The worker feeds it the events of each drive on its main loop; a Stop comes from the
control reader's thread. One lock covers its state and its writes.
"""

import json
import os
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.worker._upstream_standin import (
    AgentEnded,
    AgentStarted,
    CellEnded,
    CellStarted,
    ModelCalled,
    Thought,
)

TEXT_CAP = 8 * 1024 * 1024
ORIGINS = {"think": "think", "scripted": "puppeteered"}


def cap(text: str) -> str:
    """At most TEXT_CAP bytes: the head and the tail, the middle elided."""
    data = text.encode()
    if len(data) <= TEXT_CAP:
        return text
    half = TEXT_CAP // 2
    head = data[:half].decode(errors="ignore")
    tail = data[-half:].decode(errors="ignore")
    return f"{head}\n… {len(data) - TEXT_CAP} bytes elided …\n{tail}"


def as_text(value: Any) -> str:
    """value if it is a str, else its repr."""
    return value if isinstance(value, str) else repr(value)


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
    ancestry: tuple[int, ...]  # agent nodes, root first, ending in this one
    backbone: str
    drive: int = 1


class Recorder:
    def __init__(self, sink: EventSink, prices: PriceTable) -> None:
        self._sink = sink
        self._prices = prices
        self._lock = threading.RLock()
        self._agents: dict[int, _Agent] = {}
        self._muted = False

    def feed(self, ev: Any) -> None:
        with self._lock:
            match ev:
                case AgentStarted():
                    self._agent_start(ev)
                case ModelCalled():
                    self._model_called(ev)
                case Thought():
                    self.emit("thought", node=ev.node_id, text=cap(ev.text))
                case CellStarted():
                    origin = ORIGINS[ev.origin]
                    code = cap(ev.source)
                    self.emit(
                        "cell.start",
                        node=ev.node_id,
                        cell=ev.cell,
                        code=code,
                        origin=origin,
                    )
                case CellEnded():
                    self.emit(
                        "cell.end",
                        node=ev.node_id,
                        cell=ev.cell,
                        code=cap(ev.source),
                        output=cap(ev.output),
                        interrupted=ev.interrupted,
                    )
                case AgentEnded():
                    self._agent_end(ev)

    def stop(self, node: int, reasoner: Any) -> None:
        """deep_reasoner's stop(node), then stop.accepted saying whether it took, as one
        step: no event is written between the two."""
        with self._lock:
            agent = self._agents.get(node)
            accepted = reasoner is not None and reasoner.stop(node)
            reason = None
            if not accepted:
                reason = (
                    "no such agent in this run"
                    if agent is None
                    else "the agent has already ended"
                )
            self.emit(
                "stop.accepted",
                node=node,
                mode="dean",
                accepted=accepted,
                reason=reason,
                backbone=agent.backbone if agent else None,
            )

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

    def _agent_start(self, ev: AgentStarted) -> None:
        agent = self._agents.get(ev.node_id)
        if agent is None:
            parent = (
                self._agents.get(ev.parent_id) if ev.parent_id is not None else None
            )
            ancestry = (*(parent.ancestry if parent else ()), ev.node_id)
            agent = self._agents[ev.node_id] = _Agent(ancestry, ev.backbone)
        else:
            agent.drive += 1
        self.emit(
            "agent.start",
            node=ev.node_id,
            parent=ev.parent_id,
            ancestry=list(agent.ancestry),
            depth=len(agent.ancestry),
            task=cap(ev.task),
            namespace=ev.namespace,
            backbone=agent.backbone,
            max_iter=ev.max_iter,
            drive=agent.drive,
            parent_cell=ev.parent_cell,
            dr_run=ev.run,
        )

    def _model_called(self, ev: ModelCalled) -> None:
        estimate = self._prices.estimate(ev.model, ev.usage)
        claude = ev.call == "claude"
        self.emit(
            "usage",
            node=ev.node_id,
            call=ev.call,
            model=ev.model,
            tokens_in=estimate.tokens_in,
            tokens_out=estimate.tokens_out,
            cost_usd=ev.cost_usd if claude else estimate.usd,
            cost_source=("claude" if ev.cost_usd is not None else None)
            if claude
            else estimate.source,
            context_window=None if claude else estimate.context_window,
        )

    def _agent_end(self, ev: AgentEnded) -> None:
        answered = ev.status in ("done", "exhausted")
        self.emit(
            "agent.end",
            node=ev.node_id,
            status=ev.status,
            dr_status=ev.status,
            iter=ev.iter,
            answer=cap(as_text(ev.answer)) if answered else None,
            detail=cap(ev.detail) if ev.detail is not None else None,
            stopped_by=ev.stopped_by,
            collateral=False,
        )
