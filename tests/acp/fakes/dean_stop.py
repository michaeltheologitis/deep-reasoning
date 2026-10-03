"""A fake of Dean's stop(node_id) (§6.3), for tests only: DR_ACP_STOP_API names
tests.acp.fakes.dean_stop:stop and the worker imports it.

Importing it wraps DeepReasonerAgentBase so that a node in a stopped branch raises a
private BaseException at its next agent.turn, logs its agent.end as stopped, and answers
a Stopped marker instead of raising: points 1-6 of the contract on d7334ae.
"""

import threading
from dataclasses import dataclass
from typing import Any

from deep_reasoner.v2.agent import DeepReasonerAgentBase

_stopped: set[int] = set()
_lock = threading.Lock()


class _Stop(BaseException):
    """Unwinds one stopped drive; never reaches a cell."""


@dataclass(frozen=True)
class Stopped:
    node: int


def stop(node_id: int) -> None:
    with _lock:
        _stopped.add(node_id)


def _node(agent: DeepReasonerAgentBase) -> tuple[int, tuple[int, ...]]:
    values = agent._node[1]
    return values["node_id"], tuple(values["ancestry"])


_note_drive = DeepReasonerAgentBase._note_drive
_anext = DeepReasonerAgentBase.__anext__


def _stopping_note_drive(
    self: DeepReasonerAgentBase, event: str, **fields: Any
) -> None:
    node, ancestry = _node(self)
    with _lock:
        in_stopped_branch = bool(_stopped & set(ancestry))
    if event == "agent.turn" and in_stopped_branch:
        raise _Stop(node)
    if event == "agent.end" and str(fields.get("detail", "")).startswith("_Stop"):
        fields = {k: v for k, v in fields.items() if k != "detail"} | {
            "status": "stopped"
        }
    _note_drive(self, event, **fields)


async def _stoppable_anext(self: DeepReasonerAgentBase) -> Any:
    try:
        return await _anext(self)
    except _Stop:
        self._done = True
        self.final_answer = Stopped(_node(self)[0])
        return self.final_answer


DeepReasonerAgentBase._note_drive = _stopping_note_drive
DeepReasonerAgentBase.__anext__ = _stoppable_anext
