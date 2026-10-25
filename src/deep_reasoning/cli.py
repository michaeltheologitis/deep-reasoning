"""The `deep-reasoning` command: serve the app on 127.0.0.1 and open it in a tab."""

import argparse
import errno
import http.client
import socket
import sys
import threading
import webbrowser

import structlog
import uvicorn

from deep_reasoning.app import create_app

HOST = "127.0.0.1"
DEFAULT_PORT = 8000

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


def open_browser_once_up(port, url):
    # The socket already listens, so this request waits until uvicorn answers it.
    connection = http.client.HTTPConnection(HOST, port)
    connection.request("GET", "/")
    connection.getresponse()
    connection.close()
    webbrowser.open(url)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Start Deep Reasoning and open it in a browser tab."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"the port to serve on (default {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="don't open a browser tab"
    )
    args = parser.parse_args(argv)
    url = f"http://{HOST}:{args.port}/"
    with listen(args.port) as sock:
        if not args.no_browser:
            threading.Thread(
                target=open_browser_once_up, args=(args.port, url), daemon=True
            ).start()
        log.info("Deep Reasoning is running", url=url)
        uvicorn.Server(uvicorn.Config(create_app())).run(sockets=[sock])
