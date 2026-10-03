"""Stopping one agent's branch: Dean's stop(node_id), or the interim until he ships it
(§6.3)."""

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, Protocol

from deep_reasoning.acp import texts

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
        super().__init__(texts.stopped_by_user(target, branch, siblings))
        self.target = target
        self.branch = branch
        self.siblings = siblings


class StopAdapter(Protocol):
    mode: Literal["dean", "interim"]

    def stop(self, node_id: int) -> None:
        """Thread-safe; returns at once. Whether the stop was accepted is the
        stop.accepted event the recorder emits."""
        ...


class DeanStop:
    """The one place dr-acp calls deep_reasoner's stop."""

    mode: Literal["dean"] = "dean"

    def __init__(self, fn: Callable[[int], None], recorder: "Recorder") -> None:
        self._fn = fn
        self._recorder = recorder

    def stop(self, node_id: int) -> None:
        """fn(node_id), then recorder.note_stop(node_id, "dean"), as one step for the
        recorder: stop.accepted marks the moment the stop is in force, and no agent.end
        is classified between the two."""
        with self._recorder.holding():
            if self._recorder.running(node_id):
                self._fn(node_id)
            self._recorder.note_stop(node_id, "dean")


class InterimStop:
    mode: Literal["interim"] = "interim"

    def __init__(self, recorder: "Recorder") -> None:
        self._recorder = recorder

    def stop(self, node_id: int) -> None:
        self._recorder.note_stop(node_id, "interim")


def resolve_stop_adapter(recorder: "Recorder", spec: str | None) -> StopAdapter:
    """DeanStop over the function spec names ("module:attr"), else InterimStop."""
    if not spec:
        return InterimStop(recorder)
    module, attr = spec.split(":")
    return DeanStop(getattr(importlib.import_module(module), attr), recorder)
