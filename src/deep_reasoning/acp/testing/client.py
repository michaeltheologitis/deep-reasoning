"""An ACP client that records every update on one connection (§8.2)."""

import asyncio
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

import acp
import acp.client.connection
import acp.schema

T = TypeVar("T")

UNSTABLE_UPDATES = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)


class Caps(acp.schema.ClientCapabilities):
    subagents: dict[str, Any] | None = None


class ShimConnection(acp.client.connection.ClientSideConnection):
    """A ClientSideConnection that hands UNSTABLE_UPDATES to client.unstable_update ahead
    of the library's router, and sends initialize typed with Caps so that subagents
    reaches the wire (0.12.1 drops both, P5, P7)."""

    def __init__(
        self,
        client: "Printer",
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
    ) -> None:
        raise NotImplementedError

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Caps | None = None,
        client_info: acp.schema.Implementation | None = None,
        **kwargs: Any,
    ) -> acp.schema.InitializeResponse:
        raise NotImplementedError


@dataclass
class Subagent:
    session_id: str  # "<run>-n<node>": what session/cancel takes
    short: str  # "n<node>"
    parent_session_id: str  # the session it was announced on
    title: str  # the latest non-empty title
    state: Literal["running", "idle"]
    stop_reason: str | None  # the latest idle update's stopReason
    field_meta: dict[str, Any]  # the latest subagent_update's _meta, as sent


class SubagentMap(Mapping[str, Subagent]):
    """Keyed by full session id. A short id ("n2") is also accepted when exactly one
    recorded sub-agent has it; when several do (one per run), KeyError names them."""

    def __getitem__(self, key: str) -> Subagent:
        raise NotImplementedError

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


def outcome_phrase(meta: Mapping[str, Any] | None, node: int | None) -> str:
    """§8.2's outcome phrase from _meta.deep_reasoner of an idle update or closed card."""
    raise NotImplementedError


def field(text: str, width: int = 60, *, output: bool = False) -> str:
    """One line, cut to width with "…" as the last character; output: the last non-empty
    line, else every run of whitespace turned into one space."""
    raise NotImplementedError


def line(session_id: str, update: Mapping[str, Any]) -> str:
    """One update in §8.2's line format."""
    raise NotImplementedError


class Printer:
    """An acp Client that records every update on one connection. It never prints by
    itself: show() prints from the calling cell."""

    updates: list[tuple[str, dict[str, Any]]]  # (sessionId, the update as JSON)
    lines: list[str]  # one per update
    subagents: SubagentMap
    commands: dict[str, list[acp.schema.AvailableCommand]]  # root session id -> latest

    def __init__(self) -> None:
        raise NotImplementedError

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        """Stable updates, as the library's models."""
        raise NotImplementedError

    async def unstable_update(self, session_id: str, update: dict[str, Any]) -> None:
        """subagent_update, session_message, session_message_chunk, raw (ShimConnection)."""
        raise NotImplementedError

    def show(self) -> None:
        """Print the lines recorded since the previous show(); all of them the first time."""
        raise NotImplementedError

    async def wait_until(
        self, predicate: Callable[["Printer"], T | None], *, timeout: float = 120.0
    ) -> T:
        """Return predicate(self)'s first result that is neither None nor False, checked
        now and after every recorded update. TimeoutError after timeout seconds."""
        raise NotImplementedError
