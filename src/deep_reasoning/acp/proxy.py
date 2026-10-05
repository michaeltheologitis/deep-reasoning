"""The key proxy: the worker's model calls carry a token, the proxy swaps the key in, and
a conversation's spend stops at its cap (D5 §4.7).

The proxy runs in dr-acp's front on a thread of its own, serving 127.0.0.1 only.
"""

import fnmatch
import hashlib
import hmac
import json
import math
import platform
import secrets
import socket
import threading
import urllib.request
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Final, Literal
from urllib.parse import urlsplit

import httpx
import structlog
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route as StarletteRoute

from deep_reasoning.acp import texts
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.route import ALWAYS_REMOVED, NO_TOOL_UPSTREAMS, RouteGrant
from deep_reasoning.acp.runlog import Home

logger = structlog.get_logger(__name__)

DEFAULT_RESERVED_OUTPUT_TOKENS: Final = 4096
MAX_BODY_BYTES: Final = 32 * 1024 * 1024
MIN_SECRET_LENGTH: Final = 16
OPENAI_DEFAULT_BASE_URL: Final = "https://api.openai.com/v1"
ANTHROPIC_DEFAULT_BASE_URL: Final = "https://api.anthropic.com"
ANTHROPIC_KEY_ENV: Final = "ANTHROPIC_API_KEY"
ANTHROPIC_BASE_URL_ENV: Final = "ANTHROPIC_BASE_URL"
OPENAI_BASE_URL_ENV: Final = "OPENAI_BASE_URL"
# build_client's fallback, config.py:256
OPENAI_FALLBACK_KEY_ENV: Final = "OPENAI_API_KEY"
# ClientConfig.api_key_env's default
DEEP_REASONER_DEFAULT_KEY_ENV: Final = "NOVITA_API_KEY"
LOOPBACK_HOSTS: Final = ("127.0.0.1", "::1", "localhost")
NO_PROXY_HOSTS: Final = "127.0.0.1,localhost,::1"
UPSTREAM_TIMEOUT: Final = httpx.Timeout(600.0, connect=10.0)
# Not forwarded either way: the connection's own, and what the proxy sets itself.
HOP_BY_HOP: Final = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)
NOT_FORWARDED: Final = HOP_BY_HOP | {
    "host",
    "cookie",
    "content-length",
    "authorization",
    "x-api-key",
    "accept-encoding",
}
NOT_RETURNED: Final = HOP_BY_HOP | {"content-length", "content-encoding"}
REDACTED: Final = b"[redacted]"

Dialect = Literal["openai", "anthropic"]

METERED_PATHS: Final[Mapping[Dialect, frozenset[str]]] = {
    "openai": frozenset({"chat/completions", "completions", "embeddings"}),
    "anthropic": frozenset({"v1/messages"}),
}
FREE_PATHS: Final[Mapping[Dialect, frozenset[str]]] = {
    "openai": frozenset(),
    "anthropic": frozenset({"v1/messages/count_tokens"}),
}


@dataclass(frozen=True)
class Route:
    id: str  # 16 hex, the URL's only identifier
    session: str
    run: str
    dialect: Dialect
    upstream: str  # base URL without a trailing slash
    key: str = field(repr=False)
    token_sha256: bytes = field(repr=False)


@dataclass(frozen=True)
class Reservation:
    session: str
    usd: float


@dataclass
class Spend:
    """One root session's account."""

    spent_usd: float = 0.0
    reserved_usd: float = 0.0
    calls: int = 0
    refused: int = 0


class SpendLedger:
    """Per root session; persisted at <home>/spend/<session>.json; thread-safe."""

    def __init__(self, home: Home, cap_usd: float) -> None:
        self._dir = home.root / "spend"
        self.cap_usd = cap_usd
        self._accounts: dict[str, Spend] = {}
        self._lock = threading.Lock()

    def _account(self, session: str) -> Spend:
        """The session's account; its file is read the first time, so a restarted
        dr-acp continues the count."""
        if session not in self._accounts:
            path = self._dir / f"{session}.json"
            saved = json.loads(path.read_text()) if path.exists() else {}
            self._accounts[session] = Spend(
                spent_usd=float(saved.get("spent_usd", 0.0)),
                calls=int(saved.get("calls", 0)),
                refused=int(saved.get("refused", 0)),
            )
        return self._accounts[session]

    def _save(self, session: str, account: Spend) -> None:
        """Atomic: a temporary file, then rename."""
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{session}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(
                {
                    "v": 1,
                    "session": session,
                    "cap_usd": self.cap_usd,
                    "spent_usd": account.spent_usd,
                    "calls": account.calls,
                    "refused": account.refused,
                }
            )
        )
        temporary.replace(path)

    def reserve(self, session: str, usd: float) -> Reservation | None:
        """None (and refused += 1) when spent + reserved + usd > cap."""
        with self._lock:
            account = self._account(session)
            if account.spent_usd + account.reserved_usd + usd > self.cap_usd:
                account.refused += 1
                self._save(session, account)
                return None
            account.reserved_usd += usd
            return Reservation(session, usd)

    def settle(self, reservation: Reservation, usd: float) -> None:
        """The reservation replaced by the call's cost."""
        with self._lock:
            account = self._account(reservation.session)
            account.reserved_usd = max(0.0, account.reserved_usd - reservation.usd)
            account.spent_usd += usd
            account.calls += 1
            self._save(reservation.session, account)

    def spend(self, session: str) -> Spend:
        """A copy of the session's account."""
        with self._lock:
            return replace(self._account(session))


def is_loopback(url: str) -> bool:
    return urlsplit(url).hostname in LOOPBACK_HOSTS


def _token_from(request: Request) -> str:
    """The Bearer token, else x-api-key; "" for neither."""
    authorization = request.headers.get("authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer" and value:
        return value.strip()
    return request.headers.get("x-api-key", "").strip()


def _usage_in(dialect: Dialect, usage: Mapping[str, Any]) -> dict[str, Any]:
    """Usage as PriceTable.estimate reads it; Anthropic's cache tokens count as
    input."""
    if dialect == "openai":
        return dict(usage)
    tokens_in = sum(
        int(usage.get(name) or 0)
        for name in (
            "input_tokens",
            "cache_creation_input_tokens",
            "cache_read_input_tokens",
        )
    )
    return {"input_tokens": tokens_in, "output_tokens": usage.get("output_tokens")}


class _StreamMeter:
    """Reads the usage out of a server-sent event stream as it passes through: the last
    openai chunk that carries one, or anthropic's message_start and message_delta."""

    def __init__(self, dialect: Dialect) -> None:
        self._dialect = dialect
        self._pending = b""
        self.usage: dict[str, Any] | None = None

    def feed(self, chunk: bytes) -> None:
        self._pending += chunk
        *lines, self._pending = self._pending.split(b"\n")
        for line in lines:
            if line.startswith(b"data:"):
                self._data(line[len(b"data:") :].strip())

    def _data(self, data: bytes) -> None:
        try:
            event = json.loads(data)
        except ValueError:
            return  # "[DONE]"
        if not isinstance(event, dict):
            return
        if self._dialect == "openai":
            if event.get("usage"):
                self.usage = event["usage"]
            return
        if event.get("type") == "message_start":
            usage = (event.get("message") or {}).get("usage") or {}
            self.usage = {**(self.usage or {}), **usage}
        elif event.get("type") == "message_delta" and event.get("usage"):
            self.usage = {**(self.usage or {}), **event["usage"]}


class KeyProxy:
    """The HTTP side: 127.0.0.1 only, its own thread, started on first use."""

    def __init__(self, *, ledger: SpendLedger, prices: PriceTable, home: Home) -> None:
        self._ledger = ledger
        self._prices = prices
        self._home = home
        self._routes: dict[str, Route] = {}
        self._lock = threading.Lock()
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._port: int | None = None

    def ensure_started(self) -> None:
        """Bind 127.0.0.1:0 (so the port is known), then serve on a thread of its own;
        returns once the server accepts connections."""
        with self._lock:
            if self._server is not None:
                return
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            self._port = sock.getsockname()[1]
            config = uvicorn.Config(
                self.app(),
                log_level="warning",
                lifespan="off",
                access_log=False,
                timeout_graceful_shutdown=0,
            )
            self._server = uvicorn.Server(config)
            self._thread = threading.Thread(
                target=self._server.run,
                kwargs={"sockets": [sock]},
                name="dr-acp-key-proxy",
                daemon=True,
            )
            self._thread.start()
        while not self._server.started:
            if not self._thread.is_alive():
                raise RuntimeError("the key proxy did not start")
            threading.Event().wait(0.005)

    def stop(self, timeout_s: float = 0.5) -> None:
        if self._server is None:
            return
        self._server.should_exit = True
        self._thread.join(timeout_s)

    @property
    def base_url(self) -> str:
        """http://127.0.0.1:<port>; only after ensure_started()."""
        return f"http://127.0.0.1:{self._port}"

    def add_route(
        self,
        *,
        session: str,
        run: str,
        dialect: Dialect,
        upstream: str,
        key: str,
        token: str,
    ) -> Route:
        route = Route(
            id=secrets.token_hex(8),
            session=session,
            run=run,
            dialect=dialect,
            upstream=upstream.rstrip("/"),
            key=key,
            token_sha256=hashlib.sha256(token.encode()).digest(),
        )
        with self._lock:
            self._routes[route.id] = route
        return route

    def drop_run(self, run: str) -> None:
        """The run's routes, and so its tokens, stop working; calls in flight finish."""
        with self._lock:
            self._routes = {k: r for k, r in self._routes.items() if r.run != run}

    def app(self) -> Starlette:
        """The ASGI app of §4.7.3, which ensure_started serves."""
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        return Starlette(
            routes=[
                StarletteRoute(
                    "/r/{route_id}/{rest:path}", self._handle, methods=methods
                )
            ]
        )

    def _route(self, route_id: str, token: str) -> Route | None:
        with self._lock:
            route = self._routes.get(route_id)
        digest = hashlib.sha256(token.encode()).digest()
        if route is None or not hmac.compare_digest(digest, route.token_sha256):
            return None
        return route

    def _refuse(
        self,
        route: Route | None,
        status: int,
        code: str,
        message: str,
        model: Any = None,
    ) -> JSONResponse:
        """The refusal logged, without a key or a token, and answered in the dialect's
        own error shape."""
        logger.warning(
            "dr_acp.key_proxy.refused",
            reason=code,
            model=model,
            session=route.session if route else None,
        )
        if route is not None and route.dialect == "anthropic":
            body: dict[str, Any] = {
                "type": "error",
                "error": {"type": code, "message": message},
            }
        else:
            body = {"error": {"message": message, "type": code, "code": code}}
        return JSONResponse(body, status_code=status)

    async def _handle(self, request: Request) -> Response:
        rest = request.path_params["rest"]
        route = self._route(request.path_params["route_id"], _token_from(request))
        if route is None:
            return self._refuse(None, 401, "bad_token", texts.BAD_TOKEN)
        metered = METERED_PATHS[route.dialect]
        free = FREE_PATHS[route.dialect]
        if request.method != "POST" or rest not in metered | free:
            paths = ", ".join(sorted(metered | free))
            message = texts.not_a_model_call(paths, request.method, rest)
            return self._refuse(route, 403, "not_a_model_call", message)
        body = await self._body(request)
        if body is None:
            message = texts.bad_body(rest, MAX_BODY_BYTES // (1024 * 1024))
            return self._refuse(route, 400, "bad_body", message)
        if rest in free:
            return await self._forward(request, route, rest, body, None, None)
        return await self._metered(request, route, rest, body)

    @staticmethod
    async def _body(request: Request) -> dict[str, Any] | None:
        """The JSON object sent, at most MAX_BODY_BYTES; None otherwise."""
        raw = bytearray()
        async for chunk in request.stream():
            raw += chunk
            if len(raw) > MAX_BODY_BYTES:
                return None
        try:
            body = json.loads(raw)
        except ValueError:
            return None
        return body if isinstance(body, dict) else None

    def _price_known(self, model: Any) -> bool:
        if not isinstance(model, str):
            return False
        probe = {"prompt_tokens": 1, "completion_tokens": 1}
        return self._prices.estimate(model, probe).usd is not None

    async def _metered(
        self, request: Request, route: Route, rest: str, body: dict[str, Any]
    ) -> Response:
        model = body.get("model")
        if not self._price_known(model) and not is_loopback(route.upstream):
            message = texts.unpriced(str(model), str(self._home.root))
            return self._refuse(route, 400, "unpriced", message, model)
        if route.dialect == "openai" and body.get("stream"):
            body["stream_options"] = {
                **(body.get("stream_options") or {}),
                "include_usage": True,
            }
        payload = json.dumps(body).encode()
        tokens_out = (
            0
            if rest == "embeddings"
            else body.get("max_completion_tokens")
            or body.get("max_tokens")
            or DEFAULT_RESERVED_OUTPUT_TOKENS
        )
        estimate = self._prices.estimate(
            model,
            {
                "prompt_tokens": math.ceil(len(payload) / 4),
                "completion_tokens": tokens_out,
            },
        )
        reservation = self._ledger.reserve(route.session, estimate.usd or 0.0)
        if reservation is None:
            spend = self._ledger.spend(route.session)
            message = texts.cap_reached(spend.spent_usd, self._ledger.cap_usd)
            return self._refuse(route, 402, "cap_reached", message, model)
        return await self._forward(request, route, rest, body, model, reservation)

    def _cost(self, route: Route, model: Any, usage: Mapping[str, Any]) -> float:
        estimate = self._prices.estimate(model, _usage_in(route.dialect, usage))
        return estimate.usd or 0.0

    async def _forward(
        self,
        request: Request,
        route: Route,
        rest: str,
        body: dict[str, Any],
        model: Any,
        reservation: Reservation | None,
    ) -> Response:
        """Send body upstream with the real key; settle the reservation from the usage
        the response reports, else at the reservation for a success and at 0 for a
        refusal."""
        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() not in NOT_FORWARDED
        }
        if route.dialect == "openai":
            headers["authorization"] = f"Bearer {route.key}"
        else:
            headers["x-api-key"] = route.key
        url = f"{route.upstream}/{rest}"
        if request.url.query:
            url += f"?{request.url.query}"
        client = httpx.AsyncClient(
            timeout=UPSTREAM_TIMEOUT, trust_env=not is_loopback(route.upstream)
        )
        try:
            upstream = await client.send(
                client.build_request(
                    "POST", url, headers=headers, content=json.dumps(body).encode()
                ),
                stream=True,
            )
        except httpx.TransportError as exc:
            await client.aclose()
            if reservation is not None:
                self._ledger.settle(reservation, 0.0)
            host = urlsplit(route.upstream).netloc
            message = texts.upstream_unreachable(host, str(exc) or type(exc).__name__)
            return self._refuse(route, 502, "upstream_unreachable", message, model)
        returned = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() not in NOT_RETURNED
        }
        streamed = "text/event-stream" in upstream.headers.get("content-type", "")
        if streamed and upstream.is_success:
            return StreamingResponse(
                self._relay(client, upstream, route, model, reservation),
                status_code=upstream.status_code,
                headers=returned,
            )
        try:
            content = await upstream.aread()
        finally:
            await upstream.aclose()
            await client.aclose()
        if not upstream.is_success:
            content = content.replace(route.key.encode(), REDACTED)
        if reservation is not None:
            usage = self._json_usage(content)
            if usage is not None:
                cost = self._cost(route, model, usage)
            else:  # a refusal that reports nothing cost nothing
                cost = reservation.usd if upstream.is_success else 0.0
            self._ledger.settle(reservation, cost)
        return Response(content, status_code=upstream.status_code, headers=returned)

    @staticmethod
    def _json_usage(content: bytes) -> Mapping[str, Any] | None:
        try:
            body = json.loads(content)
        except ValueError:
            return None
        usage = body.get("usage") if isinstance(body, dict) else None
        return usage if isinstance(usage, dict) else None

    async def _relay(
        self,
        client: httpx.AsyncClient,
        upstream: httpx.Response,
        route: Route,
        model: Any,
        reservation: Reservation | None,
    ) -> AsyncIterator[bytes]:
        meter = _StreamMeter(route.dialect)
        try:
            async for chunk in upstream.aiter_bytes():
                meter.feed(chunk)
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()
            if reservation is not None:
                cost = (
                    reservation.usd
                    if meter.usage is None
                    else self._cost(route, model, meter.usage)
                )
                self._ledger.settle(reservation, cost)


def loopback_proxy_env(
    env: Mapping[str, str],
    *,
    system: str,
    system_proxies: Callable[[], Mapping[str, str]] = urllib.request.getproxies,
) -> dict[str, str]:
    """§4.7.2 step 5: NO_PROXY with the loopback hosts appended; on macOS with no proxy in
    env, the system's http and https proxies as HTTP_PROXY and HTTPS_PROXY."""
    existing = env.get("NO_PROXY") or env.get("no_proxy")
    no_proxy = f"{existing},{NO_PROXY_HOSTS}" if existing else NO_PROXY_HOSTS
    added = {"NO_PROXY": no_proxy}
    if "no_proxy" in env:  # Python reads the lower-case name first
        added["no_proxy"] = no_proxy
    names_a_proxy = any(
        name.lower() in ("http_proxy", "https_proxy", "all_proxy") and value
        for name, value in env.items()
    )
    if system == "Darwin" and not names_a_proxy:
        proxies = system_proxies()
        for scheme in ("http", "https"):
            if proxies.get(scheme):
                added[f"{scheme.upper()}_PROXY"] = proxies[scheme]
    return added


class ProxyRoute:
    """D1's ModelRoute over a KeyProxy (§4.7.2)."""

    def __init__(self, proxy: KeyProxy, env: Mapping[str, str]) -> None:
        self._proxy = proxy
        self._env = dict(env)

    def _key_name(self, client: Mapping[str, Any]) -> str | None:
        """The variable whose value the client would send, as build_client picks it;
        None when dr-acp holds no value for it."""
        name = client.get("api_key_env") or DEEP_REASONER_DEFAULT_KEY_ENV
        if not self._env.get(name) and self._env.get(OPENAI_FALLBACK_KEY_ENV):
            name = OPENAI_FALLBACK_KEY_ENV
        return name if self._env.get(name) else None

    def _upstream(self, client: Mapping[str, Any]) -> str:
        url = (
            client.get("base_url")
            or self._env.get(OPENAI_BASE_URL_ENV)
            or OPENAI_DEFAULT_BASE_URL
        )
        return url.rstrip("/")

    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = NO_TOOL_UPSTREAMS,
    ) -> RouteGrant:
        clients = {None: upstream, **dict(tool_upstreams)}
        held = {name: self._key_name(c) for name, c in clients.items()}
        anthropic_key = self._env.get(ANTHROPIC_KEY_ENV)
        if not any(held.values()) and not anthropic_key:
            return RouteGrant()
        self._proxy.ensure_started()
        tokens: dict[str, str] = {}
        routes: dict[tuple[str, str], str] = {}
        overrides: dict[str | None, dict[str, Any]] = {}
        for name, client in clients.items():
            key_name = held[name]
            if key_name is None:
                continue
            token = tokens.setdefault(key_name, secrets.token_urlsafe(32))
            where = (self._upstream(client), key_name)
            if where not in routes:
                route = self._proxy.add_route(
                    session=session,
                    run=run,
                    dialect="openai",
                    upstream=where[0],
                    key=self._env[key_name],
                    token=token,
                )
                routes[where] = f"{self._proxy.base_url}/r/{route.id}"
            overrides[name] = {"base_url": routes[where], "api_key_env": key_name}
        env_add = dict(tokens)
        if anthropic_key:
            token = secrets.token_urlsafe(32)
            route = self._proxy.add_route(
                session=session,
                run=run,
                dialect="anthropic",
                upstream=self._env.get(ANTHROPIC_BASE_URL_ENV)
                or ANTHROPIC_DEFAULT_BASE_URL,
                key=anthropic_key,
                token=token,
            )
            env_add[ANTHROPIC_KEY_ENV] = token
            env_add[ANTHROPIC_BASE_URL_ENV] = f"{self._proxy.base_url}/r/{route.id}"
        env_add |= loopback_proxy_env(self._env, system=platform.system())
        return RouteGrant(
            client_overrides=overrides.get(None, {}),
            env_add=env_add,
            env_remove=self._env_remove(
                [self._env[k] for k in tokens]
                + ([anthropic_key] if anthropic_key else [])
            ),
            tool_client_overrides={
                name: o for name, o in overrides.items() if name is not None
            },
        )

    def _env_remove(self, keys: list[str]) -> frozenset[str]:
        """Every variable whose value contains a held key, or the value of a variable
        one of ALWAYS_REMOVED's patterns names; values shorter than MIN_SECRET_LENGTH
        are never matched."""
        secret_values = [
            value
            for name, value in self._env.items()
            if any(fnmatch.fnmatchcase(name, p) for p in ALWAYS_REMOVED)
        ]
        values = [v for v in (*keys, *secret_values) if len(v) >= MIN_SECRET_LENGTH]
        return frozenset(
            name
            for name, value in self._env.items()
            if any(secret in value for secret in values)
        )

    def release(self, run: str) -> None:
        self._proxy.drop_run(run)
