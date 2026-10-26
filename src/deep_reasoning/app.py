"""The web app: the Library's, the settings', the folders', the chats' and the runs' API, and the UI's static files at /."""

import asyncio
from contextlib import asynccontextmanager, closing
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from fastapi import Path as InPath
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, StringConstraints
from starlette.middleware.trustedhost import TrustedHostMiddleware

from deep_reasoning.chats import (
    CHAT_ID,
    CHATS_FILE,
    choose,
    choose_folder,
    create_chat,
    delete_chat,
    find_chat,
    list_chats,
    rename_chat,
    title_new_chat,
)
from deep_reasoning.folders import (
    FolderError,
    chosen_folder,
    list_folders,
    remove_unless_kept,
    scratch_folder,
    short_path,
    working_folder,
)
from deep_reasoning.library import (
    LibraryError,
    add_decomposition,
    add_namespace,
    change_namespace,
    check_namespace,
    default_namespace,
    delete_namespace,
    engine_config,
    has_namespace,
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
from deep_reasoning.settings import (
    Provider,
    SettingsError,
    add_server,
    default_folder,
    drop_key,
    find_provider,
    model_lists,
    provider_list,
    remember_pick,
    remove_server,
    run_key,
    save_default_folder,
    save_key,
    starting_model,
    update_server,
)

WEB = Path(__file__).parent / "web"
# Requests naming any other host are refused, so a web page can't reach the API by DNS rebinding.
LOCAL_HOSTS = ["127.0.0.1", "localhost"]
MODEL_NAME = r"^[^\x00-\x1f\x7f]{1,200}$"

log = structlog.get_logger()

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ModelPick(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    name: Annotated[str, StringConstraints(strip_whitespace=True, pattern=MODEL_NAME)]


class ChatChange(BaseModel):
    """What a PATCH of a chat may change: its title; its namespace, model or folder, from
    its next message. A folder sent as null or blank is its scratch folder."""

    model_config = ConfigDict(extra="forbid")
    title: Title | None = None
    namespace: str | None = None
    model: ModelPick | None = None
    folder: str | None = None


def shown_folder(folder):
    """A folder kept as an absolute path, as the page shows it; None stays None."""
    return None if folder is None else short_path(Path(folder))


def same_origin(
    host: Annotated[str, Header()] = "",
    origin: Annotated[str | None, Header()] = None,
):
    """Refuse a request another site's page sent: a browser names the page's origin, and
    the app's own pages are served from the host they ask."""
    if origin is not None and origin != f"http://{host}":
        raise HTTPException(
            HTTPStatus.FORBIDDEN, "Requests from other sites are refused."
        )


def keep_namespaces(chats, home):
    """Give each chat from before chats.sqlite kept namespaces the one its runs used, so
    it doesn't move to the Library's default."""
    for chat in list_chats(chats):
        starts = [] if chat["namespace"] else turn_starts(home, chat["id"])
        if starts:
            choose(chats, chat["id"], namespace=starts[-1]["namespace"])


def create_app(library, home):
    """The app over the Library file at *library*, which each request opens afresh,
    keeping its chats and runs under *home*."""
    library = Path(library)
    home = Path(home)
    chats = home / CHATS_FILE
    runs = Runs(home)

    @asynccontextmanager
    async def lifespan(app):
        for run in end_unfinished(runs.home):
            log.warning("Ended a run the app stopped under", run=run)
        keep_namespaces(chats, runs.home)
        yield
        await runs.close()

    app = FastAPI(lifespan=lifespan, dependencies=[Depends(same_origin)])
    app.state.runs = runs
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=LOCAL_HOSTS)

    @app.exception_handler(LibraryError)
    @app.exception_handler(SettingsError)
    @app.exception_handler(FolderError)
    async def refused(request, error):
        return JSONResponse({"detail": str(error)}, status_code=HTTPStatus.BAD_REQUEST)

    @app.exception_handler(RequestValidationError)
    async def malformed(request, error):
        # FastAPI's own answer repeats what was sent; a key sent in the wrong shape mustn't come back.
        errors = [
            {name: value for name, value in each.items() if name != "input"}
            for each in error.errors()
        ]
        return JSONResponse(
            {"detail": jsonable_encoder(errors)},
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    @app.exception_handler(RunInProgress)
    async def busy(request, error):
        detail = f"Chat {error} has a run going."
        return JSONResponse({"detail": detail}, status_code=HTTPStatus.CONFLICT)

    def library_panel(connection):
        return {"file": library.name, **panel(connection)}

    @app.get("/api/library")
    def read_library():
        with closing(open_library(library)) as connection:
            return library_panel(connection)

    @app.post("/api/decompositions", status_code=HTTPStatus.CREATED)
    def post_decomposition(
        namespace: Annotated[str, Body()], yaml: Annotated[str, Body()]
    ):
        with closing(open_library(library)) as connection:
            return add_decomposition(connection, namespace, yaml)

    # Each answers with the whole Library: a namespace's fields reach every namespace under it.
    # An imported namespace's name may hold a /, hence :path.
    @app.post("/api/namespaces", status_code=HTTPStatus.CREATED)
    def post_namespace(name: Annotated[str, Body()], yaml: Annotated[str, Body()]):
        with closing(open_library(library)) as connection:
            add_namespace(connection, name, yaml)
            return library_panel(connection)

    @app.put("/api/namespaces/{name:path}")
    def put_namespace(name: str, yaml: Annotated[str, Body(embed=True)]):
        with closing(open_library(library)) as connection:
            change_namespace(connection, name, yaml)
            return library_panel(connection)

    @app.delete("/api/namespaces/{name:path}")
    def remove_namespace(name: str, decompositions: Annotated[int, Query(ge=0)]):
        with closing(open_library(library)) as connection:
            delete_namespace(connection, name, decompositions)
            return library_panel(connection)

    def known_provider(name: str):
        found = find_provider(home, name)
        if found is None:
            raise HTTPException(HTTPStatus.NOT_FOUND, f"There is no provider {name}.")
        return found

    def known_server(name: str):
        found = known_provider(name)
        if not found.custom:
            raise HTTPException(
                HTTPStatus.NOT_FOUND, f"There is no custom server {name}."
            )
        return found

    KnownProvider = Annotated[Provider, Depends(known_provider)]
    KnownServer = Annotated[Provider, Depends(known_server)]

    @app.get("/api/providers")
    async def read_providers():
        return provider_list(home)

    @app.put("/api/providers/{name}/key")
    async def put_key(
        provider: KnownProvider,
        key: Annotated[str, Body(embed=True)],
    ):
        save_key(home, provider, key)
        return provider_list(home)

    @app.delete("/api/providers/{name}/key")
    async def delete_key(provider: KnownProvider):
        drop_key(home, provider.key_env)
        return provider_list(home)

    @app.post("/api/servers", status_code=HTTPStatus.CREATED)
    async def post_server(
        name: Annotated[str, Body()],
        base_url: Annotated[str, Body()],
        key: Annotated[str | None, Body()] = None,
    ):
        add_server(home, name, base_url, key)
        return provider_list(home)

    @app.put("/api/servers/{name}")
    async def put_server(
        server: KnownServer,
        base_url: Annotated[str, Body()],
        key: Annotated[str | None, Body()] = None,
    ):
        update_server(home, server, base_url, key)
        return provider_list(home)

    @app.delete("/api/servers/{name}")
    async def delete_server(server: KnownServer):
        remove_server(home, server)
        return provider_list(home)

    @app.get("/api/models")
    async def read_models():
        return await model_lists(home)

    @app.get("/api/folders")
    def read_folders(path: str = "~"):
        return list_folders(path)

    # Coroutines, as every writer of settings.json is, so no two rewrites race.
    @app.get("/api/default-folder")
    async def read_default_folder():
        return {"folder": shown_folder(default_folder(home))}

    @app.put("/api/default-folder")
    async def put_default_folder(folder: Annotated[str | None, Body(embed=True)]):
        save_default_folder(home, chosen_folder(folder))
        return await read_default_folder()

    def starting_points():
        """Where a chat that hasn't picked starts: the Library's default namespace, and the
        model new chats start on."""
        return default_namespace(library), starting_model(home)

    def shown(chat, starts):
        """A chat as the API gives it: with the id of its run that is going, if one is, and
        the namespace and model its next message runs on."""
        namespace, model = starts
        if chat["model"] is not None:
            model = {"provider": chat["provider"], "name": chat["model"]}
        return {
            "id": chat["id"],
            "title": chat["title"],
            "created": chat["created"],
            "live": runs.live(chat["id"]),
            "namespace": chat["namespace"] or namespace,
            "model": model,
            "folder": shown_folder(chat["folder"]),
            "scratch_folder": short_path(scratch_folder(home, chat["id"])),
        }

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
        starts = starting_points()
        return [shown(chat, starts) for chat in list_chats(chats)]

    @app.post("/api/chats", status_code=HTTPStatus.CREATED)
    async def post_chat():
        return shown(create_chat(chats, default_folder(home)), starting_points())

    @app.get("/api/chats/{chat}")
    async def read_chat(chat: KnownChat):
        turns = [
            {"run": start["run"], "events": list(read_events(runs.home, start["run"]))}
            for start in turn_starts(runs.home, chat["id"])
        ]
        return shown(chat, starting_points()) | {"turns": turns}

    @app.patch("/api/chats/{chat}")
    async def patch_chat(chat: KnownChat, change: ChatChange):
        if change.namespace is not None:
            with closing(open_library(library)) as connection:
                check_namespace(connection, change.namespace)
        model = change.model
        if model is not None and find_provider(home, model.provider) is None:
            raise SettingsError(f"There is no provider {model.provider}.")
        moved = "folder" in change.model_fields_set
        folder = chosen_folder(change.folder) if moved else None
        if change.title is not None:
            rename_chat(chats, chat["id"], change.title)
        provider, name = (model.provider, model.name) if model else (None, None)
        choose(chats, chat["id"], change.namespace, provider, name)
        if moved:
            choose_folder(chats, chat["id"], folder)
        if model is not None:
            remember_pick(home, provider, name)
        return shown(find_chat(chats, chat["id"]), starting_points())

    @app.delete("/api/chats/{chat}", status_code=HTTPStatus.NO_CONTENT)
    async def remove_chat(chat: KnownChat):
        # Read before anything goes, so settings that can't be read delete nothing.
        chosen = [each["folder"] for each in list_chats(chats)]
        chosen += [default_folder(home), *runs.folders_in_use(besides=chat["id"])]
        keep = [each for each in chosen if each]
        # The chat goes first: a crash part way through leaves run folders that no chat
        # lists, never a chat missing some of its turns.
        delete_chat(chats, chat["id"])
        await runs.remove(chat["id"], keep)
        # After its workers exit, as they work in it; off the loop, as it may be large.
        scratch = scratch_folder(home, chat["id"])
        await asyncio.to_thread(remove_unless_kept, scratch, keep)

    @app.post("/api/chats/{chat}/runs", status_code=HTTPStatus.CREATED)
    async def start_run(
        chat: KnownChat, prompt: Annotated[str, Body(embed=True, min_length=1)]
    ):
        # Before the chat's turns are read: a run that is going has no turn.end yet.
        if runs.live(chat["id"]) is not None:
            raise RunInProgress(chat["id"])
        chosen = shown(chat, starting_points())
        namespace, model = chosen["namespace"], chosen["model"]
        with closing(open_library(library)) as connection:
            if not has_namespace(connection, namespace):
                raise LibraryError(
                    f"This chat's namespace {namespace} no longer exists — pick another."
                )
        if model is None:
            raise SettingsError("Pick a model for this chat, under the message box.")
        provider = find_provider(home, model["provider"])
        if provider is None:
            raise SettingsError(
                f"There is no provider {model['provider']} any more; pick another model."
            )
        key = run_key(home, provider)
        folder = working_folder(home, chat)
        starts = turn_starts(runs.home, chat["id"])
        earlier = [read_turn(runs.home, start["run"]) for start in starts]
        client = {"base_url": provider.base_url, "api_key_env": provider.key_env}

        def config_for(run_folder):
            # The Library's tools as they are now, in a folder of its own; the chat's model.
            config = engine_config(library, namespace, run_folder / "tools")
            return config | {"model": model["name"], "client": client}

        keys = {provider.key_env: key}
        run = runs.start(
            chat["id"], prompt, config_for, earlier, provider.name, keys, folder
        )
        choose(chats, chat["id"], namespace, provider.name, model["name"])
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
        # EventSource sends no Last-Event-ID on its first connect, hence ?after=.
        async for event in runs.events(run, after=max(after, last_event_id)):
            yield ServerSentEvent(data=event, id=str(event["seq"]))

    # A mount at / answers every path, so API routes must be added above it.
    app.mount("/", StaticFiles(directory=WEB, html=True))
    return app
