"""The web app: the Library's and the runs' API, and the UI's static files at /."""

from contextlib import asynccontextmanager, closing
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import Body, Depends, FastAPI, Header, HTTPException
from fastapi import Path as InPath
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from deep_reasoning.library import (
    LibraryError,
    add_decomposition,
    default_namespace,
    engine_config,
    open_library,
    panel,
)
from deep_reasoning.runs import (
    RUN_ID,
    RunInProgress,
    Runs,
    end_unfinished,
    read_turn,
    turn_starts,
)

WEB = Path(__file__).parent / "web"
# Requests naming any other host are refused, so a web page can't reach the API by DNS rebinding.
LOCAL_HOSTS = ["127.0.0.1", "localhost"]
# A chat id is the client's own name for a chat: plain characters only.
CHAT_ID = r"^[A-Za-z0-9_-]{1,100}$"

log = structlog.get_logger()


def create_app(library, home):
    """The app over the Library file at *library*, which each request opens afresh,
    keeping its runs under *home*."""
    library = Path(library)
    runs = Runs(Path(home))

    @asynccontextmanager
    async def lifespan(app):
        for run in end_unfinished(runs.home):
            log.warning("Ended a run the app stopped under", run=run)
        yield
        await runs.close()

    app = FastAPI(lifespan=lifespan)
    app.state.runs = runs
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=LOCAL_HOSTS)

    @app.exception_handler(LibraryError)
    async def refused(request, error):
        return JSONResponse({"detail": str(error)}, status_code=HTTPStatus.BAD_REQUEST)

    @app.exception_handler(RunInProgress)
    async def busy(request, error):
        detail = f"Chat {error} has a run going."
        return JSONResponse({"detail": detail}, status_code=HTTPStatus.CONFLICT)

    @app.get("/api/library")
    def read_library():
        with closing(open_library(library)) as connection:
            return {"file": library.name, **panel(connection)}

    @app.post("/api/decompositions", status_code=HTTPStatus.CREATED)
    def post_decomposition(
        namespace: Annotated[str, Body()], yaml: Annotated[str, Body()]
    ):
        with closing(open_library(library)) as connection:
            return add_decomposition(connection, namespace, yaml)

    @app.post("/api/chats/{chat}/runs", status_code=HTTPStatus.CREATED)
    async def start_run(
        chat: Annotated[str, InPath(pattern=CHAT_ID)],
        prompt: Annotated[str, Body(embed=True, min_length=1)],
    ):
        # Before the chat's turns are read: a run that is going has no turn.end yet.
        if runs.live(chat) is not None:
            raise RunInProgress(chat)
        starts = turn_starts(runs.home, chat)
        # A chat stays in the namespace it started in.
        namespace = starts[0]["namespace"] if starts else default_namespace(library)
        earlier = [read_turn(runs.home, start["run"]) for start in starts]

        def config_for(folder):
            # The run gets the Library's tools as they are now, in a folder of its own.
            return engine_config(library, namespace, folder / "tools")

        return {"run": runs.start(chat, prompt, config_for, earlier)}

    def known_run(run: Annotated[str, InPath(pattern=RUN_ID)]):
        if not runs.exists(run):
            raise HTTPException(HTTPStatus.NOT_FOUND, f"There is no run {run}.")
        return run

    @app.post("/api/runs/{run}/stop")
    async def stop_run(run: Annotated[str, Depends(known_run)]):
        if not runs.stop(run):
            raise HTTPException(HTTPStatus.CONFLICT, f"Run {run} has already ended.")
        return {"run": run, "stopping": True}

    @app.get("/api/runs/{run}/events", response_class=EventSourceResponse)
    async def run_events(
        run: Annotated[str, Depends(known_run)],
        last_event_id: Annotated[int, Header(ge=0)] = 0,
    ):
        async for event in runs.events(run, after=last_event_id):
            yield ServerSentEvent(data=event, id=str(event["seq"]))

    # A mount at / answers every path, so API routes must be added above it.
    app.mount("/", StaticFiles(directory=WEB, html=True))
    return app
