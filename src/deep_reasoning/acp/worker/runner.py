"""The worker: one deep_reasoner run, driven by control messages (§4.3).

python -m deep_reasoning.acp.worker --control-fd N --events-fd M
"""

from collections.abc import Sequence
from typing import Any


class RunKilled(BaseException):
    """Raised in the main thread by SIGTERM: the front ended the run."""


def as_text(value: Any) -> str:
    """value if it is a str, else its repr."""
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    """Read Start, then Prompts, until Close, a failure or SIGTERM; never returns
    normally once a run is built (teardown ends the process with os._exit)."""
    raise NotImplementedError
