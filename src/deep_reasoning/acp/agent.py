"""DrAcpAgent: the ACP methods (§4.2, §5.5). Handlers return raw dicts."""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any

import structlog

from deep_reasoning.acp import __version__, ids, texts
from deep_reasoning.acp.catalog import Catalog, CatalogSnapshot
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.route import ModelRoute
from deep_reasoning.acp.runlog import Home, SessionIndex, detail_of
from deep_reasoning.acp.session import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    AgentContext,
    Session,
    refusal,
)
from deep_reasoning.acp.wire import ClientMode, Outbox

logger = structlog.get_logger(__name__)

PROTOCOL_VERSION = 1
SESSION_CLOSE_GRACE_S = 2.0
AGENT_CAPABILITIES = {
    "loadSession": True,
    "promptCapabilities": {"image": False, "audio": False, "embeddedContext": False},
    "mcpCapabilities": {"http": True, "sse": True},
    "sessionCapabilities": {"close": {}},
}


def user_text(blocks: list[Any]) -> tuple[str, list[str]]:
    """The user's own text, and the text blocks dropped from it.

    The user's text is the first text block; each resource link adds its uri on a line
    of its own. OpenHands' bridge sends the user's message as one text block, then its
    images, then the turn's extensions and, on the first prompt, its system suffix, each
    a text block of its own (_build_acp_prompt): every later text block is the client's
    context, not the task. Images are ignored (none is advertised).
    """
    texts_ = [block.text for block in blocks if block.type == "text"]
    links = [block.uri for block in blocks if block.type == "resource_link"]
    return "\n".join([*texts_[:1], *links]), texts_[1:]


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
    ) -> None:
        self._ctx = AgentContext(
            catalog, home, route, outbox, prices, client, heartbeat_s
        )
        self._sessions: dict[str, Session] = {}
        self._background: set[asyncio.Task[None]] = set()

    def _after_response(self, coro: Coroutine[Any, Any, None]) -> None:
        """Sent once the handler's response has gone out (P6)."""
        task = asyncio.create_task(coro)
        self._background.add(task)
        task.add_done_callback(self._background.discard)

    def _session(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            raise refusal(
                INVALID_PARAMS, texts.unknown_session(session_id), "UNKNOWN_SESSION"
            )
        return self._sessions[session_id]

    async def _snapshot(self) -> CatalogSnapshot:
        try:
            return await asyncio.to_thread(self._ctx.catalog.snapshot)
        except Exception as exc:
            logger.exception("dr_acp.catalog_failed")
            sentence = texts.catalog_error(detail_of(exc))
            raise refusal(INTERNAL_ERROR, sentence, "CATALOG_ERROR") from exc

    def _offer_menu(self, session: Session) -> None:
        self._after_response(self._ctx.outbox.update(*session.menu()))

    async def initialize(
        self,
        protocol_version: int,
        client_capabilities: Any = None,
        client_info: Any = None,
        **meta: Any,
    ) -> dict[str, Any]:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "agentCapabilities": AGENT_CAPABILITIES,
            "agentInfo": {
                "name": "dr-acp",
                "title": "deep_reasoner",
                "version": __version__,
            },
            "authMethods": [],
        }

    async def new_session(
        self,
        cwd: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]:
        snapshot = await self._snapshot()
        session = Session(
            id=ids.new_session_id(),
            cwd=Path(cwd),
            snapshot=snapshot,
            namespace=snapshot.default_namespace,
            ctx=self._ctx,
            mcp_servers=[m.model_dump(mode="json", by_alias=True) for m in mcp_servers],
        )
        session.offer(snapshot.default_namespace)
        self._sessions[session.id] = session
        self._offer_menu(session)
        return {"sessionId": session.id, "configOptions": session.options()}

    async def load_session(
        self,
        cwd: str,
        session_id: str,
        mcp_servers: list[Any],
        additional_directories: list[str] | None = None,
        **meta: Any,
    ) -> dict[str, Any]:
        index = SessionIndex.load(self._ctx.home, session_id)
        if index is None:
            raise refusal(
                INVALID_PARAMS, texts.unknown_session(session_id), "UNKNOWN_SESSION"
            )
        if session_id in self._sessions:
            await self._sessions.pop(session_id).close(SESSION_CLOSE_GRACE_S)
        session = Session(
            id=session_id,
            cwd=Path(cwd),
            snapshot=await self._snapshot(),
            namespace=index.namespace,
            ctx=self._ctx,
            started=index.started,
            runs=list(index.runs),
            last_end=index.last_end,
            mcp_servers=[m.model_dump(mode="json", by_alias=True) for m in mcp_servers],
            source=index.source,
            created=index.created,
        )
        if not session.started:
            session.offer(index.namespace)
        async with session.lock:
            await session.replay()
        self._sessions[session_id] = session
        if not session.started:
            self._offer_menu(session)
        return {"configOptions": session.options()}

    async def set_config_option(
        self, config_id: str, session_id: str, value: str, **meta: Any
    ) -> dict[str, Any]:
        session = self._session(session_id)
        if config_id != "namespace":
            raise refusal(
                INVALID_PARAMS, texts.unknown_option(config_id), "UNKNOWN_OPTION"
            )
        async with session.lock:
            was_started = session.started
            options = session.set_namespace(value)
            if not was_started:
                await self._ctx.outbox.update(*session.menu())
        return {"configOptions": options}

    async def prompt(
        self, prompt: list[Any], session_id: str, **meta: Any
    ) -> dict[str, Any]:
        text, dropped = user_text(prompt)
        result = await self._session(session_id).prompt(text, dropped)
        return {
            "stopReason": result.stop_reason,
            "_meta": {"deep_reasoner": {"run": result.run, "outcome": result.outcome}},
        }

    async def cancel(self, session_id: str, **meta: Any) -> None:
        """A root session id stops the run; a live child's id stops its branch."""
        if session_id in self._sessions:
            await self._sessions[session_id].stop_root()
        elif not any(s.stop_child(session_id) for s in self._sessions.values()):
            logger.warning(f"session/cancel for unknown session '{session_id}' ignored")

    async def close_session(self, session_id: str, **meta: Any) -> dict[str, Any]:
        self._session(session_id)
        await self._sessions.pop(session_id).close(SESSION_CLOSE_GRACE_S)
        return {}

    async def close_all(self, grace_s: float) -> None:
        """Shutdown: close every session's live run concurrently."""
        await asyncio.gather(*(s.close(grace_s) for s in self._sessions.values()))
