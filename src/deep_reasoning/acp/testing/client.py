"""An ACP client that records every update on one connection (§8.2)."""

import asyncio
import textwrap
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

import acp
import acp.client.connection
import acp.schema
from acp.utils import request_model
from pydantic import Field

from deep_reasoning.acp import ids

T = TypeVar("T")

UNSTABLE_UPDATES = frozenset(
    {"subagent_update", "session_message", "session_message_chunk"}
)
MESSAGES = ("agent_message_chunk", "user_message_chunk")
BODY_COLUMN = 28
WRAP = 72
FIELD = 60
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
    short: str  # "n<node>"
    parent_session_id: str  # the session it was announced on
    title: str  # the latest non-empty title
    state: Literal["running", "idle"]
    stop_reason: str | None  # the latest idle update's stopReason
    field_meta: dict[str, Any]  # the latest subagent_update's _meta, as sent


class SubagentMap(Mapping[str, Subagent]):
    """Keyed by full session id. A short id ("n2") is also accepted when exactly one
    recorded sub-agent has it; when several do (one per run), KeyError names them."""

    def __init__(self) -> None:
        self._by_id: dict[str, Subagent] = {}

    def __getitem__(self, key: str) -> Subagent:
        if key in self._by_id:
            return self._by_id[key]
        found = [a for a in self._by_id.values() if a.short == key]
        if len(found) > 1:
            named = ", ".join(a.session_id for a in found)
            raise KeyError(f"{key!r} names several sub-agents: {named}")
        if not found:
            raise KeyError(key)
        return found[0]

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_id)

    def __len__(self) -> int:
        return len(self._by_id)

    def record(self, parent_session_id: str, update: Mapping[str, Any]) -> None:
        session_id = update["sessionId"]
        state = update.get("state") or {}
        known = self._by_id.get(session_id)
        self._by_id[session_id] = Subagent(
            session_id=session_id,
            short=ids.short(session_id),
            parent_session_id=parent_session_id,
            title=update.get("title") or (known.title if known else ""),
            state=state.get("state", "running"),
            stop_reason=state.get("stopReason"),
            field_meta=dict(update.get("_meta") or {}),
        )


def outcome_phrase(meta: Mapping[str, Any] | None, node: int | None) -> str:
    """§8.2's outcome phrase from _meta.deep_reasoner of an idle update or closed card."""
    outcome = (meta or {}).get("deep_reasoner") or {}
    status = outcome.get("status")
    if status is None:
        return "running"
    if status == "failed":
        return f"failed: {field(outcome.get('detail') or '', DETAIL)}"
    if status == "stopped":
        by = outcome.get("stopped_by")
        if by is None or by == node:
            return "stopped"
        return (
            f"stopped with #{by}" if outcome.get("collateral") else f"stopped by #{by}"
        )
    return status


def field(text: str, width: int = FIELD, *, output: bool = False) -> str:
    """One line, cut to width with "…" as the last character; output: the last non-empty
    line, else every run of whitespace turned into one space."""
    if output:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = lines[-1] if lines else ""
    else:
        text = " ".join(text.split())
    return text if len(text) <= width else f"{text[: width - 1]}…"


def first_text(content: Any) -> str:
    """The first text of an update's content: a block, or a list of (tool) contents."""
    items = content if isinstance(content, list) else [content]
    for item in items:
        inner = item.get("content", item) if isinstance(item, dict) else {}
        if isinstance(inner, dict) and inner.get("type") == "text":
            return inner["text"]
    return ""


def _wrapped(text: str) -> list[str]:
    pieces: list[str] = []
    for paragraph in text.rstrip().split("\n"):
        pieces.extend(textwrap.wrap(paragraph, WRAP) or [""])
    return pieces


def _body(kind: str, update: Mapping[str, Any]) -> str:
    if kind == "agent_thought_chunk":
        return field(first_text(update.get("content")))
    if kind == "tool_call":
        call = ids.short(update["toolCallId"])
        return f"{call} {update.get('kind') or '':<7}  {field(update.get('title', ''))}"
    if kind == "tool_call_update":
        output = field(first_text(update.get("content") or []), output=True)
        head = f"{ids.short(update['toolCallId'])} {update.get('status', '')}"
        return f"{head}  {output}" if output else head
    if kind == "subagent_update":
        return _subagent_body(update)
    if kind == "session_message":
        recipient = ids.short(update["recipientSessionId"])
        return f"→ {recipient}  '{field(first_text(update.get('content')))}'"
    if kind == "usage_update":
        cost = update.get("cost")
        return f"{cost['amount']:.4f} {cost['currency']}" if cost else "cost unknown"
    if kind == "available_commands_update":
        return repr([c["name"] for c in update.get("availableCommands", [])])
    if kind == "config_option_update":
        return ", ".join(_option(o) for o in update.get("configOptions", []))
    return ""


def _subagent_body(update: Mapping[str, Any]) -> str:
    who = ids.short(update["sessionId"])
    state = update.get("state") or {}
    if state.get("state") != "idle":
        return f"{who}  '{field(update.get('title') or '')}'  running"
    body = f"{who}  idle"
    if reason := state.get("stopReason"):
        body += f" {reason}"
    node = ((update.get("_meta") or {}).get("deep_reasoner") or {}).get("node")
    phrase = outcome_phrase(update.get("_meta"), node)
    if phrase not in ("done", "exhausted", "running"):
        body += f"  ({phrase})"
    return body


def _option(option: Mapping[str, Any]) -> str:
    values = [o.get("value") for o in option.get("options") or []]
    fixed = " (fixed)" if values == [option.get("currentValue")] else ""
    return f"{option.get('id')} = {option.get('currentValue')}{fixed}"


def line(session_id: str, update: Mapping[str, Any]) -> str:
    """One update in §8.2's line format."""
    kind = update.get("sessionUpdate", "")
    head = f"{ids.short(session_id):<9}{kind.removesuffix('_chunk'):<17}  "
    if kind in MESSAGES:
        indent = "\n" + " " * BODY_COLUMN
        return head + indent.join(_wrapped(first_text(update.get("content"))))
    return (head + _body(kind, update)).rstrip()


class Printer:
    """An acp Client that records every update on one connection. It never prints by
    itself: show() prints from the calling cell."""

    updates: list[tuple[str, dict[str, Any]]]  # (sessionId, the update as JSON)
    lines: list[str]  # one per update
    subagents: SubagentMap
    commands: dict[str, list[acp.schema.AvailableCommand]]  # root session id -> latest

    def __init__(self) -> None:
        self.updates = []
        self.lines = []
        self.subagents = SubagentMap()
        self.commands = {}
        self._shown = 0
        self._arrived = asyncio.Event()

    def _record(self, session_id: str, update: dict[str, Any]) -> None:
        self.updates.append((session_id, update))
        self.lines.append(line(session_id, update))
        if update.get("sessionUpdate") == "subagent_update":
            self.subagents.record(session_id, update)
        self._arrived.set()

    async def session_update(self, session_id: str, update: Any, **kwargs: Any) -> None:
        """Stable updates, as the library's models."""
        if isinstance(update, acp.schema.AvailableCommandsUpdate):
            self.commands[session_id] = list(update.available_commands)
        dumped = update.model_dump(mode="json", by_alias=True, exclude_none=True)
        self._record(session_id, dumped)

    async def unstable_update(self, session_id: str, update: dict[str, Any]) -> None:
        """subagent_update, session_message, session_message_chunk, raw (ShimConnection)."""
        self._record(session_id, update)

    def show(self) -> None:
        """Print the lines recorded since the previous show(); all of them the first time."""
        for recorded in self.lines[self._shown :]:
            print(recorded)
        self._shown = len(self.lines)

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
