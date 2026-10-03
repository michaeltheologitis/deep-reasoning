"""The panel's browser tests: a real dr-library serve over a Library of our own, and
Chromium driving the frame UI it serves (D3 §7.3)."""

import functools
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode

import pytest
from playwright.sync_api import Browser, Error, Page, expect, sync_playwright

from deep_reasoning.library import Library, library_path, store

FIXTURE = Path(__file__).parent / "fixtures" / "library" / "main.yaml"
DR_LIBRARY = Path(sys.executable).parent / "dr-library"
# The agent-server starts an App backend with only these variables from its environment.
BACKEND_ENV = ("PATH", "LANG", "TMPDIR")
READY_S = 30
SAFETY_ACK = "localStorage.setItem('dr-library.safety-acknowledged', '1')"
# The frame polls /health every 3 s; a change made elsewhere shows within one poll.
expect.set_options(timeout=10_000)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def get_json(url: str) -> dict:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=5) as response:
        return json.load(response)


@dataclass(frozen=True)
class LibraryServer:
    url: str  # http://127.0.0.1:<port>
    home: Path
    process: subprocess.Popen[bytes]

    def library(self) -> Library:
        """Library.open on the same file, for asserting what was stored."""
        return Library.open(library_path(self.home))


@pytest.fixture
def library_home(tmp_path: Path) -> Path:
    """A Library at tmp_path/home holding fixtures/library (imported, starter=False)."""
    home = tmp_path / "home"
    Library.open(library_path(home), starter=False).import_config(FIXTURE)
    return home


def serve(home: Path) -> LibraryServer:
    """dr-library serve on a free port, environment PATH, LANG and TMPDIR only; waits for
    /health."""
    port = free_port()
    env = {name: os.environ[name] for name in BACKEND_ENV if name in os.environ}
    process = subprocess.Popen(
        [str(DR_LIBRARY), "serve", "--port", str(port), "--home", str(home)],
        env=env,
        cwd=home,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    server = LibraryServer(url=f"http://127.0.0.1:{port}", home=home, process=process)
    deadline = time.monotonic() + READY_S
    while True:
        try:
            get_json(f"{server.url}/health")
            return server
        except (OSError, urllib.error.URLError):
            if process.poll() is not None:
                raise RuntimeError(process.stderr.read().decode()) from None
            if time.monotonic() > deadline:
                process.kill()
                raise
            time.sleep(0.1)


def stop(server: LibraryServer) -> None:
    server.process.terminate()
    try:
        server.process.wait(10)
    except subprocess.TimeoutExpired:
        server.process.kill()
        server.process.wait()


@pytest.fixture
def library_server(library_home: Path) -> Iterator[LibraryServer]:
    server = serve(library_home)
    yield server
    stop(server)


# Module scope: while Playwright's sync API is started, its event loop counts as running
# in this thread, so asyncio.run (D1's harness) fails until it stops.
@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    """Chromium; skips with a reason when Playwright's browser is missing, fails when CI is
    set."""
    playwright = sync_playwright().start()
    try:
        chromium = playwright.chromium.launch()
    except Error as error:
        playwright.stop()
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Playwright's Chromium is not installed here: {error.message}")
    yield chromium
    chromium.close()
    playwright.stop()


def ui_url(base: str, **params: str | bool) -> str:
    query = {k: ("1" if v is True else v) for k, v in params.items() if v is not False}
    return f"{base}/ui/?{urlencode(query)}" if query else f"{base}/ui/"


@pytest.fixture
def open_ui(
    browser: Browser, library_server: LibraryServer
) -> Iterator[Callable[..., Page]]:
    """open_ui(tab="create", namespace="router", started=True, cap="5") → a page at /ui/?…,
    standalone, notice acknowledged unless notice=True is passed."""
    contexts = []

    def open_page(*, notice: bool = False, **params: str | bool) -> Page:
        context = browser.new_context()
        contexts.append(context)
        if not notice:
            context.add_init_script(SAFETY_ACK)
        page = context.new_page()
        page.goto(ui_url(library_server.url, **params))
        return page

    yield open_page
    for context in contexts:
        context.close()


def text(data: dict) -> str:
    return json.dumps(data)


def write_new(page: Page, name: str, task: str, code: str = "FinalAnswer(1)") -> None:
    """In Create decomposition: a name, the task card and the step's code."""
    page.get_by_test_id("dr-name").fill(name)
    page.get_by_test_id("dr-card-0-task").fill(task)
    page.get_by_test_id("dr-card-1-code").fill(code)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return None


@pytest.fixture
def parent_site(tmp_path: Path) -> Iterator[Callable[[dict[str, str]], str]]:
    """parent_site({"name": content, ...}) serves the files on another site than the
    frame's, http://localhost:<port>/, as Canvas's page is; returns that origin."""
    root = tmp_path / "parent"
    root.mkdir()
    handler = functools.partial(_QuietHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def publish(files: dict[str, str]) -> str:
        for name, content in files.items():
            (root / name).write_text(content)
        return f"http://localhost:{server.server_address[1]}"

    yield publish
    server.shutdown()
    server.server_close()


def stale_head(server: LibraryServer) -> None:
    """A head that no longer validates under the installed deep_reasoner, as after an
    upgrade: written to the store directly, since the Library refuses to write one."""
    with store.write(server.library().path, "test", "stale head") as w:
        w.add(
            "namespace",
            "router.archive",
            yaml="name: router.archive\nretired_key: 1\n",
            attached=[],
        )
