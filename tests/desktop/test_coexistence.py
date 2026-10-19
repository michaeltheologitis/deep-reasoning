"""The app and the browser command on one computer (TASK-48 §7.5): port 18000 is the lock,
so whichever starts second is refused before it writes anything under ~/.deep-reasoning.

It needs the app installed from the .deb and the tarball, both from one build, so both
carry the same setup command: uv run pytest -m desktop tests/desktop/test_coexistence.py,
under xvfb-run.
"""

import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from desktop import build
from tests.desktop.app import (
    AGENT_SERVER_PORT,
    APP,
    FIRST_LAUNCH_S,
    STARTUP_FAILED,
    LaunchedApp,
    fresh_home,
    interrupt,
    launch,
    launch_web,
    snapshot,
    web_command,
    web_text,
)

PINS = build.load_pins(build.PINS)
TARBALL = build.REPO / "dist" / build.web_tarball_name(PINS.app.version)

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.skipif(not APP.exists(), reason=f"the app is not installed at {APP}"),
    pytest.mark.skipif(not TARBALL.exists(), reason=f"no {TARBALL}: build.py web"),
]

HEAD = build.git("rev-parse", "HEAD", cwd=build.REPO).strip()
COMMAND = web_command(HEAD, TARBALL, "--no-open")
RUNNING = "Deep Reasoning is running at "
REFUSED_S = 10.0
APP_REFUSED_S = 120.0
STOP_S = 30.0
# Every load of Canvas reads the settings. A window's first load against a HOME no page
# has opened then saves them once (Canvas's enabled-skills migration): the app's own
# write, a few seconds after setup is done.
WINDOW_READ = '"GET /api/settings HTTP/1.1" 200'
QUIET_S = 5.0
SETTLE_S = 60.0


def settled(app: LaunchedApp) -> dict[str, str]:
    """snapshot(app.data) once the window has loaded and nothing changed for QUIET_S."""
    app.wait_for_line(WINDOW_READ, FIRST_LAUNCH_S)
    deadline = time.monotonic() + SETTLE_S
    last, since = snapshot(app.data), time.monotonic()
    while time.monotonic() - since < QUIET_S:
        assert time.monotonic() < deadline, f"{app.data} kept changing"
        time.sleep(0.5)
        now = snapshot(app.data)
        if now != last:
            last, since = now, time.monotonic()
    return last


@pytest.fixture(scope="module")
def home() -> Iterator[Path]:
    """One HOME for both: the browser's first start installs, the app's start reuses."""
    with fresh_home() as fresh:
        yield fresh


def test_the_app_will_not_start_beside_the_browser_and_writes_nothing(home, tmp_path):
    web = launch_web(home, tmp_path / "web.log", COMMAND)
    try:
        web.wait_for_line(RUNNING, FIRST_LAUNCH_S)
        before = snapshot(web.data)
        app = launch(home, tmp_path / "app.log")
        try:
            app.wait_for_line(STARTUP_FAILED, APP_REFUSED_S)
            assert [line for line in app.lines() if f"port {AGENT_SERVER_PORT}" in line]
            assert snapshot(web.data) == before
        finally:
            app.stop()
    finally:
        interrupt(web)
        assert web.process.wait(timeout=STOP_S) == 0


def test_the_browser_will_not_start_beside_the_app_and_writes_nothing(home, tmp_path):
    app = launch(home, tmp_path / "app.log")
    try:
        app.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
        assert not [line for line in app.lines() if "installing deep-reasoning" in line]
        before = settled(app)
        web = launch_web(home, tmp_path / "web.log", COMMAND)
        code = web.process.wait(timeout=REFUSED_S)
        refused = web_text("already_running", AGENT_SERVER_PORT)
        assert (code, web.lines()[-1]) == (20, refused)
        assert snapshot(app.data) == before
    finally:
        app.stop()
