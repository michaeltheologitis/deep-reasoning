"""The launch harness's failures say why (D5 §7.5, §7.6): the app's log comes with them,
and a launch the app itself reports failed ends the wait at once, since the packaged
app stays open on its failure screen."""

import subprocess
import sys
import time

import pytest

from tests.desktop.app import LOG_TAIL_LINES, LaunchedApp

STARTUP_FAILED = (
    "[desktop] Startup failed: SetupCommandError: setup before-start exited 11"
)


def running(tmp_path, lines: list[str], *, exits: bool) -> LaunchedApp:
    log = tmp_path / "app.log"
    log.write_text("".join(f"\x1b[36m{line}\x1b[0m\n" for line in lines))
    code = "pass" if exits else "import time; time.sleep(30)"
    process = subprocess.Popen([sys.executable, "-c", code])
    if exits:
        process.wait()
    return LaunchedApp(process, tmp_path, log, 0)


@pytest.mark.parametrize(
    ("last", "exits", "why"),
    [
        ("[setup before-start] installing deep-reasoning", True, "the app exited 0"),
        (STARTUP_FAILED, False, "the app reported its launch failed"),
        ("[setup before-start] installing deep-reasoning", False, "in 2 s"),
    ],
    ids=["exited", "reported-failure", "timed-out"],
)
def test_a_failed_wait_says_why_with_the_logs_last_lines(tmp_path, last, exits, why):
    lines = [f"line {n}" for n in range(LOG_TAIL_LINES + 5)] + [last]
    app = running(tmp_path, lines, exits=exits)
    started = time.monotonic()
    try:
        with pytest.raises(AssertionError) as failed:
            app.wait_for_line("[setup after-ready] Done in", 2)
    finally:
        app.process.kill()
        app.process.wait()
    message = str(failed.value)
    assert why in message
    assert message.endswith("\n".join(lines[-LOG_TAIL_LINES:]))
    assert "line 4\n" not in message
    assert time.monotonic() - started < 5
