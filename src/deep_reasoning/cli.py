"""The `deep-reasoning` command: serve the app on 127.0.0.1 and open it in a tab, or import a config into the Library."""

import argparse
import contextlib
import errno
import logging
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
from deep_reasoning.library import LibraryError, import_config, open_library

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_PORT = 65535
LIBRARY_DIR = ".deep-reasoning"
LIBRARY_FILE = "library.sqlite"

log = structlog.get_logger()


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


def serve(port, no_browser, library):
    open_or_exit(library).close()
    server = uvicorn.Server(uvicorn.Config(create_app(library)))
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
    parser = argparse.ArgumentParser(
        description="Start Deep Reasoning and open it in a browser tab."
    )
    default_library = Path.home() / LIBRARY_DIR / LIBRARY_FILE
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
    # SUPPRESS keeps a --library given before `import` from being reset to the default.
    importer.add_argument(
        "--library", type=Path, default=argparse.SUPPRESS, help=library_help
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= MAX_PORT:
        parser.error(f"--port must be between 0 and {MAX_PORT}")
    if args.command == "import":
        import_or_exit(args.library, args.config)
        return
    serve(args.port, args.no_browser, args.library)
