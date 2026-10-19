"""The launch harness's failures say why (D5 §7.5, §7.6): the app's log comes with them,
and a launch the app itself reports failed ends the wait at once, since the packaged
app stays open on its failure screen."""

import struct
import subprocess
import sys
import time

import pytest

from tests.desktop.app import (
    LOG_TAIL_LINES,
    LaunchedApp,
    age_uv_index_answers,
    fresh_home,
    user_environment,
)

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


def test_git_under_the_fresh_home_stores_no_credentials_whatever_the_systems_helper(
    tmp_path,
):
    """The runner's system git config names a credential helper (osxkeychain on the
    macOS runner); under a HOME with no keychain its store waits on a dialog no one
    answers, so a fetch that authenticated never ends (run 37230513867)."""
    stored = tmp_path / "stored"
    system = tmp_path / "gitconfig"
    system.write_text(f'[credential]\n\thelper = "!f() {{ cat > {stored}; }}; f"\n')
    credential = "protocol=https\nhost=github.com\nusername=x\npassword=token\n\n"
    with fresh_home() as home:
        env = user_environment(home) | {"GIT_CONFIG_SYSTEM": str(system)}
        subprocess.run(
            ["git", "credential", "approve"],
            input=credential,
            env=env,
            text=True,
            check=True,
            timeout=30,
        )
    assert not stored.exists()


def answer(path, fetched: int, *, padding: int = 600) -> None:
    """A cached index answer as uv lays one out: its fetch time a u64 near the end."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x07" * padding + struct.pack("<Q", fetched) + b"\0" * 16)


def fetched(path) -> int:
    return struct.unpack_from("<Q", path.read_bytes(), 600)[0]


def test_ageing_uvs_index_answers_moves_each_fetch_time_back_and_says_when_it_cannot(
    tmp_path,
):
    """TASK-66 M8: uv's answers expire as if fetched an hour ago, without the wait."""
    now = int(time.time())
    answers = [tmp_path / "simple-v17" / "pypi" / f"{n}.rkyv" for n in ("a", "b")]
    for path in answers:
        answer(path, now - 30)
    answer(tmp_path / "simple-v17" / "pypi" / "old.rkyv", now - 7200)
    with pytest.raises(AssertionError, match="old.rkyv"):
        age_uv_index_answers(tmp_path, now - 60, 3600)
    (tmp_path / "simple-v17" / "pypi" / "old.rkyv").unlink()
    for path in answers:
        answer(path, now - 30)
    assert age_uv_index_answers(tmp_path, now - 60, 3600) == 2
    assert [fetched(path) for path in answers] == [now - 30 - 3600] * 2
    with pytest.raises(AssertionError, match="no index answers"):
        age_uv_index_answers(tmp_path / "empty", now - 60, 3600)
