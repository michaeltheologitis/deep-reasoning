"""The browser command's smokes (TASK-48 §7.6): its first start, from a fresh HOME, gets
the Library App's backend ready and Ctrl+C leaves nothing; and, on a Mac, the Python
uvx picks reaches GitHub's release downloads (W4).

DR_WEB_TARBALL names a tarball build.py web made to run the command on; without one,
the command downloads the release's own, as a user's does, at DR_WEB_COMMIT (a release's
commit; the checkout's HEAD by default). It starts no conversation, so no model is
called.
"""

import json
import os
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from desktop import build
from dr_web.cli import command_for
from tests.desktop.app import (
    FIRST_LAUNCH_S,
    fresh_home,
    interrupt,
    launch_web,
    processes_mentioning,
    user_environment,
    web_command,
)

pytestmark = pytest.mark.web

BACKEND = "/api/canvas-extensions/installed/dr-library/backend"
RUNNING = "Deep Reasoning is running at "
TARBALL = (
    Path(os.environ["DR_WEB_TARBALL"]) if os.environ.get("DR_WEB_TARBALL") else None
)
COMMIT = (
    os.environ.get("DR_WEB_COMMIT")
    or build.git("rev-parse", "HEAD", cwd=build.REPO).strip()
)
STOPPED_S = 10.0
DOWNLOAD_S = 120.0
# dr_web.cache.download, in the interpreter uvx picks for the command's own package.
DOWNLOAD = (
    "import sys; from pathlib import Path; from dr_web.cache import download; "
    "download(sys.argv[1], Path(sys.argv[2]))"
)


@dataclass
class FirstStart:
    backend: dict[str, Any]
    returncode: int | None
    left: list[str]


@pytest.fixture(scope="module")
def first_start(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FirstStart]:
    """One first start, to the page, then Ctrl+C."""
    with fresh_home() as home:
        log = tmp_path_factory.mktemp("web-smoke") / "web.log"
        web = launch_web(home, log, web_command(COMMIT, TARBALL, "--no-open"))
        try:
            web.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
            backend = web.request("GET", BACKEND)
            web.wait_for_line(RUNNING, FIRST_LAUNCH_S)
        finally:
            if web.process.poll() is None:
                interrupt(web)
            try:
                web.process.wait(timeout=STOPPED_S)
            finally:
                web.stop()
                print(f"the command's log: {log}")
        yield FirstStart(
            backend, web.process.returncode, processes_mentioning(str(home))
        )


def test_the_first_start_gets_the_library_backend_ready_and_ctrl_c_leaves_nothing(
    first_start,
):
    assert first_start.backend["state"] == "ready"
    assert first_start.returncode == 0
    assert first_start.left == []


def typescript_client_url() -> str:
    """The SDK fork's release file the Canvas pin's package.json names: a GitHub release
    download, as the browser command's own tarball is."""
    pins = build.load_pins(build.PINS)
    package = build.read_file_at(
        pins.canvas_fork.repo, pins.canvas_fork.commit, "package.json"
    )
    spec = json.loads(package)
    return {**spec.get("devDependencies", {}), **spec.get("dependencies", {})}[
        build.TYPESCRIPT_CLIENT
    ]


@pytest.mark.skipif(sys.platform != "darwin", reason="the Mac's Python and its TLS")
def test_the_python_uvx_picks_reaches_githubs_release_downloads(tmp_path):
    url = typescript_client_url()
    source = command_for(COMMIT).split()[2]
    with fresh_home() as home:
        done = subprocess.run(
            [
                "uvx",
                "--from",
                source,
                "python",
                "-I",
                "-c",
                DOWNLOAD,
                url,
                str(tmp_path / "client.tgz"),
            ],
            env=user_environment(home),
            capture_output=True,
            text=True,
            timeout=DOWNLOAD_S,
            check=False,
        )
    assert done.returncode == 0, done.stdout + done.stderr
    assert (tmp_path / "client.tgz").stat().st_size > 0
