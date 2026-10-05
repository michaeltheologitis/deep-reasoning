import hashlib
import os
import signal
import subprocess
import sys
import time
import tomllib
from pathlib import Path

import pytest

from dr_app import texts
from dr_app.cli import before_start
from dr_app.layout import SetupError, SetupState
from dr_app.runtime import PUMP_DRAIN_S, deep_reasoner_pin, run_logged
from tests.app.conftest import COMMIT, NEXT_COMMIT, REPO, ROOT

DR_URL = "https://github.com/DeanLight/deep_reasoner_beta"
DR_COMMIT = deep_reasoner_pin(ROOT).commit


def setup(layout, commit=COMMIT):
    before_start(layout, REPO, commit, env=os.environ)


def lines(capsys) -> list[str]:
    return capsys.readouterr().out.splitlines()


def test_a_first_launch_checks_then_installs_the_commits_own_lock(
    layout, stubs, capsys
):
    setup(layout)
    source = str(layout.runtime_dir / f"{COMMIT}.tmp-{os.getpid()}-source")
    building = str(layout.runtime_dir / f"{COMMIT}.tmp-{os.getpid()}")
    assert stubs.argvs("git") == [
        ["--version"],
        ["init", "-q", source],
        ["fetch", "-q", "--depth", "1", REPO, COMMIT],
        ["checkout", "-q", "FETCH_HEAD"],
        ["ls-remote", DR_URL, "HEAD"],
    ]
    venv, sync = stubs.calls("uv")
    assert venv["argv"] == [
        "venv",
        "--relocatable",
        "--managed-python",
        "--python",
        "3.12",
        building,
    ]
    assert sync["argv"] == [
        "sync",
        "--frozen",
        "--no-dev",
        "--no-editable",
        "--all-packages",
        "--project",
        source,
    ]
    assert sync["env"]["UV_PROJECT_ENVIRONMENT"] == building
    assert layout.current_runtime.resolve() == layout.runtime_dir / COMMIT
    assert {p.name for p in layout.runtime_dir.iterdir()} == {COMMIT, "current"}
    for name in ("dr-app", "dr"):
        assert (
            layout.bin_dir / name
        ).readlink() == layout.current_runtime / "bin" / name
    state = SetupState.load(layout.setup_file)
    lock_sha256 = hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest()
    assert (state.dr_home, state.runtime.commit, state.runtime.lock_sha256) == (
        str(layout.root),
        COMMIT,
        lock_sha256,
    )
    said = lines(capsys)
    assert said[:4] == [
        texts.home_local(str(layout.root)),
        texts.checks_ok("2.39.5", "github.com/DeanLight/deep_reasoner_beta"),
        texts.safety("5"),
        texts.installing(COMMIT[:7], DR_COMMIT[:7]),
    ]
    assert "Resolved 173 packages" in said
    assert said[-1].startswith("installed in ")


def test_deep_reasoners_pin_is_read_from_uv_lock_as_pyproject_names_it():
    pin = deep_reasoner_pin(ROOT)
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pin.url == DR_URL
    assert (
        f"deep-reasoner @ git+{pin.url}@{pin.commit}"
        in (pyproject["project"]["dependencies"])
    )


def test_the_runtimes_uv_sync_reads_no_project_setting_that_changes_its_set():
    """uv sync honours a .python-version and [tool.uv]'s default-groups; neither may
    move the runtime off its relocatable Python 3.12 venv or add a group to it."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert not (ROOT / ".python-version").exists()
    assert "default-groups" not in pyproject["tool"]["uv"]


def test_the_runtimes_commands_run_from_where_the_install_leaves_them(layout, stubs):
    setup(layout)
    for name in ("dr-acp", "dr-library", "dr-app", "dr"):
        ran = subprocess.run(
            [layout.current_runtime / "bin" / name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert (ran.returncode, ran.stdout) == (0, f"{name} ran\n"), ran.stderr


def test_a_relaunch_with_nothing_changed_runs_no_uv_and_no_git(layout, stubs, capsys):
    setup(layout)
    before = len(stubs.calls())
    capsys.readouterr()
    setup(layout)
    assert stubs.calls()[before:] == []
    assert lines(capsys) == []


def test_a_new_commit_reinstalls(layout, stubs, capsys):
    setup(layout)
    capsys.readouterr()
    setup(layout, NEXT_COMMIT)
    said = lines(capsys)
    assert texts.safety("5") not in said, "the safety line is for a first install"
    assert said[1] == texts.installing(NEXT_COMMIT[:7], DR_COMMIT[:7])
    assert len(stubs.argvs("uv")) == 4
    assert {p.name for p in layout.runtime_dir.iterdir()} == {NEXT_COMMIT, "current"}
    assert layout.current_runtime.resolve() == layout.runtime_dir / NEXT_COMMIT


def test_a_broken_runtime_python_reinstalls(layout, stubs):
    setup(layout)
    (layout.runtime_dir / COMMIT / "bin" / "python").unlink()
    setup(layout)
    assert [argv[0] for argv in stubs.argvs("uv")] == ["venv", "sync", "venv", "sync"]
    assert (layout.runtime_dir / COMMIT / "bin" / "python").exists()


def test_an_unreadable_deep_reasoner_installs_nothing(layout, stubs, monkeypatch):
    monkeypatch.setenv("STUB_GIT_LS_REMOTE_EXIT", "128")
    with pytest.raises(SetupError) as refused:
        setup(layout)
    assert refused.value.exit_code == 10
    assert refused.value.message == texts.no_access_dr(
        "github.com/DeanLight/deep_reasoner_beta"
    )
    assert stubs.calls("uv") == []
    assert list(layout.runtime_dir.iterdir()) == []


def test_without_uv_nothing_is_installed(layout, stubs, monkeypatch):
    (stubs.bin / "uv").unlink()
    monkeypatch.setenv("PATH", f"{stubs.bin}{os.pathsep}/usr/bin{os.pathsep}/bin")
    if any((Path(d) / "uv").exists() for d in ("/usr/bin", "/bin")):
        pytest.skip("this machine has uv in /usr/bin or /bin")
    with pytest.raises(SetupError) as refused:
        setup(layout)
    assert (refused.value.exit_code, refused.value.message) == (10, texts.NO_UV)


@pytest.mark.parametrize(
    ("failing", "step"),
    [("STUB_GIT_FETCH_EXIT", "git fetch"), ("STUB_UV_SYNC_EXIT", "uv sync")],
)
def test_a_failed_install_keeps_current_and_exits_11(
    layout, stubs, monkeypatch, failing, step
):
    setup(layout)
    monkeypatch.setenv(failing, "2")
    with pytest.raises(SetupError) as failed:
        setup(layout, NEXT_COMMIT)
    assert failed.value.exit_code == 11
    assert failed.value.message == texts.install_failed(NEXT_COMMIT[:7], step, "2")
    assert layout.current_runtime.resolve() == layout.runtime_dir / COMMIT
    assert {p.name for p in layout.runtime_dir.iterdir()} == {COMMIT, "current"}
    assert SetupState.load(layout.setup_file).runtime.commit == COMMIT


def test_an_interrupted_install_is_cleaned_up(layout, stubs):
    (layout.runtime_dir / f"{COMMIT}.tmp-999" / "bin").mkdir(parents=True)
    (layout.runtime_dir / f"{COMMIT}.tmp-999-source").mkdir()
    setup(layout)
    assert {p.name for p in layout.runtime_dir.iterdir()} == {COMMIT, "current"}


@pytest.mark.parametrize("preset", [None, "ssh -i ~/.ssh/work"])
def test_git_never_prompts(layout, stubs, monkeypatch, preset):
    if preset:
        monkeypatch.setenv("GIT_SSH_COMMAND", preset)
    else:
        monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    setup(layout)
    fetching = [c for c in stubs.calls() if c["argv"] != ["--version"]]
    assert [c["argv"][0] for c in fetching] == [
        "init",
        "fetch",
        "checkout",
        "ls-remote",
        "venv",
        "sync",
    ]
    for call in fetching:
        assert call["env"]["GIT_TERMINAL_PROMPT"] == "0"
        assert call["env"]["GIT_SSH_COMMAND"] == (preset or "ssh -o BatchMode=yes")


# What the desktop app ships for (D5 §4.2.4): Linux on x86-64, and macOS on Apple silicon
# (Michael, 2026-10-04) from macOS 14, the oldest the locked arm64 wheels install on.
SHIPPED_PLATFORMS = ("x86_64-unknown-linux-gnu", "aarch64-apple-darwin")
OLDEST_MACOS = "14.0"


@pytest.mark.parametrize("platform", SHIPPED_PLATFORMS)
def test_the_runtime_lock_installs_on_every_platform_the_app_ships_for(
    tmp_path, platform
):
    """A dry run of uv.lock's registry packages for the platform, as the runtime's uv
    sync takes them, wheels only: the app builds nothing on the user's machine, which
    may have no compiler (cryptography's source needs Rust). It reads PyPI's
    metadata."""
    exported = subprocess.run(
        [
            *("uv", "export", "--frozen", "--no-dev", "--all-packages"),
            *("--no-emit-workspace", "--no-hashes", "--no-header", "--no-annotate"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    registry_only = tmp_path / "lock.txt"
    registry_only.write_text(
        "".join(
            line for line in exported.splitlines(keepends=True) if " @ git+" not in line
        )
    )
    dry_run = subprocess.run(
        [
            *(
                "uv",
                "pip",
                "install",
                "--dry-run",
                "--no-deps",
                "--only-binary",
                ":all:",
            ),
            *("--python-platform", platform, "--python-version", "3.12"),
            *("--target", str(tmp_path / "target"), "-r", str(registry_only)),
        ],
        env=os.environ | {"MACOSX_DEPLOYMENT_TARGET": OLDEST_MACOS},
        capture_output=True,
        text=True,
        check=False,
    )
    assert dry_run.returncode == 0, dry_run.stderr


def test_a_background_child_that_keeps_the_output_never_holds_setup():
    logged: list[str] = []
    started = time.monotonic()
    code = run_logged(
        ["sh", "-c", "echo one; sleep 30 & echo $!; echo two >&2; exit 3"],
        env=os.environ,
        log=logged.append,
    )
    took = time.monotonic() - started
    os.kill(int(logged[1]), signal.SIGTERM)
    assert code == 3
    assert [logged[0], logged[2]] == ["one", "two"]
    assert took < PUMP_DRAIN_S + 1.0


def test_nothing_setup_starts_leaves_the_process_group():
    logged: list[str] = []
    probe = "import os; print(os.getpgrp(), os.getsid(0))"
    run_logged([sys.executable, "-c", probe], env=os.environ, log=logged.append)
    assert logged == [f"{os.getpgrp()} {os.getsid(0)}"]
