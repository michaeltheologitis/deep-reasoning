import contextlib
import queue
import socket
import webbrowser

import pytest
import uvicorn

from deep_reasoning import cli

GRACE_SECONDS = 0.5
REQUEST_BYTES = 4096
OK_RESPONSE = b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"


def answer_one_request(listener):
    """Answer the request that arrives within GRACE_SECONDS, as uvicorn would."""
    listener.settimeout(GRACE_SECONDS)
    with contextlib.suppress(TimeoutError):
        connection, _ = listener.accept()
        with connection:
            connection.recv(REQUEST_BYTES)
            connection.sendall(OK_RESPONSE)


@pytest.fixture
def free_port():
    with socket.create_server(("127.0.0.1", 0)) as probe:
        return probe.getsockname()[1]


@pytest.fixture
def opened(monkeypatch):
    """The URLs the browser was asked to open."""
    urls = queue.Queue()
    monkeypatch.setattr(webbrowser, "open", urls.put)
    return urls


@pytest.fixture
def served(monkeypatch):
    """The addresses uvicorn served on. The fake answers one request, then stops."""
    addresses = []

    def serve(server, sockets):
        addresses.append(sockets[0].getsockname())
        answer_one_request(sockets[0])

    monkeypatch.setattr(uvicorn.Server, "run", serve)
    return addresses


def test_serves_on_localhost_only(served, free_port):
    cli.main(["--port", str(free_port), "--no-browser"])
    assert served == [("127.0.0.1", free_port)]


def test_opens_the_browser_at_the_app_url_once_the_server_answers(
    monkeypatch, opened, free_port
):
    def start_slowly(server, sockets):
        with pytest.raises(queue.Empty):
            opened.get(timeout=GRACE_SECONDS)
        answer_one_request(sockets[0])

    monkeypatch.setattr(uvicorn.Server, "run", start_slowly)
    cli.main(["--port", str(free_port)])
    assert opened.get(timeout=GRACE_SECONDS) == f"http://127.0.0.1:{free_port}/"


def test_no_browser_opens_no_tab(served, opened, free_port):
    cli.main(["--port", str(free_port), "--no-browser"])
    with pytest.raises(queue.Empty):
        opened.get(timeout=GRACE_SECONDS)


def test_a_taken_port_exits_with_a_plain_error_suggesting_another(served):
    with socket.create_server(("127.0.0.1", 0)) as taken:
        port = taken.getsockname()[1]
        with pytest.raises(SystemExit, match=f"Port {port} is already in use.*--port"):
            cli.main(["--port", str(port), "--no-browser"])
    assert served == []
