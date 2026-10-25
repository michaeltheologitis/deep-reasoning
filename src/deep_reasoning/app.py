"""The web app: the Library's API, and the UI's static files at /."""

from contextlib import closing
from pathlib import Path
from typing import Annotated

from fastapi import Body, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from deep_reasoning.library import LibraryError, add_decomposition, open_library, panel

WEB = Path(__file__).parent / "web"
# Requests naming any other host are refused, so a web page can't reach the API by DNS rebinding.
LOCAL_HOSTS = ["127.0.0.1", "localhost"]
BAD_REQUEST = 400
CREATED = 201


def create_app(library):
    """The app over the Library file at *library*; each request opens it afresh."""
    library = Path(library)
    app = FastAPI()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=LOCAL_HOSTS)

    @app.exception_handler(LibraryError)
    async def refused(request, error):
        return JSONResponse({"detail": str(error)}, status_code=BAD_REQUEST)

    @app.get("/api/library")
    def read_library():
        with closing(open_library(library)) as connection:
            return {"file": library.name, **panel(connection)}

    @app.post("/api/decompositions", status_code=CREATED)
    def post_decomposition(
        namespace: Annotated[str, Body()], yaml: Annotated[str, Body()]
    ):
        with closing(open_library(library)) as connection:
            return add_decomposition(connection, namespace, yaml)

    # A mount at / answers every path, so API routes must be added above it.
    app.mount("/", StaticFiles(directory=WEB, html=True))
    return app
