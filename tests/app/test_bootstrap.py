"""desktop/bootstrap.sh, run as C3's launcher runs the setup command, with a stub git and
uvx (D5 §4.3.1)."""

import importlib.util
import subprocess
from pathlib import Path

from dr_app import texts
from tests.app.conftest import COMMIT

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = (ROOT / "desktop" / "bootstrap.sh").read_text()
REPO = "https://github.com/michaeltheologitis/deep-reasoning"
_spec = importlib.util.spec_from_file_location("build", ROOT / "desktop" / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)
ACCESS_LINE = (
    "✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check that this "
    "computer is online, and that your git credentials can read it. It is private: ask "
    "Michael for read access, then sign git in for https (gh auth login, or an SSH key "
    'and git config --global url."git@github.com:".insteadOf "https://github.com/") and '
    "restart. Nothing was installed."
)


def bootstrap(stubs, repo=REPO, *, path=None, **exits: str):
    env = {
        "PATH": path or f"{stubs.bin}:/usr/bin:/bin",
        "STUB_LOG": str(stubs.log_path),
    }
    return subprocess.run(
        build.setup_command(repo, COMMIT, BOOTSTRAP),
        env=env | exits,
        capture_output=True,
        text=True,
        check=False,
    )


def test_no_git_says_how_to_install_it(stubs, tmp_path):
    (stubs.bin / "git").unlink()
    alone = tmp_path / "only-uvx"
    alone.mkdir()
    (alone / "uvx").symlink_to(stubs.bin / "uvx")
    (alone / "sh").symlink_to("/bin/sh")
    done = bootstrap(stubs, path=str(alone))
    assert (done.returncode, done.stdout) == (10, texts.NO_GIT + "\n")
    assert stubs.calls("uvx") == []


def test_an_unreadable_deep_reasoning_says_so_and_keeps_uvx_status(stubs):
    done = bootstrap(stubs, STUB_UVX_FROM_EXIT="2", STUB_GIT_LS_REMOTE_EXIT="128")
    assert (done.returncode, done.stdout) == (2, ACCESS_LINE + "\n")
    assert stubs.argvs("git")[-1] == ["ls-remote", REPO, "HEAD"]


def test_dr_apps_own_failure_passes_through_without_the_access_line(stubs):
    done = bootstrap(stubs, STUB_UVX_FROM_EXIT="12", STUB_GIT_LS_REMOTE_EXIT="128")
    assert (done.returncode, done.stdout) == (12, "")
    assert stubs.argvs("git") == [["--version"]]


def test_the_arguments_reach_dr_app_unchanged(stubs):
    spaced = "/Volumes/My Drive/deep-reasoning"
    done = bootstrap(stubs, spaced)
    assert done.returncode == 0
    [call] = stubs.calls("uvx")
    assert call["argv"] == [
        "--from",
        f"git+{spaced}@{COMMIT}#subdirectory=packages/dr-app",
        "dr-app",
        "setup",
        "--repo",
        spaced,
        "--commit",
        COMMIT,
    ]
    assert call["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert call["env"]["GIT_SSH_COMMAND"] == "ssh -o BatchMode=yes"
