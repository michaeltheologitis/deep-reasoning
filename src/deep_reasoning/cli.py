"""The `deep-reasoning` command: serve the app on 127.0.0.1 and open it in a tab, import a
config into the Library, or reset: delete the Library file and its folders."""

import argparse
import contextlib
import errno
import logging
import os
import shutil
import socket
import sqlite3
import sys
import threading
import webbrowser
from pathlib import Path

import structlog
import uvicorn
import yaml

from deep_reasoning.app import create_app
from deep_reasoning.chats import list_chats
from deep_reasoning.folders import data_folder, holds_any, short_path
from deep_reasoning.library import LibraryError, import_config, open_library
from deep_reasoning.settings import ENV_FILE, default_folder

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_PORT = 65535
# The app's home: its runs, scratch folders and keys, and its app file by default.
HOME_DIR = ".deep-reasoning"
LIBRARY_FILE = "library.sqlite"
# SQLite's files beside an app file: while it is open, or after a crash.
SIDE_FILES = ("-wal", "-shm", "-journal")
# What versions before the app file kept directly in the app's home, unread since.
LEFTOVERS = ("chats.sqlite", "settings.json", "runs", "work")
CONFIRMATION = "delete"

log = structlog.get_logger()


class Server(uvicorn.Server):
    """uvicorn's server, ending the runs before it waits on open responses: a run's
    stream stays open until the run ends, so uvicorn would wait on it for good."""

    async def shutdown(self, sockets=None):
        await self.config.app.state.runs.close()
        await super().shutdown(sockets)


def listen(port):
    """A socket listening on HOST:port, or a plain error when the port is taken."""
    try:
        return socket.create_server((HOST, port))
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        sys.exit(
            f"Port {port} is already in use. Pick another with --port, "
            f"for example: deep-reasoning --port {port + 1}"
        )


def open_or_exit(path):
    """The Library at *path*, created if new, or a plain error when it can't be one."""
    try:
        return open_library(path)
    except (OSError, sqlite3.Error, LibraryError) as error:
        sys.exit(f"Could not open the Library at {path}: {error}")


def import_or_exit(library, config):
    with contextlib.closing(open_or_exit(library)) as connection:
        try:
            imported = import_config(connection, config)
        except (OSError, ValueError, yaml.YAMLError, sqlite3.Error) as error:
            sys.exit(f"Could not import {config}; the Library is unchanged.\n{error}")
    log.info(
        "Imported into the Library",
        config=str(config),
        library=str(library),
        **imported,
    )


def chosen_or_exit(library):
    """The folders the Library's chats and settings chose, which a reset never deletes; a
    plain error, deleting nothing, when the file isn't a Library it can read."""
    if not library.is_file():
        return []
    try:
        chosen = [chat["folder"] for chat in list_chats(library)]
        chosen.append(default_folder(library))
    except (OSError, sqlite3.Error, LibraryError) as error:
        sys.exit(
            f"Could not read the Library at {library}, so nothing was deleted: {error}"
        )
    return [folder for folder in chosen if folder]


def reset_plan(doomed, kept, home):
    lines = [
        "Stop Deep Reasoning before a reset: deleting its Library while it runs breaks it.",
        "",
        "This deletes the Library file, with its namespaces, decompositions, tools, chats and",
        "settings; its runs' and chats' scratch folders; and what older versions left:",
        *(f"  {short_path(path)}" for path in doomed),
        *(
            f"It keeps {short_path(path)}, as a chat chose it or a folder in it."
            for path in kept
        ),
        f"It keeps your keys, in {short_path(home / ENV_FILE)} (remove them in settings),",
        "every folder a chat chose, and other Library files and their folders.",
    ]
    return "\n".join(lines)


def confirmed():
    """Whether the person at the terminal typed the confirmation; Ctrl+C or Ctrl+D is a no."""
    if not sys.stdin.isatty():
        sys.exit(
            "There is no terminal to ask on, so nothing was deleted. "
            "Pass --yes to reset without asking."
        )
    try:
        return input(f"Type {CONFIRMATION} to delete them: ").strip() == CONFIRMATION
    except (EOFError, KeyboardInterrupt):
        return False


def delete(path):
    """Delete *path*, a folder with all it holds; a symlink only as itself, even one to a
    folder, so nothing is deleted through one."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def reset_or_exit(library, home, yes):
    """Delete the app file at *library*, its SQLite side files and its data folder, and what
    older versions left in the app's *home*, once it has said what goes and what stays and,
    unless *yes*, been told to."""
    paths = [library, *(library.with_name(library.name + side) for side in SIDE_FILES)]
    paths += [data_folder(home, library), *(home / name for name in LEFTOVERS)]
    # Listed before the Library is read: closing it can delete a side file left over.
    there = [path for path in paths if os.path.lexists(path)]
    chosen = chosen_or_exit(library)
    kept = [path for path in there if holds_any(path, chosen)]
    doomed = [path for path in there if path not in kept]
    if not doomed:
        print(
            f"Nothing to reset: no Library at {short_path(library)}, nor folders of it."
        )
        return
    print(reset_plan(doomed, kept, home))
    if not yes and not confirmed():
        sys.exit("Nothing was deleted.")
    for path in doomed:
        try:
            delete(path)
        except OSError as error:
            sys.exit(f"Could not delete {short_path(path)}: {error}")
    print(
        "Deleted them. The next start makes a fresh Library, "
        "with history at root and the librarian namespace."
    )


def serve(port, no_browser, library, home):
    open_or_exit(library).close()
    server = Server(uvicorn.Config(create_app(library, home)))
    with listen(port) as sock:
        url = f"http://{HOST}:{sock.getsockname()[1]}/"
        log.info("Deep Reasoning is running", url=url, library=str(library))
        if not no_browser:
            # The tab's request waits for uvicorn; a thread, as some launchers block.
            threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        # uvicorn re-raises Ctrl+C after a clean shutdown; uvicorn.run hides it too.
        with contextlib.suppress(KeyboardInterrupt):
            server.run(sockets=[sock])


def main(argv=None):
    # Importing deep_reasoner quiets structlog to warnings; this command's lines are info.
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
    )
    # Tracebacks without each frame's variables: a frame may hold a key.
    structlog.dev.ConsoleRenderer.get_active().exception_formatter = (
        structlog.dev.plain_traceback
    )
    parser = argparse.ArgumentParser(
        description="Start Deep Reasoning and open it in a browser tab."
    )
    home = Path.home() / HOME_DIR
    default_library = home / LIBRARY_FILE
    library_help = f"the Library file to use (default {default_library})"
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the port to serve on (default {DEFAULT_PORT}; 0 picks a free one)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="don't open a browser tab"
    )
    parser.add_argument(
        "--library", type=Path, default=default_library, help=library_help
    )
    commands = parser.add_subparsers(dest="command", metavar="command")
    importer = commands.add_parser(
        "import",
        help="read a deep_reasoner config into the Library, then exit",
        description="Read a deep_reasoner config into the Library, replacing same-named items.",
    )
    importer.add_argument("config", type=Path, help="the config's main YAML file")
    resetter = commands.add_parser(
        "reset",
        help="delete the Library file and its run and scratch folders, after asking",
        description=(
            "Delete the Library file (its namespaces, decompositions, tools, chats and "
            "settings), its runs' and chats' scratch folders, and what older versions "
            "left in the app's home, after asking. Your keys and the folders chats chose "
            "stay. Stop the app first."
        ),
    )
    resetter.add_argument("--yes", action="store_true", help="delete without asking")
    for command in (importer, resetter):
        # SUPPRESS keeps a --library given before the command from being reset to the default.
        command.add_argument(
            "--library", type=Path, default=argparse.SUPPRESS, help=library_help
        )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= MAX_PORT:
        parser.error(f"--port must be between 0 and {MAX_PORT}")
    if args.command == "import":
        import_or_exit(args.library, args.config)
        return
    if args.command == "reset":
        reset_or_exit(args.library, home, args.yes)
        return
    serve(args.port, args.no_browser, args.library, home)
