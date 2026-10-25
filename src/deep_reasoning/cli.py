"""The `deep-reasoning` command: serve the app on 127.0.0.1 and open it in a tab."""

import argparse
import contextlib
import errno
import socket
import sys
import threading
import webbrowser

import structlog
import uvicorn

from deep_reasoning.app import create_app

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_PORT = 65535

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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Start Deep Reasoning and open it in a browser tab."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the port to serve on (default {DEFAULT_PORT}; 0 picks a free one)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="don't open a browser tab"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= MAX_PORT:
        parser.error(f"--port must be between 0 and {MAX_PORT}")
    server = uvicorn.Server(uvicorn.Config(create_app()))
    with listen(args.port) as sock:
        url = f"http://{HOST}:{sock.getsockname()[1]}/"
        log.info("Deep Reasoning is running", url=url)
        if not args.no_browser:
            # The tab's request waits for uvicorn; a thread, as some launchers block.
            threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        # uvicorn re-raises Ctrl+C after a clean shutdown; uvicorn.run hides it too.
        with contextlib.suppress(KeyboardInterrupt):
            server.run(sockets=[sock])
