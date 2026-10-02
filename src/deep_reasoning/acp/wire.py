"""The connection, the initialize tap and the single send path (§4.2)."""

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

import acp.connection

from deep_reasoning.acp.runlog import Mode

if TYPE_CHECKING:
    from deep_reasoning.acp.agent import DrAcpAgent

READER_LIMIT = 64 * 1024 * 1024


class ClientMode:
    """Decided once per connection, by the tap, before the router sees initialize."""

    def __init__(self, *, flat: bool = False) -> None: ...

    mode: Mode  # "native" iff clientCapabilities.subagents is an object and not --flat

    def decide(self, initialize_params: Any) -> None:
        raise NotImplementedError


class Outbox:
    """Every byte dr-acp sends to the client goes through here, in call order."""

    def __init__(self, conn: acp.connection.Connection) -> None: ...

    async def update(self, session_id: str, update: Mapping[str, Any]) -> None:
        """A session/update notification, raw JSON: {"sessionId": ..., "update": update}.
        Dropped once the client has closed the pipe."""
        raise NotImplementedError

    def observe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """fn sees every outgoing JSON-RPC message (tests, golden recording)."""
        raise NotImplementedError

    @property
    def seconds_since_last_send(self) -> float:
        raise NotImplementedError


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
    raise NotImplementedError
