"""dr-app as the launcher and the user run it: a process with HOME a fresh folder."""

import fcntl
import os
import platform
import subprocess
import time
from pathlib import Path

import pytest

import dr_app.cli
from dr_app import texts
from dr_app.layout import SOCKET_PATH_MAX, SetupState, deepest_socket
from tests.app.conftest import COMMIT, DR_APP, REPO

SETUP = ["setup", "--repo", REPO, "--commit", COMMIT]


def dr_app_env(layout, **extra: str) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("AGENT_SERVER_URL", "SESSION_API_KEY", "OH_CANVAS_SETUP_PHASE")
    }
    return env | {"HOME": str(layout.root.parent)} | extra


def dr_app_run(layout, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [DR_APP, *args],
        env=dr_app_env(layout, **extra),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_two_setups_never_run_at_once(layout, stubs):
    layout.root.mkdir(parents=True)
    with layout.lock_file.open("a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        waiting = subprocess.Popen(
            [DR_APP, *SETUP],
            env=dr_app_env(layout),
            stdout=subprocess.PIPE,
            text=True,
        )
        time.sleep(1.0)
        assert waiting.poll() is None
        assert stubs.calls() == []
    out, _ = waiting.communicate(timeout=120)
    assert waiting.returncode == 0, out
    assert stubs.calls("uv")


def test_a_failed_check_exits_with_its_code_and_its_sentence(layout, stubs):
    done = dr_app_run(layout, *SETUP, STUB_GIT_LS_REMOTE_EXIT="128")
    assert done.returncode == 10
    assert done.stdout.splitlines()[-1] == texts.no_access_dr(
        "github.com/DeanLight/deep_reasoner_beta"
    )


def test_export_runs_the_runtimes_dr_library_with_the_home(layout, tmp_path, stubs):
    nothing = dr_app_run(layout, "export", str(tmp_path / "out"))
    assert (nothing.returncode, nothing.stdout) == (13, texts.NOTHING_INSTALLED + "\n")
    assert dr_app_run(layout, *SETUP).returncode == 0
    argv_file = tmp_path / "argv"
    (layout.current_runtime / "bin" / "dr-library").write_text(
        f'#!/bin/sh\necho "$@" > {argv_file}\necho "wrote $2/main.yaml"\nexit 3\n'
    )
    done = dr_app_run(
        layout, "export", str(tmp_path / "out"), "--namespace", "advising"
    )
    assert done.returncode == 3
    assert done.stdout == f"wrote {tmp_path / 'out'}/main.yaml\n"
    assert argv_file.read_text().split() == [
        "export",
        str(tmp_path / "out"),
        "--home",
        str(layout.root),
        "--namespace",
        "advising",
    ]


def test_home_records_a_local_folder_and_refuses_a_network_one(
    layout, tmp_path, monkeypatch, capsys
):
    chosen = layout.root.parents[1] / "data"
    done = dr_app_run(layout, "home", str(chosen))
    assert done.returncode == 0, done.stdout
    assert done.stdout == texts.home_set(str(chosen), str(layout.root)) + "\n"
    assert SetupState.load(layout.setup_file).dr_home == str(chosen)
    shown = dr_app_run(layout, "home")
    assert shown.stdout.startswith(str(chosen))
    relative = dr_app_run(layout, "home", "data")
    assert relative.returncode == 13
    assert (
        relative.stdout == texts.home_refused("data", "is not an absolute path") + "\n"
    )

    monkeypatch.setenv("HOME", str(layout.root.parent))
    monkeypatch.setattr(dr_app.cli.platform, "system", lambda: "Linux")
    monkeypatch.setattr(dr_app.cli, "filesystem_type", lambda path: "nfs4")
    mounted = layout.root.parents[1] / "mounted"
    assert dr_app.cli.main(["home", str(mounted)]) == 13
    assert capsys.readouterr().out == (
        texts.home_refused(str(mounted), "is on a network filesystem (nfs4)") + "\n"
    )
    assert SetupState.load(layout.setup_file).dr_home == str(chosen)


def test_home_refuses_a_folder_too_long_for_a_claude_runs_socket(layout, tmp_path):
    deep = tmp_path / ("d" * 60)
    done = dr_app_run(layout, "home", str(deep))
    assert done.returncode == 13
    assert done.stdout == (
        texts.home_too_long(
            str(deep),
            str(deepest_socket(deep)),
            str(SOCKET_PATH_MAX[platform.system()]),
        )
        + "\n"
    )
    assert not deep.exists()
    assert SetupState.load(layout.setup_file).dr_home is None


def test_the_bin_links_lead_to_the_runtime(layout, stubs):
    assert dr_app_run(layout, *SETUP).returncode == 0
    for name in ("dr-app", "dr"):
        assert Path(layout.bin_dir / name).resolve().parent == (
            layout.runtime_dir / COMMIT / "bin"
        )


STATES = [
    ('{"v": 2}', lambda path: texts.state_from_a_newer_app(path, "2")),
    ('{"x": 1}', lambda path: texts.state_unusable(path, "it has no version")),
    ("{", lambda path: texts.state_unusable(path, "it is not JSON")),
]


@pytest.mark.parametrize("command", [SETUP, ["home"]])
@pytest.mark.parametrize(("content", "sentence"), STATES)
def test_a_setup_state_it_cannot_use_is_explained_and_exits_14(
    layout, stubs, command, content, sentence
):
    """A newer app's setup.json, or one no app wrote, met by this one: a sentence in the
    bootstrap's trusted 10-19 band, not a traceback, and nothing run."""
    layout.root.mkdir(parents=True, exist_ok=True)
    layout.setup_file.write_text(content)
    done = dr_app_run(layout, *command, OH_CANVAS_SETUP_PHASE="before-start")
    expected = sentence(str(layout.setup_file)) + "\n"
    assert (done.returncode, done.stdout) == (14, expected)
    assert "Traceback" not in done.stderr
    assert stubs.calls() == []
