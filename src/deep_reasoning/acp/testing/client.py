"""An ACP client that records every update on one connection (§8.2)."""

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

import acp
import acp.client.connection
import acp.schema
from acp.utils import request_model
from pydantic import Field

T = TypeVar("T")

UNSTABLE_UPDATES = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)
DETAIL = 40


class Caps(acp.schema.ClientCapabilities):
    subagents: dict[str, Any] | None = None


class _InitializeWithCaps(acp.schema.InitializeRequest):
    """InitializeRequest typed with Caps, so subagents survives serialization."""

    client_capabilities: Caps | None = Field(default=None, alias="clientCapabilities")


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
        super().__init__(client, writer, reader)
        router = self._conn._handler

        async def handler(method: str, params: Any, is_notification: bool) -> Any:
            update = (params or {}).get("update") or {}
            if (
                method == "session/update"
                and update.get("sessionUpdate") in UNSTABLE_UPDATES
            ):
                return await client.unstable_update(params["sessionId"], update)
            return await router(method, params, is_notification)

        self._conn._handler = handler

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Caps | None = None,
        client_info: acp.schema.Implementation | None = None,
        **kwargs: Any,
    ) -> acp.schema.InitializeResponse:
        request = _InitializeWithCaps(
            protocol_version=protocol_version,
            client_capabilities=client_capabilities or Caps(),
            client_info=client_info,
            field_meta=kwargs or None,
        )
        return await request_model(
            self._conn, "initialize", request, acp.schema.InitializeResponse
        )


@dataclass
class Subagent:
    session_id: str  # "<run>-n<node>": what session/cancel takes
    parent_session_id: str  # the session it was announced on
    title: str  # the latest non-empty title
    state: Literal["running", "idle"]
    stop_reason: str | None  # the latest idle update's stopReason
    field_meta: dict[str, Any]  # the latest subagent_update's _meta, as sent


def outcome_phrase(meta: Mapping[str, Any] | None, node: int | None) -> str:
    """§8.2's outcome phrase from _meta.deep_reasoner of an idle update or closed card."""
    outcome = (meta or {}).get("deep_reasoner") or {}
    status = outcome.get("status")
    if status is None:
        return "running"
    if status == "failed":
        detail = " ".join((outcome.get("detail") or "").split())
        cut = detail if len(detail) <= DETAIL else f"{detail[: DETAIL - 1]}…"
        return f"failed: {cut}"
    if status == "stopped":
        by = outcome.get("stopped_by")
        if by is None or by == node:
            return "stopped"
        return (
            f"stopped with #{by}" if outcome.get("collateral") else f"stopped by #{by}"
        )
    return status


def first_text(content: Any) -> str:
    """The first text of an update's content: a block, or a list of (tool) contents."""
    items = content if isinstance(content, list) else [content]
    for item in items:
        inner = item.get("content", item) if isinstance(item, dict) else {}
        if isinstance(inner, dict) and inner.get("type") == "text":
            return inner["text"]
    return ""


class Printer:
    """An acp Client that records every update on one connection."""

    updates: list[tuple[str, dict[str, Any]]]  # (sessionId, the update as JSON)
    subagents: dict[str, Subagent]  # by full session id
    commands: dict[str, list[acp.schema.AvailableCommand]]  # root session id -> latest

    def __init__(self) -> None:
        self.updates = []
        self.subagents = {}
        self.commands = {}
        self._arrived = asyncio.Event()

    def _record(self, session_id: str, update: dict[str, Any]) -> None:
        self.updates.append((session_id, update))
        if update.get("sessionUpdate") == "subagent_update":
            self._record_subagent(session_id, update)
        self._arrived.set()

    def _record_subagent(self, parent_session_id: str, update: dict[str, Any]) -> None:
        session_id = update["sessionId"]
        state = update.get("state") or {}
        known = self.subagents.get(session_id)
        self.subagents[session_id] = Subagent(
            session_id=session_id,
            parent_session_id=parent_session_id,
            title=update.get("title") or (known.title if known else ""),
            state=state.get("state", "running"),
            stop_reason=state.get("stopReason"),
            field_meta=dict(update.get("_meta") or {}),
        )

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        """Stable updates, as the library's models."""
        if isinstance(update, acp.schema.AvailableCommandsUpdate):
            self.commands[session_id] = list(update.available_commands)
        dumped = update.model_dump(mode="json", by_alias=True, exclude_none=True)
        self._record(session_id, dumped)

    async def unstable_update(self, session_id: str, update: dict[str, Any]) -> None:
        """subagent_update, session_message, session_message_chunk, raw (ShimConnection)."""
        self._record(session_id, update)

    async def wait_until(
        self, predicate: Callable[["Printer"], T | None], *, timeout: float = 120.0
    ) -> T:
        """Return predicate(self)'s first result that is neither None nor False, checked
        now and after every recorded update. TimeoutError after timeout seconds."""
        async with asyncio.timeout(timeout):
            while True:
                self._arrived.clear()
                result = predicate(self)
                if result is not None and result is not False:
                    return result
                await self._arrived.wait()
