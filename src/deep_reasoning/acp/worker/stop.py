"""Stopping one agent's branch: Dean's stop(node_id), or the interim until he ships it
(§6.3)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from deep_reasoning.acp.worker.recorder import Recorder

# "module:attr" of Dean's stop(node_id), set when he ships it. DR_ACP_STOP_API overrides
# it (the tests point it at the fake). None means the interim.
DEAN_STOP_API: str | None = None


class StoppedByUser(Exception):
    """Interim only. An Exception, so the parent's cell catches it.

    Cells catch Exception (repls/backends.py:523, v2/repl_coro.py:84). The message is
    §5.6's StoppedByUser sentence.
    """

    def __init__(
        self, target: int, branch: tuple[int, ...], siblings: tuple[int, ...]
    ) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class StopReceipt:
    node: int
    mode: Literal["dean", "interim"]
    accepted: bool  # False: unknown node, or it already ended
    reason: str | None


class StopAdapter(Protocol):
    mode: Literal["dean", "interim"]

    def stop(self, node_id: int) -> StopReceipt:
        """Thread-safe; returns at once."""
        ...


class DeanStop:
    """The one place dr-acp calls deep_reasoner's stop."""

    mode: Literal["dean"] = "dean"

    def __init__(self, fn: Callable[[int], None], recorder: "Recorder") -> None: ...

    def stop(self, node_id: int) -> StopReceipt:
        """recorder.note_stop(node_id, "dean"), then fn(node_id)."""
        raise NotImplementedError


class InterimStop:
    mode: Literal["interim"] = "interim"

    def __init__(self, recorder: "Recorder") -> None: ...

    def stop(self, node_id: int) -> StopReceipt:
        """recorder.arm(node_id)."""
        raise NotImplementedError


def resolve_stop_adapter(recorder: "Recorder", spec: str | None) -> StopAdapter:
    """DeanStop over the function spec names ("module:attr"), else InterimStop."""
    raise NotImplementedError
