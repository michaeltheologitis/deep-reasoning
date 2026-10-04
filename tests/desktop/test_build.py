"""desktop/build.py's checks and what it writes, with every reader of a fork passed in
(D5 §4.2, §7.3). The packaging itself is tested by building it (§7.5, §7.6)."""

import copy
import importlib.util
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("build", ROOT / "desktop" / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

CANVAS_REPO = "https://github.com/michaeltheologitis/OpenHands"
SDK_REPO = "https://github.com/michaeltheologitis/software-agent-sdk"
CANVAS_COMMIT = "c" * 40
SDK_COMMIT = "34c540ce0598b20ddf913d51968dd903c1c13b2e"
CLIENT = f"{SDK_REPO}/releases/download/dr-2/openhands-typescript-client-1.50.1.tgz"
PINS = build.Pins(
    canvas_fork=build.ForkPin(CANVAS_REPO, CANVAS_COMMIT, "dr-1"),
    sdk_fork=build.ForkPin(SDK_REPO, SDK_COMMIT, "dr-2"),
    app=build.AppPin(
        "Deep Reasoning",
        "io.github.michaeltheologitis.deep-reasoning",
        "deep-reasoning",
        "1.0.0-rc.1",
        "M <m@example.invalid>",
        "0.12.23",
    ),
)
# The Canvas fork's config/defaults.json at 7c12afb, the keys D5 reads or writes, wired.
DEFAULTS = {
    "_comment": "Single source of truth for version pins, ports, paths, and defaults.",
    "versions": {"agentServer": "1.50.1", "agentCanvas": "1.24.0"},
    "sources": {"agentServerGitRepo": SDK_REPO, "agentServerGitRef": SDK_COMMIT},
    "ports": {"agentServer": 18000, "proxy": 8000},
    "paths": {"stateSubdir": "agent-canvas", "stateDir": None},
    "setup": {"command": None, "phases": ["before-start", "after-ready"]},
    "telemetry": {
        "posthogApiKey": "phc_upstreams_key",
        "posthogHost": "https://us.i.posthog.com",
    },
}
GIT = ("git", "-c", "user.name=t", "-c", "user.email=t@example.invalid")


def ours_acp_lock() -> str:
    """The SDK fork's uv.lock as far as check 4 reads it: our agent-client-protocol."""
    version = build.locked_version(
        (ROOT / "uv.lock").read_text(), "agent-client-protocol"
    )
    return f'version = 1\n\n[[package]]\nname = "agent-client-protocol"\nversion = "{version}"\n'


@pytest.fixture
def canvas(tmp_path: Path) -> Path:
    checkout = tmp_path / "canvas"
    (checkout / "config").mkdir(parents=True)
    (checkout / "config" / "defaults.json").write_text(json.dumps(DEFAULTS))
    package = {"dependencies": {"@openhands/typescript-client": CLIENT}}
    (checkout / "package.json").write_text(json.dumps(package))
    return checkout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A deep-reasoning checkout: its lock files, committed and pushed to origin."""
    origin, checkout = tmp_path / "origin.git", tmp_path / "deep-reasoning"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    for name in (
        "desktop/pins.toml",
        "pyproject.toml",
        "uv.lock",
        "packages/dr-app/pyproject.toml",
        str(build.RUNTIME_LOCK),
    ):
        (checkout / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, checkout / name)
    for argv in (
        ["init", "-q", "-b", "main"],
        ["add", "-A"],
        ["commit", "-q", "-m", "the build's inputs"],
        ["remote", "add", "origin", str(origin)],
        ["push", "-q", "origin", "main"],
    ):
        subprocess.run([*GIT, *argv], cwd=checkout, check=True)
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=checkout, check=True)
    return checkout


def readers(**changed):
    tags = {
        "refs/tags/dr-1": CANVAS_COMMIT,
        "refs/tags/dr-2": "a" * 40,  # the annotated tag's own object
        "refs/tags/dr-2^{}": SDK_COMMIT,
    } | changed.pop("tags", {})
    on_branch = changed.pop("on_branch", {CANVAS_COMMIT, SDK_COMMIT})
    sdk_lock = changed.pop("sdk_lock", ours_acp_lock())
    return {
        "ls_remote": lambda url, refs: {r: tags[r] for r in refs if r in tags},
        "read_sdk_file": lambda path: {"uv.lock": sdk_lock}[path],
        "is_on_branch": lambda url, branch, commit: (
            branch == "deep-reasoning" and commit in on_branch
        ),
    }


def problems(canvas, repo, pins=PINS, **changed):
    return build.check_pins(pins, canvas=canvas, repo=repo, **readers(**changed))


def rewire(canvas: Path, **sources) -> None:
    path = canvas / "config" / "defaults.json"
    defaults = json.loads(path.read_text())
    defaults["sources"] |= sources
    path.write_text(json.dumps(defaults))


def test_pins_that_belong_together_pass_every_check(canvas, repo):
    assert problems(canvas, repo) == []


def test_pins_with_a_short_commit_are_refused(tmp_path):
    pins = (ROOT / "desktop" / "pins.toml").read_text()
    short = tmp_path / "pins.toml"
    placeholder = tomllib.loads(pins)["canvas_fork"]["commit"]
    short.write_text(
        pins.replace(placeholder, CANVAS_COMMIT).replace(SDK_COMMIT, SDK_COMMIT[:7])
    )
    with pytest.raises(
        ValueError, match="sdk_fork.commit must be a full 40-hex commit"
    ):
        build.load_pins(short)


def test_a_canvas_fork_wired_to_another_sdk_commit_is_refused(canvas, repo):
    rewire(canvas, agentServerGitRef="cef3b24" + "0" * 33)
    assert problems(canvas, repo) == [
        (
            "✗ Canvas fork dr-1 runs the agent-server at cef3b24 (its wiring commit), "
            "but desktop/pins.toml pins the SDK fork at dr-2 (34c540c). Bump both, or "
            "neither."
        )
    ]


def test_a_tag_that_moved_is_refused(canvas, repo):
    found = problems(canvas, repo, tags={"refs/tags/dr-2^{}": "b" * 40})
    assert found == [build.tag_moved("SDK fork", "dr-2", "b" * 40, SDK_COMMIT)]


def test_a_commit_off_the_forks_deep_reasoning_branch_is_refused(canvas, repo):
    assert problems(canvas, repo, on_branch={CANVAS_COMMIT}) == [
        build.off_branch("SDK fork", SDK_COMMIT)
    ]


def test_a_typescript_client_from_another_tag_is_refused(canvas, repo):
    elsewhere = CLIENT.replace("/dr-2/", "/dr-1/")
    (canvas / "package.json").write_text(
        json.dumps({"dependencies": {"@openhands/typescript-client": elsewhere}})
    )
    assert problems(canvas, repo) == [
        build.client_from_elsewhere("dr-1", elsewhere, "dr-2")
    ]


def test_a_different_acp_python_is_refused(canvas, repo):
    theirs = ours_acp_lock().replace('version = "0.', 'version = "9.')
    [problem] = problems(canvas, repo, sdk_lock=theirs)
    assert problem.startswith(
        "✗ The SDK fork's uv.lock at dr-2 locks agent-client-protocol 9."
    )


def test_a_fork_that_carries_our_values_is_refused(canvas, repo):
    path = canvas / "config" / "defaults.json"
    defaults = json.loads(path.read_text())
    defaults["paths"]["stateDir"] = "~/.elsewhere/agent-canvas"
    path.write_text(json.dumps(defaults))
    assert problems(canvas, repo) == [
        build.fork_sets_ours("dr-1", "paths.stateDir", "~/.elsewhere/agent-canvas")
    ]


def test_a_dirty_or_unpushed_checkout_is_refused(canvas, repo):
    (repo / "desktop" / "pins.toml").write_text("# changed\n")
    assert problems(canvas, repo) == [build.checkout_dirty(1)]
    subprocess.run([*GIT, "commit", "-q", "-am", "local only"], cwd=repo, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert problems(canvas, repo) == [build.head_unpushed(head)]


def test_a_runtime_lock_that_is_not_uv_lock_is_refused(canvas, repo):
    lock = repo / build.RUNTIME_LOCK
    lock.write_text(lock.read_text().replace("httpx==", "httpx>="))
    subprocess.run([*GIT, "commit", "-q", "-am", "stale"], cwd=repo, check=True)
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=repo, check=True)
    assert problems(canvas, repo) == [build.lock_stale()]


def test_defaults_gain_only_d5s_four_keys():
    before = copy.deepcopy(DEFAULTS)
    command = ["sh", "-c", "script", "dr-app-bootstrap", "spec", "repo", "c" * 40]
    patched = build.patch_defaults(DEFAULTS, state_dir=build.STATE_DIR, command=command)
    assert DEFAULTS == before
    expected = copy.deepcopy(DEFAULTS)
    expected["paths"]["stateDir"] = "~/.deep-reasoning/canvas/agent-canvas"
    expected["setup"] = {"command": command, "phases": ["before-start", "after-ready"]}
    expected["telemetry"]["posthogApiKey"] = ""
    assert patched == expected


def test_telemetry_is_off_in_the_built_defaults():
    patched = build.patch_defaults(DEFAULTS, state_dir=build.STATE_DIR, command=[])
    assert patched["telemetry"] == {
        "posthogApiKey": "",
        "posthogHost": "https://us.i.posthog.com",
    }


def test_the_setup_command_embeds_the_bootstrap_and_the_commit():
    bootstrap = (ROOT / "desktop" / "bootstrap.sh").read_text()
    command = build.setup_command(build.DEEP_REASONING, SDK_COMMIT, bootstrap)
    assert command == [
        "sh",
        "-c",
        bootstrap,
        "dr-app-bootstrap",
        (
            f"git+https://github.com/michaeltheologitis/deep-reasoning@{SDK_COMMIT}"
            "#subdirectory=packages/dr-app"
        ),
        "https://github.com/michaeltheologitis/deep-reasoning",
        SDK_COMMIT,
    ]


def test_the_committed_sdk_pin_is_34c540c_tagged_dr_2():
    raw = tomllib.loads((ROOT / "desktop" / "pins.toml").read_text())
    assert raw["sdk_fork"] == {"repo": SDK_REPO, "commit": SDK_COMMIT, "tag": "dr-2"}
    assert raw["app"]["uv_version"] == "0.12.23"


def test_the_committed_pins_load():
    pins = build.load_pins(ROOT / "desktop" / "pins.toml")
    assert pins.canvas_fork == build.ForkPin(
        CANVAS_REPO, "fc87687abb304a839c60171ac8445f306eacd907", "dr-1"
    )
    assert pins.sdk_fork == build.ForkPin(SDK_REPO, SDK_COMMIT, "dr-2")
    assert "@" in pins.app.maintainer
