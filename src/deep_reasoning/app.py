"""The web app: the Library's, the chats' and the runs' API, and the UI's static files at /."""

from contextlib import asynccontextmanager, closing
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi import Path as InPath
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from pydantic import StringConstraints
from starlette.middleware.trustedhost import TrustedHostMiddleware

from deep_reasoning.chats import (
    CHATS_FILE,
    create_chat,
    delete_chat,
    find_chat,
    list_chats,
    rename_chat,
    title_new_chat,
)
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
    read_events,
    read_turn,
    turn_starts,
)

WEB = Path(__file__).parent / "web"
# Requests naming any other host are refused, so a web page can't reach the API by DNS rebinding.
LOCAL_HOSTS = ["127.0.0.1", "localhost"]
# A chat id in a path: plain characters only, like the ids the app makes.
CHAT_ID = r"^[A-Za-z0-9_-]{1,100}$"

log = structlog.get_logger()


def create_app(library, home):
    """The app over the Library file at *library*, which each request opens afresh,
    keeping its chats and runs under *home*."""
    library = Path(library)
    chats = Path(home) / CHATS_FILE
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

    def shown(chat):
        """A chat as the API gives it: with the id of its run that is going, if one is."""
        return chat | {"live": runs.live(chat["id"])}

    # The chat routes are coroutines, so they run on the event loop with the runs: what
    # they read of a run is whole, and no chat is deleted between this check and a route.
    async def known_chat(chat: Annotated[str, InPath(pattern=CHAT_ID)]):
        found = find_chat(chats, chat)
        if found is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"There is no chat {chat}.")
        return found

    KnownChat = Annotated[dict, Depends(known_chat)]

    @app.get("/api/chats")
    async def read_chats():
        return [shown(chat) for chat in list_chats(chats)]

    @app.post("/api/chats", status_code=HTTPStatus.CREATED)
    async def post_chat():
        return shown(create_chat(chats))

    @app.get("/api/chats/{chat}")
    async def read_chat(chat: KnownChat):
        turns = [
            {"run": start["run"], "events": list(read_events(runs.home, start["run"]))}
            for start in turn_starts(runs.home, chat["id"])
        ]
        return shown(chat) | {"turns": turns}

    @app.patch("/api/chats/{chat}")
    async def patch_chat(
        chat: KnownChat,
        title: Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1),
            Body(embed=True),
        ],
    ):
        rename_chat(chats, chat["id"], title)
        return shown(chat | {"title": title})

    @app.delete("/api/chats/{chat}", status_code=HTTPStatus.NO_CONTENT)
    async def remove_chat(chat: KnownChat):
        # The chat goes first: a crash part way through leaves run folders that no chat
        # lists, never a chat missing some of its turns.
        delete_chat(chats, chat["id"])
        await runs.remove(chat["id"])

    @app.post("/api/chats/{chat}/runs", status_code=HTTPStatus.CREATED)
    async def start_run(
        chat: KnownChat, prompt: Annotated[str, Body(embed=True, min_length=1)]
    ):
        # Before the chat's turns are read: a run that is going has no turn.end yet.
        if runs.live(chat["id"]) is not None:
            raise RunInProgress(chat["id"])
        starts = turn_starts(runs.home, chat["id"])
        # A chat stays in the namespace it started in.
        namespace = starts[0]["namespace"] if starts else default_namespace(library)
        earlier = [read_turn(runs.home, start["run"]) for start in starts]

        def config_for(folder):
            # The run gets the Library's tools as they are now, in a folder of its own.
            return engine_config(library, namespace, folder / "tools")

        run = runs.start(chat["id"], prompt, config_for, earlier)
        if not starts:
            title_new_chat(chats, chat["id"], prompt)
        return {"run": run}

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
        after: Annotated[int, Query(ge=0)] = 0,
        last_event_id: Annotated[int, Header(ge=0)] = 0,
    ):
        # A page catching up names the last seq it has in ?after=, as EventSource sends
        # no Last-Event-ID on its first connect; on a reconnect the header is newer.
        async for event in runs.events(run, after=max(after, last_event_id)):
            yield ServerSentEvent(data=event, id=str(event["seq"]))

    # A mount at / answers every path, so API routes must be added above it.
    app.mount("/", StaticFiles(directory=WEB, html=True))
    return app
