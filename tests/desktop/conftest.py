"""The desktop modules' shared fixture: Playwright on the launched app's own Chromium.
Each module launches its own app (fixture app), which this attaches to."""

import time
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Error, sync_playwright

from tests.desktop.app import FIRST_LAUNCH_S, LaunchedApp


@pytest.fixture(scope="module")
def browser(app: LaunchedApp) -> Iterator[Browser]:
    """Playwright attached to the app's own Chromium over its DevTools port."""
    with sync_playwright() as playwright:
        deadline = time.monotonic() + FIRST_LAUNCH_S
        while True:
            try:
                cdp = playwright.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{app.debug_port}"
                )
                break
            except Error:
                assert app.process.poll() is None, "the app exited before its window"
                assert time.monotonic() < deadline, "no DevTools port"
                time.sleep(1.0)
        yield cdp
