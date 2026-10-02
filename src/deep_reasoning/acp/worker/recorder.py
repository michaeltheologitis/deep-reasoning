"""The structlog processor that turns deep_reasoner's events into RunEvents (§6.1)."""

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.worker.stop import StopReceipt


class EventSink:
    """The worker's end of the event pipe."""

    def __init__(self, fd: int) -> None: ...

    def emit(self, ev: Mapping[str, Any]) -> None:
        """One JSON line, under the recorder's lock."""
        raise NotImplementedError


class Recorder:
    """Installed ahead of deep_reasoner's LogProcessor; runs on every thread that logs,
    returns the event dict unchanged and raises only StoppedByUser (§6.3)."""

    def __init__(self, sink: EventSink, prices: PriceTable) -> None: ...

    def __call__(
        self, logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError

    def set_puppeteer(self, turns: Sequence[str]) -> None:
        """The main decomposition's turns, each opening one cell of the root's first drive."""
        raise NotImplementedError

    def note_stop(self, node: int, mode: Literal["dean", "interim"]) -> StopReceipt:
        """Record an accepted target (§6.3) and emit stop.accepted."""
        raise NotImplementedError

    def arm(self, node: int) -> StopReceipt:
        """Interim: note_stop(node, "interim"); the target now raises at agent.turn."""
        raise NotImplementedError

    def emit(self, kind: str, **fields: Any) -> None:
        """The runner's own events: worker.ready, prompt.end."""
        raise NotImplementedError
