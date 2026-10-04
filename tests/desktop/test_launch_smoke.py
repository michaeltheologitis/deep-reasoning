"""The launch smoke (D5 §7.6): the built app's first launch, with a fresh HOME, gets the
Library App's backend ready, and the app quits. On a real Mac it is S2 PR 3's
falsifier, "the Library App's backend does not start on macOS"; desktop-release.yml's
macos job runs it on the .app it built. It starts no conversation, so no model is
called.
"""

import pytest

from dr_app import texts
from tests.desktop.app import APP, FIRST_LAUNCH_S, fresh_home, launch

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.skipif(not APP.exists(), reason=f"the app is not installed at {APP}"),
]

BACKEND = "/api/canvas-extensions/installed/dr-library/backend"


def test_the_first_launch_starts_the_library_backend_and_the_app_quits(tmp_path):
    with fresh_home() as home:
        app = launch(home, tmp_path / "app.log")
        try:
            app.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
            after = [line for line in app.lines() if "[setup after-ready] " in line]
            status = app.request("GET", BACKEND)
        finally:
            app.stop()
            print(f"the app's log: {app.log}")
    assert any(line.endswith(texts.app_ready("0.1.0", "installed")) for line in after)
    assert status["state"] == "ready"
    assert app.process.returncode == 0
