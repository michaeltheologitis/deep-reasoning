import io
import os
import queue
import shutil
import socket
import sys
import urllib.parse
import webbrowser

import pytest
import structlog
import uvicorn
from fastapi.testclient import TestClient

from deep_reasoning import cli
from deep_reasoning.chats import create_chat
from deep_reasoning.folders import data_folder
from deep_reasoning.library import open_library

WAIT_SECONDS = 0.5
KEY_IN_A_FRAME = "sk-held-in-a-frame"
KEYS = "OPENAI_API_KEY=sk-kept-by-reset\n"


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


def test_a_traceback_the_server_logs_shows_no_frames_variables(
    served, capsys, free_port
):
    cli.main(["--port", str(free_port), "--no-browser"])

    def refused(key):
        raise RuntimeError("the provider refused")

    try:
        refused(KEY_IN_A_FRAME)
    except RuntimeError:
        structlog.get_logger().exception("models.not_listed")
    said = capsys.readouterr().out
    assert "RuntimeError: the provider refused" in said
    assert KEY_IN_A_FRAME not in said


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


def test_a_file_that_is_not_a_library_exits_with_a_plain_error(
    served, tmp_path, free_port
):
    notes = tmp_path / "notes.txt"
    notes.write_text("not a database\n")
    with pytest.raises(SystemExit, match="Could not open the Library at .*notes.txt"):
        cli.main(["--port", str(free_port), "--no-browser", "--library", str(notes)])
    assert served == []


class Terminal(io.StringIO):
    """Standard input from a person at a terminal, who types what it holds."""

    def isatty(self):
        return True


def app_file(app_home, library):
    """A Library at *library* with its data folder, and what older versions left in
    *app_home*: the paths a reset deletes, but SQLite's side files."""
    open_library(library).close()
    data = data_folder(app_home, library)
    (data / "work" / "some-chat").mkdir(parents=True)
    (data / "runs" / "some-run").mkdir(parents=True)
    old_files = [app_home / "chats.sqlite", app_home / "settings.json"]
    for path in old_files:
        path.write_text("left by an older version\n")
    old_folders = [app_home / "runs", app_home / "work"]
    for folder in old_folders:
        (folder / "old").mkdir(parents=True)
    return [library, data, *old_files, *old_folders]


def test_reset_yes_deletes_the_app_file_its_folders_and_old_leftovers(
    app_home, tmp_path
):
    library = app_home / "library.sqlite"
    project = tmp_path / "project"
    project.mkdir()
    create_chat(library, folder=str(project))
    doomed = app_file(app_home, library)
    for side in ("-wal", "-shm", "-journal"):
        side_file = library.with_name(library.name + side)
        side_file.write_text("left by a crash\n")
        doomed.append(side_file)
    keys = app_home / ".env"
    keys.write_text(KEYS)
    other = data_folder(app_home, tmp_path / "other.sqlite")
    other.mkdir(parents=True)
    cli.main(["reset", "--yes"])
    assert [path for path in doomed if os.path.lexists(path)] == []
    assert keys.read_text() == KEYS
    assert project.is_dir()
    assert other.is_dir()


@pytest.mark.parametrize("answer", ["no\n", "yes\n", "\n", "delete it\n", ""])
def test_reset_lists_what_goes_and_deletes_nothing_unless_told_delete(
    app_home, monkeypatch, capsys, answer
):
    library = app_home / "library.sqlite"
    doomed = app_file(app_home, library)
    monkeypatch.setattr(sys, "stdin", Terminal(answer))
    with pytest.raises(SystemExit, match="Nothing was deleted"):
        cli.main(["reset"])
    said = capsys.readouterr().out
    assert "~/.deep-reasoning/library.sqlite" in said
    assert "~/.deep-reasoning/chats.sqlite" in said
    assert "~/.deep-reasoning/.env" in said
    assert "Stop Deep Reasoning" in said
    assert all(os.path.lexists(path) for path in doomed)


def test_typing_delete_resets(app_home, monkeypatch):
    library = app_home / "library.sqlite"
    doomed = app_file(app_home, library)
    monkeypatch.setattr(sys, "stdin", Terminal("delete\n"))
    cli.main(["reset"])
    assert [path for path in doomed if os.path.lexists(path)] == []


def test_reset_without_a_terminal_or_yes_deletes_nothing(app_home, monkeypatch):
    library = app_home / "library.sqlite"
    doomed = app_file(app_home, library)
    monkeypatch.setattr(sys, "stdin", io.StringIO("delete\n"))
    with pytest.raises(SystemExit, match="no terminal.*--yes"):
        cli.main(["reset"])
    assert all(os.path.lexists(path) for path in doomed)


@pytest.mark.parametrize("before", [True, False], ids=["before reset", "after reset"])
def test_reset_library_resets_that_file_not_the_default(app_home, tmp_path, before):
    default = app_home / "library.sqlite"
    open_library(default).close()
    shared = tmp_path / "shared.sqlite"
    open_library(shared).close()
    option = ["--library", str(shared)]
    cli.main([*option, "reset", "--yes"] if before else ["reset", "--yes", *option])
    assert not shared.exists()
    assert default.is_file()


def test_reset_with_nothing_there_says_so(app_home, capsys):
    app_home.mkdir()
    keys = app_home / ".env"
    keys.write_text(KEYS)
    cli.main(["reset"])
    assert "Nothing to reset" in capsys.readouterr().out
    assert keys.read_text() == KEYS


def test_reset_never_deletes_through_a_symlink(app_home, tmp_path):
    library = app_home / "library.sqlite"
    app_file(app_home, library)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "notes.txt").write_text("mine\n")
    data = data_folder(app_home, library)
    (data / "work" / "some-chat" / "link").symlink_to(outside)
    shutil.rmtree(app_home / "runs")
    (app_home / "runs").symlink_to(outside)
    cli.main(["reset", "--yes"])
    assert (outside / "notes.txt").read_text() == "mine\n"
    assert not data.exists()
    assert not os.path.lexists(app_home / "runs")


def test_reset_keeps_a_folder_holding_one_a_chat_chose(app_home):
    library = app_home / "library.sqlite"
    old_scratch = app_home / "work" / "old-chat"
    old_scratch.mkdir(parents=True)
    create_chat(library, folder=str(old_scratch))
    cli.main(["reset", "--yes"])
    assert old_scratch.is_dir()
    assert not library.exists()


def test_reset_refuses_a_file_that_is_not_a_library(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("not a database\n")
    with pytest.raises(SystemExit, match="Could not read .*notes.txt.*nothing was"):
        cli.main(["reset", "--yes", "--library", str(notes)])
    assert notes.read_text() == "not a database\n"
