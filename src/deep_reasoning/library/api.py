"""The App backend's HTTP API (§6): one Starlette app over one Library."""

import io
import os
import socket
import sys
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Receive, Scope, Send

from deep_reasoning.library import shapes, texts
from deep_reasoning.library.library import Library
from deep_reasoning.library.records import (
    Kind,
    LibraryBadRequest,
    LibraryError,
    LibraryForbidden,
    LibraryNotFound,
    LibraryNotJson,
)
from deep_reasoning.library.ui import ui_routes

Peer = tuple[str, int]
JSON_TYPE = "application/json"
BODY_METHODS = frozenset({"PUT", "POST"})
PROC_NET = Path("/proc/net")


def _proc_address(host: str, port: int) -> str:
    """host:port as /proc/net/tcp{,6} prints it: each 32-bit word in host byte order."""
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    packed = socket.inet_pton(family, host)
    words = (packed[i : i + 4] for i in range(0, len(packed), 4))
    return (
        "".join(f"{int.from_bytes(w, sys.byteorder):08X}" for w in words)
        + f":{port:04X}"
    )


def same_user_peer(
    client: tuple[str, int],
    server: tuple[str, int],
    *,
    proc_net: Path = PROC_NET,
) -> bool:
    """True when the TCP socket at client connected to server belongs to os.getuid().

    Reads proc_net/tcp and tcp6, finds the row whose local address is client and remote
    address is server (hex, little-endian per 32-bit word, as the kernel prints them), and
    compares its uid. No such row: False.
    """
    try:
        local, remote = _proc_address(*client), _proc_address(*server)
    except OSError:
        return False
    for table in ("tcp", "tcp6"):
        path = proc_net / table
        if not path.exists():
            continue
        for line in path.read_text().splitlines()[1:]:
            fields = line.split()
            if fields[1:3] == [local, remote]:
                return int(fields[7]) == os.getuid()
    return False


def _refusal(
    scope: Scope, same_user: Callable[[Peer, Peer], bool] | None
) -> LibraryError | None:
    """Why a request is refused before it reaches a route, or None."""
    client, server = scope.get("client"), scope.get("server")
    if same_user is not None and not (
        client and server and same_user(tuple(client), tuple(server))
    ):
        return LibraryForbidden(texts.FORBIDDEN_PEER)
    port = server[1] if server else 0
    headers = {
        k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]
    }
    # A page on another site that rebinds its DNS name to 127.0.0.1 still says its own name.
    if headers.get("host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
        return LibraryForbidden(texts.forbidden_host(port))
    content_type = headers.get("content-type", "").split(";")[0].strip().lower()
    # A cross-site form or text/plain fetch can POST without a preflight; JSON cannot.
    if scope["method"] in BODY_METHODS and content_type != JSON_TYPE:
        return LibraryNotJson(texts.NOT_JSON)
    return None


class _Guard:
    """Refuses another user's connection, a foreign Host header and a non-JSON body."""

    def __init__(
        self, app: ASGIApp, same_user: Callable[[Peer, Peer], bool] | None
    ) -> None:
        self.app = app
        self.same_user = same_user

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and (refused := _refusal(scope, self.same_user)):
            await JSONResponse(refused.payload(), status_code=refused.status)(
                scope, receive, send
            )
            return
        await self.app(scope, receive, send)


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yaml: str
    base_version: int | None = None


class _ListBody(_Body):
    """A profile's or a namespace's: the YAML and its decompositions, in order."""

    decompositions: list[str] | None = None


class _DecompositionBody(_Body):
    use_when: str | None = None
    hint: str | None = None
    namespaces: list[str] | None = None
    top_level: bool | None = None


class _ToolBody(_Body):
    source: str | None = None
    granted_in: list[str] | None = None
    # D4: save a tool whose Check failed in a way it allows (D4 §3.5).
    accept_check_failure: bool = False


class _ValidateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Kind
    yaml: str
    name: str | None = None
    source: str | None = None


def _parse[T: BaseModel](
    model: type[T], body: bytes, sentence: str = texts.BAD_REQUEST
) -> T:
    """The body as model; a body it cannot read is 400, sentence and pydantic's reason."""
    try:
        return model.model_validate_json(body)
    except ValidationError as exc:
        raise LibraryBadRequest(f"{sentence} {exc.errors()[0]['msg']}") from exc


def _base_version(request: Request) -> int | None:
    raw = request.query_params.get("base_version")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise LibraryBadRequest(
            f"base_version must be a whole number; got {raw!r}."
        ) from exc


def _dump(result: Any) -> Any:
    if isinstance(result, BaseModel):
        return result.model_dump(mode="json")
    if isinstance(result, list):
        return [_dump(item) for item in result]
    return result


def _exists(read: Callable[[], Any]) -> bool:
    try:
        read()
    except LibraryNotFound:
        return False
    return True


def _key_matches(library: Library, kind: Kind, text: str, key: str) -> None:
    """A PUT's path key must be the YAML's own (name, or a decomposition's slug)."""
    result = library.validate(kind, text)
    address = result.slug if kind == "decomposition" else result.name
    if result.ok and address != key:
        raise LibraryBadRequest(texts.name_mismatch(result.name, key, kind))


def _zip(directory: Path, prefix: str) -> bytes:
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            archive.write(path, f"{prefix}/{path.relative_to(directory)}")
    return data.getvalue()


def json_route(
    path: str, method: str, handler: Callable[[Request, bytes], Any]
) -> Route:
    """A route whose handler runs in a thread with the request and its body, and returns
    a Response, a payload, or (payload, status); payloads are sent as JSON."""

    async def endpoint(request: Request) -> Response:
        body = await request.body() if method in BODY_METHODS else b""
        result = await run_in_threadpool(handler, request, body)
        if isinstance(result, Response):
            return result
        payload, status = result if isinstance(result, tuple) else (result, 200)
        return JSONResponse(_dump(payload), status_code=status)

    return Route(path, endpoint, methods=[method])


def create_app(
    library: Library,
    *,
    same_user: Callable[[tuple[str, int], tuple[str, int]], bool] | None = None,
) -> Starlette:
    """The routes of §6, then the panel's /ui/ (D3 §4.5), then D4's tool and MCP routes
    (D4 §7.2); a tool's PUT passes D4's Check first (D4 §3.5). same_user(client, server) is
    asked for every request; a False is 403 FORBIDDEN_PEER. Default: same_user_peer on
    Linux, no check elsewhere."""
    # D4's routes build on json_route, so they are imported only once this module is.
    from deep_reasoning.tools.check import require_check
    from deep_reasoning.tools.routes import tool_routes

    if same_user is None and sys.platform == "linux":
        same_user = same_user_peer
    lib = library

    def health(request: Request, body: bytes) -> Any:
        state = lib.state()
        return {
            "ok": True,
            "rev": state.rev,
            "path": str(lib.path),
            "deep_reasoner": shapes.deep_reasoner_build(),
            "default_namespace": state.profile.default_namespace,
        }

    def validate(request: Request, body: bytes) -> Any:
        sent = _parse(_ValidateBody, body)
        return lib.validate(sent.kind, sent.yaml, name=sent.name, source=sent.source)

    def put_profile(request: Request, body: bytes) -> Any:
        sent = _parse(_ListBody, body)
        return lib.put_profile(
            sent.yaml,
            decompositions=sent.decompositions,
            base_version=sent.base_version,
        )

    def put_namespace(request: Request, body: bytes) -> Any:
        name, sent = request.path_params["name"], _parse(_ListBody, body)
        _key_matches(lib, "namespace", sent.yaml, name)
        existed = _exists(lambda: lib.namespace(name))
        record = lib.put_namespace(
            sent.yaml,
            decompositions=sent.decompositions,
            base_version=sent.base_version,
        )
        return record, 200 if existed else 201

    def put_decomposition(request: Request, body: bytes) -> Any:
        key, sent = request.path_params["slug"], _parse(_DecompositionBody, body)
        _key_matches(lib, "decomposition", sent.yaml, key)
        existed = _exists(lambda: lib.decomposition(key))
        record = lib.put_decomposition(
            sent.yaml,
            use_when=sent.use_when,
            hint=sent.hint,
            namespaces=sent.namespaces,
            top_level=sent.top_level,
            base_version=sent.base_version,
        )
        return record, 200 if existed else 201

    def put_tool(request: Request, body: bytes) -> Any:
        name, sent = request.path_params["name"], _parse(_ToolBody, body)
        require_check(
            lib,
            name,
            sent.yaml,
            sent.source,
            accept_failure=sent.accept_check_failure,
        )
        existed = _exists(lambda: lib.tool(name))
        record = lib.put_tool(
            name,
            sent.yaml,
            source=sent.source,
            granted_in=sent.granted_in,
            base_version=sent.base_version,
        )
        return record, 200 if existed else 201

    def deleting(kind: Kind, param: str) -> Callable[[Request, bytes], Any]:
        def delete(request: Request, body: bytes) -> Any:
            key = request.path_params[param]
            return lib.delete(kind, key, base_version=_base_version(request))

        return delete

    def versions(kind: Kind, param: str | None) -> Callable[[Request, bytes], Any]:
        def history(request: Request, body: bytes) -> Any:
            key = request.path_params[param] if param else "profile"
            entries = lib.history(kind, key)
            if "n" not in request.path_params:
                return entries
            n = request.path_params["n"]
            found = [e for e in entries if e.version == n]
            if not found:
                raise LibraryNotFound(texts.no_version(kind, key, n))
            return found[0]

        return history

    def export(request: Request, body: bytes) -> Any:
        rev = lib.rev()
        with tempfile.TemporaryDirectory(prefix="dr-library-") as tmp:
            config = lib.materialize(
                Path(tmp) / "library",
                namespace=request.query_params.get("namespace"),
                rev=rev,
            )
            content = _zip(config, "library")
        return Response(
            content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="library-rev{rev}.zip"'
            },
        )

    def reading(
        read: Callable[..., Any], *params: str
    ) -> Callable[[Request, bytes], Any]:
        return lambda request, body: read(*(request.path_params[p] for p in params))

    routes = [
        json_route("/health", "GET", health),
        json_route("/problems", "GET", reading(lib.check)),
        json_route("/validate", "POST", validate),
        json_route("/profile", "GET", reading(lib.profile)),
        json_route("/profile", "PUT", put_profile),
        json_route("/profile/versions", "GET", versions("profile", None)),
        json_route("/profile/versions/{n:int}", "GET", versions("profile", None)),
        json_route("/namespaces", "GET", reading(lib.namespaces)),
        json_route("/namespaces/{name}", "GET", reading(lib.namespace, "name")),
        json_route("/namespaces/{name}", "PUT", put_namespace),
        json_route("/namespaces/{name}", "DELETE", deleting("namespace", "name")),
        json_route(
            "/namespaces/{name}/effective", "GET", reading(lib.effective, "name")
        ),
        json_route("/namespaces/{name}/versions", "GET", versions("namespace", "name")),
        json_route(
            "/namespaces/{name}/versions/{n:int}", "GET", versions("namespace", "name")
        ),
        json_route(
            "/effective",
            "GET",
            lambda request, body: [lib.effective(ns.name) for ns in lib.namespaces()],
        ),
        json_route("/decompositions", "GET", reading(lib.decompositions)),
        json_route("/decompositions/{slug}", "GET", reading(lib.decomposition, "slug")),
        json_route("/decompositions/{slug}", "PUT", put_decomposition),
        json_route(
            "/decompositions/{slug}", "DELETE", deleting("decomposition", "slug")
        ),
        json_route(
            "/decompositions/{slug}/versions", "GET", versions("decomposition", "slug")
        ),
        json_route(
            "/decompositions/{slug}/versions/{n:int}",
            "GET",
            versions("decomposition", "slug"),
        ),
        json_route("/tools", "GET", reading(lib.tools)),
        json_route("/tools/{name}", "GET", reading(lib.tool, "name")),
        json_route("/tools/{name}", "PUT", put_tool),
        json_route("/tools/{name}", "DELETE", deleting("tool", "name")),
        json_route("/tools/{name}/versions", "GET", versions("tool", "name")),
        json_route("/tools/{name}/versions/{n:int}", "GET", versions("tool", "name")),
        json_route("/export", "GET", export),
        *ui_routes(),
        *tool_routes(lib),
    ]

    async def library_error(request: Request, exc: Exception) -> Response:
        assert isinstance(exc, LibraryError)
        return JSONResponse(exc.payload(), status_code=exc.status)

    app = Starlette(routes=routes, exception_handlers={LibraryError: library_error})
    app.add_middleware(_Guard, same_user=same_user)
    return app
