"""The launch smoke (D5 §7.6): the built app's first launch, with a fresh HOME, gets the
Library App's backend ready, and the app quits. On a real Mac it is S2 PR 3's
falsifier, "the Library App's backend does not start on macOS"; desktop-release.yml
launches the universal .app it built on an Apple silicon runner and on an Intel one,
so each half of it runs once. It starts no conversation, so no model is called.
"""

import platform
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest

from dr_app import texts
from tests.desktop.app import APP, FIRST_LAUNCH_S, fresh_home, launch

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.skipif(not APP.exists(), reason=f"the app is not installed at {APP}"),
]

BACKEND = "/api/canvas-extensions/installed/dr-library/backend"
BUNDLED_UV = "[desktop] Injected bundled uv from "
# The universal app's per-architecture runtime directories, by this Mac's machine.
MAC_RUNTIMES = {"arm64": "bin-arm64", "x86_64": "bin-x64"}


@dataclass
class FirstLaunch:
    lines: list[str]
    backend: dict[str, Any]
    returncode: int | None


@pytest.fixture(scope="module")
def first_launch(tmp_path_factory) -> Iterator[FirstLaunch]:
    """One first launch, to the end of setup's after-ready phase, then a quit."""
    with fresh_home() as home:
        app = launch(home, tmp_path_factory.mktemp("launch") / "app.log")
        try:
            app.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
            backend = app.request("GET", BACKEND)
        finally:
            app.stop()
            print(f"the app's log: {app.log}")
        yield FirstLaunch(app.lines(), backend, app.process.returncode)


def test_the_first_launch_starts_the_library_backend_and_the_app_quits(first_launch):
    after = [line for line in first_launch.lines if "[setup after-ready] " in line]
    assert any(line.endswith(texts.app_ready("0.1.0", "installed")) for line in after)
    assert first_launch.backend["state"] == "ready"
    assert first_launch.returncode == 0


@pytest.mark.skipif(sys.platform != "darwin", reason="a universal app is macOS's")
def test_the_universal_app_runs_the_runtime_of_this_macs_architecture(first_launch):
    [bundled] = [line for line in first_launch.lines if line.startswith(BUNDLED_UV)]
    assert bundled.endswith(f"/{MAC_RUNTIMES[platform.machine()]}"), bundled
