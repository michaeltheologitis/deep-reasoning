"""The connection, the initialize tap and the single send path (§4.2)."""

import asyncio
import os
import signal
import time
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

import structlog
from acp.agent.router import build_agent_router
from acp.connection import Connection, StreamDirection, StreamEvent

from deep_reasoning.acp.runlog import Mode

if TYPE_CHECKING:
    from deep_reasoning.acp.agent import DrAcpAgent

logger = structlog.get_logger(__name__)

READER_LIMIT = 64 * 1024 * 1024


class ClientMode:
    """Decided once per connection, by the tap, before the router sees initialize."""

    mode: Mode  # "native" iff clientCapabilities.subagents is an object and not --flat

    def __init__(self, *, flat: bool = False) -> None:
        self._flat = flat
        self.mode = "flat"

    def decide(self, initialize_params: Any) -> None:
        """Read subagents from the raw params: ACP Python 0.12.1's model drops it."""
        capabilities = (initialize_params or {}).get("clientCapabilities") or {}
        native = isinstance(capabilities.get("subagents"), dict) and not self._flat
        self.mode = "native" if native else "flat"


class Outbox:
    """Every byte dr-acp sends to the client goes through here, in call order."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn
        self._last_send = time.monotonic()
        conn.add_observer(self._sent)

    def _sent(self, event: StreamEvent) -> None:
        if event.direction is StreamDirection.OUTGOING:
            self._last_send = time.monotonic()

    async def update(self, session_id: str, update: Mapping[str, Any]) -> None:
        """A session/update notification, raw JSON: {"sessionId": ..., "update": update}.
        Dropped once the client has closed the pipe: the run log still has it."""
        params = {"sessionId": session_id, "update": dict(update)}
        try:
            await self._conn.send_notification("session/update", params)
        except (ConnectionError, OSError):
            logger.debug("dr_acp.update_dropped", session=session_id)

    def observe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """fn sees every outgoing JSON-RPC message (tests, golden recording)."""

        def outgoing(event: StreamEvent) -> None:
            if event.direction is StreamDirection.OUTGOING:
                fn(event.message)

        self._conn.add_observer(outgoing)

    @property
    def seconds_since_last_send(self) -> float:
        return time.monotonic() - self._last_send


async def _stdio_streams(
    stdin_fd: int, acp_out_fd: int
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader(limit=READER_LIMIT)
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader), os.fdopen(stdin_fd, "rb", 0)
    )
    transport, protocol = await loop.connect_write_pipe(
        lambda: asyncio.StreamReaderProtocol(asyncio.StreamReader()),
        os.fdopen(acp_out_fd, "wb", 0),
    )
    return reader, asyncio.StreamWriter(transport, protocol, None, loop)


async def serve(
    make_agent: "Callable[[Outbox, ClientMode], DrAcpAgent]",
    *,
    acp_out_fd: int,
    stdin_fd: int = 0,
    flat: bool = False,
    shutdown_grace_s: float = 0.3,
) -> None:
    """Serve one ACP connection until the client closes stdin or SIGTERM arrives, then
    close every live run (shutdown_grace_s each, concurrently).

    Builds asyncio streams on (stdin_fd, acp_out_fd) with a 64 MiB reader limit, then
    Connection(handler, writer, reader), where handler is the initialize tap in front of
    build_agent_router(agent, use_unstable_protocol=True).
    """
    reader, writer = await _stdio_streams(stdin_fd, acp_out_fd)
    client = ClientMode(flat=flat)
    router = None

    async def handler(method: str, params: Any, is_notification: bool) -> Any:
        if method == "initialize":
            client.decide(params)
        return await router(method, params, is_notification)

    conn = Connection(handler, writer, reader, listening=False)
    agent = make_agent(Outbox(conn), client)
    router = build_agent_router(agent, use_unstable_protocol=True)
    receiving = asyncio.ensure_future(conn.main_loop())
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, receiving.cancel)
    try:
        await receiving
    except asyncio.CancelledError:
        logger.info("dr_acp.sigterm")
    await agent.close_all(grace_s=shutdown_grace_s)
    await conn.close()
