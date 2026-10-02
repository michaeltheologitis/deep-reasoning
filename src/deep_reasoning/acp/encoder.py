"""RunEvents -> ACP session updates (§5.2 native, §5.3 flat, §5.7 replay).

Pure: no I/O, no clock. One Encoder per run, and one per run in a replay.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from deep_reasoning.acp.catalog import CatalogSnapshot, CommandEntry
from deep_reasoning.acp.costs import NO_COST, CostLedger
from deep_reasoning.acp.runlog import Mode, RunEvent

# (sessionId, the "update" object of a session/update notification)
Update = tuple[str, dict[str, Any]]


@dataclass(frozen=True)
class ChildRef:
    node: int
    running: bool


class Encoder:
    def __init__(
        self,
        *,
        root: str,
        run: str,
        mode: Mode,
        replay: bool = False,
        carry: CostLedger = NO_COST,
    ) -> None: ...

    def feed(self, ev: RunEvent) -> list[Update]:
        """The updates one RunEvent produces: §5.2 (native), §5.3 (flat)."""
        raise NotImplementedError

    def flush_usage(self) -> list[Update]:
        """A usage_update for each session whose totals changed since the last flush."""
        raise NotImplementedError

    def root_usage(self) -> Update:
        """The root's usage_update, always."""
        raise NotImplementedError

    def child(self, session_id: str) -> ChildRef | None:
        raise NotImplementedError

    @property
    def prompt_in_flight(self) -> bool:
        """A prompt.start was fed and neither its prompt.end nor a run.end yet."""
        raise NotImplementedError

    @property
    def root_cost(self) -> CostLedger:
        """carry plus this run's root total."""
        raise NotImplementedError


def closing_message(
    root: str, text: str, *, run: str | None, prompt: int | None, outcome: str
) -> Update:
    """§5.2's CM: the root agent_message_chunk that ends a turn or a run."""
    raise NotImplementedError


def idle_root_usage(root: str, cost: CostLedger) -> Update:
    """The root's usage_update while no run is live: the conversation's cost so far."""
    raise NotImplementedError


def commands_update(
    root: str, commands: Sequence[CommandEntry], namespace: str
) -> Update:
    """available_commands_update for a namespace's menu (§5.5's command shape)."""
    raise NotImplementedError


def namespace_option(
    snapshot: CatalogSnapshot, namespace: str, *, fixed: bool
) -> dict[str, Any]:
    """The namespace select option (§5.5); fixed: only the current value is offered."""
    raise NotImplementedError


def config_update(root: str, options: list[dict[str, Any]]) -> Update:
    """config_option_update carrying the full options."""
    raise NotImplementedError
