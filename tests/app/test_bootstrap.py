"""desktop/bootstrap.sh, run as C3's launcher runs the setup command, with a stub git and
uvx (D5 §4.3.1)."""

import subprocess

from desktop import build
from dr_app import texts
from tests.app.conftest import COMMIT

BOOTSTRAP = build.BOOTSTRAP.read_text()
REPO = build.DEEP_REASONING
# deep-reasoning is public, so a fetch that fails means the network.
UNREACHABLE_LINE = (
    "✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check that this "
    "computer is online, then restart. Nothing was installed."
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


def test_an_unreachable_deep_reasoning_says_so_and_keeps_uvx_status(stubs):
    done = bootstrap(stubs, STUB_UVX_FROM_EXIT="2", STUB_GIT_LS_REMOTE_EXIT="128")
    assert (done.returncode, done.stdout) == (2, UNREACHABLE_LINE + "\n")
    assert stubs.argvs("git")[-1] == ["ls-remote", REPO, "HEAD"]


def test_dr_apps_own_failure_passes_through_without_the_fetch_line(stubs):
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
