"""The panel's frame UI (D3), served at /ui/ from the files built into the package (§4.5)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from deep_reasoning.library import texts
from deep_reasoning.library.records import LibraryNotFound

UI_ROOT: Final = Path(__file__).resolve().parents[1] / "canvas_app" / "ui"
UI_HEADERS: Final[Mapping[str, str]] = {
    "Cache-Control": "no-cache",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "base-uri 'none'; form-action 'none'; "
        "frame-ancestors http://localhost:* http://127.0.0.1:*"
    ),
}


def ui_routes(
    root: Path = UI_ROOT,
) -> list[Route]:
    """GET /ui/ → root/index.html; GET /ui/assets/{name} → root/assets/<name> for a name that
    was a file there at start-up, else 404 (LibraryNotFound, D2's JSON); every answer
    carries UI_HEADERS. Without root/index.html, /ui/ answers 503 UI_NOT_BUILT. Nothing
    outside root/assets is ever opened."""
    index = root / "index.html"
    assets = root / "assets"
    built = (
        {path.name for path in assets.iterdir() if path.is_file()}
        if assets.is_dir()
        else set()
    )

    async def page(request: Request) -> Response:
        if not index.is_file():
            body = {"error": "not_built", "message": texts.UI_NOT_BUILT}
            return JSONResponse(body, status_code=503, headers=UI_HEADERS)
        return FileResponse(index, headers=UI_HEADERS)

    async def asset(request: Request) -> Response:
        name = request.path_params["name"]
        if name not in built:
            missing = LibraryNotFound(texts.ui_file_missing(name))
            return JSONResponse(
                missing.payload(), status_code=missing.status, headers=UI_HEADERS
            )
        return FileResponse(assets / name, headers=UI_HEADERS)

    return [
        Route("/ui/", page, methods=["GET"]),
        Route("/ui/assets/{name}", asset, methods=["GET"]),
    ]
