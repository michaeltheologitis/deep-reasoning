import queue
import socket
import urllib.parse
import webbrowser

import pytest
import uvicorn
from fastapi.testclient import TestClient

from deep_reasoning import cli

WAIT_SECONDS = 0.5


@pytest.fixture
def free_port():
    with socket.create_server(("127.0.0.1", 0)) as probe:
        return probe.getsockname()[1]


@pytest.fixture
def opened(monkeypatch):
    """The URLs the browser was asked to open; each must already accept connections."""
    urls = queue.Queue()

    def open_tab(url):
        address = urllib.parse.urlsplit(url)
        socket.create_connection((address.hostname, address.port)).close()
        urls.put(url)

    monkeypatch.setattr(webbrowser, "open", open_tab)
    return urls


@pytest.fixture
def served(monkeypatch):
    """The addresses uvicorn served on. The fake stops at once."""
    addresses = []

    def serve(server, sockets):
        addresses.append(sockets[0].getsockname())

    monkeypatch.setattr(uvicorn.Server, "run", serve)
    return addresses


def test_serves_on_localhost_only(served, free_port):
    cli.main(["--port", str(free_port), "--no-browser"])
    assert served == [("127.0.0.1", free_port)]


def test_says_where_it_runs_and_which_library_it_serves(
    served, capsys, home, free_port
):
    cli.main(["--port", str(free_port), "--no-browser"])
    said = capsys.readouterr().out
    assert f"url=http://127.0.0.1:{free_port}/" in said
    assert str(home / ".deep-reasoning" / "library.sqlite") in said


def test_opens_a_tab_at_the_port_it_listens_on(monkeypatch, opened):
    tabs = []

    def serve(server, sockets):
        port = sockets[0].getsockname()[1]
        tabs.append((opened.get(timeout=WAIT_SECONDS), port))

    monkeypatch.setattr(uvicorn.Server, "run", serve)
    cli.main(["--port", "0"])
    [(url, port)] = tabs
    assert url == f"http://127.0.0.1:{port}/"


def test_no_browser_opens_no_tab(monkeypatch, opened, free_port):
    def serve(server, sockets):
        with pytest.raises(queue.Empty):
            opened.get(timeout=WAIT_SECONDS)

    monkeypatch.setattr(uvicorn.Server, "run", serve)
    cli.main(["--port", str(free_port), "--no-browser"])


def test_a_taken_port_exits_with_a_plain_error_suggesting_another(served):
    with socket.create_server(("127.0.0.1", 0)) as taken:
        port = taken.getsockname()[1]
        with pytest.raises(SystemExit, match=f"Port {port} is already in use.*--port"):
            cli.main(["--port", str(port), "--no-browser"])
    assert served == []


@pytest.mark.parametrize("port", ["-1", "65536"])
def test_a_port_out_of_range_exits_with_a_plain_error(served, capsys, port):
    with pytest.raises(SystemExit):
        cli.main(["--port", port, "--no-browser"])
    assert "--port must be between 0 and 65535" in capsys.readouterr().err
    assert served == []


def test_ctrl_c_stops_the_server_without_a_traceback(monkeypatch, free_port):
    def interrupted(server, sockets):
        raise KeyboardInterrupt

    monkeypatch.setattr(uvicorn.Server, "run", interrupted)
    try:
        cli.main(["--port", str(free_port), "--no-browser"])
    except KeyboardInterrupt:
        pytest.fail("Ctrl+C escaped main, so the terminal shows a traceback")


def test_the_library_defaults_to_one_under_the_home_directory(served, home, free_port):
    cli.main(["--port", str(free_port), "--no-browser"])
    assert (home / ".deep-reasoning" / "library.sqlite").is_file()


def test_library_opens_the_given_file_and_import_fills_it(
    monkeypatch, tmp_path, advisors, free_port
):
    shared = tmp_path / "shared.sqlite"
    cli.main(["import", str(advisors), "--library", str(shared)])
    seen = []

    def serve(server, sockets):
        client = TestClient(server.config.app, base_url="http://127.0.0.1")
        seen.append(client.get("/api/library").json())

    monkeypatch.setattr(uvicorn.Server, "run", serve)
    cli.main(["--port", str(free_port), "--no-browser", "--library", str(shared)])
    [library] = seen
    assert library["file"] == "shared.sqlite"
    assert library["default_namespace"] == "router"


def test_a_failed_import_exits_with_a_plain_error(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(SystemExit, match="Could not import .*the Library is unchanged"):
        cli.main(["import", str(missing), "--library", str(tmp_path / "lib.sqlite")])
