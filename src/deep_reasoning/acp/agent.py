"""DrAcpAgent: the ACP methods (§4.2, §5.5). Handlers return raw dicts."""

from typing import Any

from deep_reasoning.acp.catalog import Catalog
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.route import ModelRoute
from deep_reasoning.acp.runlog import Home
from deep_reasoning.acp.wire import ClientMode, Outbox


class DrAcpAgent:
    def __init__(
        self,
        outbox: Outbox,
        client: ClientMode,
        *,
        catalog: Catalog,
        home: Home,
        route: ModelRoute,
        prices: PriceTable,
        heartbeat_s: float,
    ) -> None: ...

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Any = None,
        client_info: Any = None,
        **meta: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def load_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def set_config_option(
        self, config_id: str, session_id: str, value: str, **meta: Any
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def prompt(
        self, prompt: list[Any], session_id: str, **meta: Any
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def cancel(self, session_id: str, **meta: Any) -> None:
        """A root session id stops the run; a live child's id stops its branch."""
        raise NotImplementedError

    async def close_session(self, session_id: str, **meta: Any) -> dict[str, Any]:
        raise NotImplementedError

    async def close_all(self, grace_s: float) -> None:
        """Shutdown: close every session's live run concurrently."""
        raise NotImplementedError
