"""desktop/build.py's checks and what it writes, with every reader of a fork passed in
(D5 §4.2, §7.3). The packaging itself is tested by building it (§7.5, §7.6)."""

import copy
import dataclasses
import json
import plistlib
import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

from desktop import build
from dr_app.profile import PROFILE_NAME
from tests.tarballs import write_tarball

ROOT = Path(__file__).resolve().parents[2]

CANVAS_REPO = "https://github.com/michaeltheologitis/OpenHands"
SDK_REPO = "https://github.com/michaeltheologitis/software-agent-sdk"
CANVAS_COMMIT = "c" * 40
SDK_COMMIT = "34c540ce0598b20ddf913d51968dd903c1c13b2e"
CLIENT = f"{SDK_REPO}/releases/download/dr-2/openhands-typescript-client-1.50.1.tgz"
CUTOFF = "2026-10-04T00:00:00Z"
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
        CUTOFF,
    ),
)
# The Canvas fork's config/defaults.json at 7c12afb, the keys D5 reads or writes, wired,
# plus the null settings a fork must declare for this build: the agent lock, the app's
# title and the PyPI cutoff.
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
    "agent": {"lockedProfile": None},
    "branding": {"appTitle": None},
    "uv": {"excludeNewer": None},
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
    """A deep-reasoning checkout of its pins and uv.lock, committed and pushed."""
    origin, checkout = tmp_path / "origin.git", tmp_path / "deep-reasoning"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    for name in ("desktop/pins.toml", "uv.lock"):
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


@pytest.mark.parametrize(
    "value",
    [
        "2026-10-04",
        "2026-10-04T00:00:00+02:00",
        "1 week",
        "2026-02-30T00:00:00Z",
        "",
        "20261004",
    ],
)
def test_a_cutoff_that_is_not_a_utc_time_is_refused(tmp_path, value):
    """uv reads a date in the user's own time zone and a span relative to now (TASK-66
    K2); 30 February is no instant."""
    pins = (ROOT / "desktop" / "pins.toml").read_text()
    path = tmp_path / "pins.toml"
    path.write_text(pins.replace(f'"{CUTOFF}"', json.dumps(value)))
    with pytest.raises(ValueError) as refused:
        build.load_pins(path)
    assert str(refused.value) == (
        f"{path}: app.uv_exclude_newer must be a UTC time such as "
        f"2026-10-04T00:00:00Z, not {value!r}"
    )


def test_pins_with_a_short_commit_are_refused(tmp_path):
    pins = (ROOT / "desktop" / "pins.toml").read_text()
    short = tmp_path / "pins.toml"
    committed = tomllib.loads(pins)
    placeholder = committed["canvas_fork"]["commit"]
    sdk = committed["sdk_fork"]["commit"]
    short.write_text(pins.replace(placeholder, CANVAS_COMMIT).replace(sdk, sdk[:7]))
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


def change_defaults(canvas: Path, change) -> None:
    path = canvas / "config" / "defaults.json"
    defaults = json.loads(path.read_text())
    change(defaults)
    path.write_text(json.dumps(defaults))


@pytest.mark.parametrize(
    ("block", "key", "value"),
    [
        ("paths", "stateDir", "~/.elsewhere/agent-canvas"),
        ("setup", "command", ["sh", "-c", "true"]),
        ("agent", "lockedProfile", "someone_elses_agent"),
        ("branding", "appTitle", "Someone Else's Canvas"),
        ("uv", "excludeNewer", "2026-01-01T00:00:00Z"),
    ],
)
def test_a_fork_that_carries_our_values_is_refused(canvas, repo, block, key, value):
    change_defaults(canvas, lambda defaults: defaults[block].update({key: value}))
    assert problems(canvas, repo) == [
        build.fork_sets_ours("dr-1", f"{block}.{key}", value)
    ]


@pytest.mark.parametrize(
    "key", ["agent.lockedProfile", "branding.appTitle", "uv.excludeNewer"]
)
def test_a_canvas_fork_that_lacks_a_setting_the_build_writes_is_refused(
    canvas, repo, key
):
    """As Canvas dr-3 lacks them: the whole block, which it would ignore if written."""
    block = key.split(".")[0]
    change_defaults(canvas, lambda defaults: defaults.pop(block))
    assert problems(canvas, repo) == [
        (
            f"✗ Canvas fork dr-1's config/defaults.json has no {key}, so this build "
            "cannot set it: pin dr-4 or later."
        )
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


def test_defaults_gain_only_the_keys_the_build_writes():
    before = copy.deepcopy(DEFAULTS)
    command = ["sh", "-c", "script", "dr-app-bootstrap", "spec", "repo", "c" * 40]
    patched = build.patch_defaults(
        DEFAULTS,
        state_dir=build.STATE_DIR,
        command=command,
        app_title="A Product",
        exclude_newer="2026-01-02T03:04:05Z",
    )
    assert DEFAULTS == before
    written = {
        "paths.stateDir": "~/.deep-reasoning/canvas/agent-canvas",
        "setup.command": command,
        "setup.phases": ["before-start", "after-ready"],
        "telemetry.posthogApiKey": "",
        "agent.lockedProfile": "deep_reasoner",
        "branding.appTitle": "A Product",
        "uv.excludeNewer": "2026-01-02T03:04:05Z",
    }
    assert set(written) == {
        *build.FORK_NULL_KEYS,
        "setup.phases",
        "telemetry.posthogApiKey",
    }
    expected = copy.deepcopy(DEFAULTS)
    for key, value in written.items():
        block, name = key.split(".")
        expected.setdefault(block, {})[name] = value
    assert patched == expected


def written_defaults(pins, *, canvas, repo, work, monkeypatch) -> dict:
    """The defaults.json prepare() writes into the Canvas checkout, which the desktop
    packages and the browser tarball both carry: its checkout and checks stand on
    canvas, and it stops at its first npm."""

    class Packaging(Exception):
        pass

    def npm(argv, **_):
        raise Packaging(argv)

    monkeypatch.setattr(build, "check_checkouts", lambda *_, **__: (canvas, []))
    monkeypatch.setattr(build, "run", npm)
    with pytest.raises(Packaging):
        build.prepare(pins, repo=repo, work=work)
    return json.loads((canvas / "config" / "defaults.json").read_text())


def test_the_build_writes_the_product_name_as_the_title_and_the_pinned_cutoff(
    canvas, repo, tmp_path, monkeypatch
):
    app = dataclasses.replace(
        PINS.app, product_name="A Product", uv_exclude_newer="2026-01-02T03:04:05Z"
    )
    written = written_defaults(
        dataclasses.replace(PINS, app=app),
        canvas=canvas,
        repo=repo,
        work=tmp_path,
        monkeypatch=monkeypatch,
    )
    assert written["branding"]["appTitle"] == "A Product"
    assert written["uv"]["excludeNewer"] == "2026-01-02T03:04:05Z"


def test_the_locked_profile_is_the_one_setup_creates():
    assert build.LOCKED_PROFILE == PROFILE_NAME


def test_telemetry_is_off_in_the_built_defaults():
    patched = build.patch_defaults(
        DEFAULTS,
        state_dir=build.STATE_DIR,
        command=[],
        app_title="Deep Reasoning",
        exclude_newer=CUTOFF,
    )
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


DR_3 = "b82dffbaf0e3a58e4248878f01fe0a01ed011876"


def test_the_committed_sdk_pin_is_b82dffb_tagged_dr_3():
    raw = tomllib.loads((ROOT / "desktop" / "pins.toml").read_text())
    assert raw["sdk_fork"] == {"repo": SDK_REPO, "commit": DR_3, "tag": "dr-3"}
    assert raw["app"]["uv_version"] == "0.12.23"


def test_the_committed_pins_load():
    pins = build.load_pins(ROOT / "desktop" / "pins.toml")
    assert pins.canvas_fork == build.ForkPin(
        CANVAS_REPO, "138d41fd3b540fe00fe88572db6e3968e19a820b", "dr-4"
    )
    assert pins.sdk_fork == build.ForkPin(SDK_REPO, DR_3, "dr-3")
    assert "@" in pins.app.maintainer
    assert pins.app.uv_exclude_newer == "2026-10-04T00:00:00Z"


@pytest.mark.skipif(
    shutil.which("dpkg-deb") is None, reason="lists a .deb with dpkg-deb"
)
def test_a_debs_payload_paths_keep_their_spaces(tmp_path):
    package = tmp_path / "package"
    (package / "DEBIAN").mkdir(parents=True)
    (package / "DEBIAN" / "control").write_text(
        "Package: t\nVersion: 1\nArchitecture: all\nMaintainer: t <t@example.invalid>\n"
        "Description: t\n"
    )
    (package / "opt" / "Deep Reasoning").mkdir(parents=True)
    (package / "opt" / "Deep Reasoning" / "deep-reasoning").write_text("")
    subprocess.run(
        ["dpkg-deb", "--build", str(package), str(tmp_path / "t.deb")],
        check=True,
        capture_output=True,
    )
    paths = build.payload_paths(tmp_path / "t.deb", tmp_path)
    assert "./opt/Deep Reasoning/deep-reasoning" in paths


ARM64_DMG = "deep-reasoning-1.0.0-rc.1-arm64.dmg"


def built_mac_app(
    canvas: Path, dmg: str = ARM64_DMG, plist: dict | None = None
) -> Path:
    """dist-electron as electron-builder leaves it for the mac target: the .dmg, and
    the .app it was made from, with the binaries the arm64 check reads and the
    Info.plist the minimum-macOS check reads."""
    output = canvas / "dist-electron"
    app = output / "mac-arm64" / "Deep Reasoning.app" / "Contents"
    for binary in (
        "MacOS/Deep Reasoning",
        "Resources/bin/uv",
        "Resources/node/bin/node",
    ):
        (app / binary).parent.mkdir(parents=True, exist_ok=True)
        (app / binary).write_text("")
    info = {"CFBundleName": "Deep Reasoning", "LSMinimumSystemVersion": "14.0"}
    info |= plist or {}
    declared = {key: value for key, value in info.items() if value is not None}
    (app / "Info.plist").write_bytes(plistlib.dumps(declared))
    (output / dmg).write_text("")
    return output


def test_the_mac_build_is_one_arm64_dmg_whose_binaries_are_arm64_only(canvas):
    built_mac_app(canvas)
    [dmg] = build.verify("mac-arm64", PINS, canvas, archs_of=lambda path: "arm64")
    assert dmg.name == ARM64_DMG


@pytest.mark.parametrize(
    ("dmg", "archs", "refused"),
    [
        ("deep-reasoning-1.0.0-rc.1-universal.dmg", "arm64", "unexpected artifacts"),
        ("deep-reasoning-1.0.0-rc.1-x64.dmg", "arm64", "unexpected artifacts"),
        (ARM64_DMG, "x86_64 arm64", "Resources/bin/uv is x86_64 arm64"),
    ],
    ids=["universal", "intel", "universal-binary"],
)
def test_a_mac_build_that_is_not_arm64_only_is_refused(canvas, dmg, archs, refused):
    built_mac_app(canvas, dmg)

    def archs_of(path: Path) -> str:
        return archs if path.name == "uv" else "arm64"

    with pytest.raises(SystemExit, match=refused):
        build.verify("mac-arm64", PINS, canvas, archs_of=archs_of)


@pytest.mark.parametrize("declared", ["12.0", "13.0", None])
def test_a_mac_app_that_opens_before_macos_14_is_refused(canvas, declared):
    """macOS 14 is the oldest the runtime's arm64 wheels install on: the app must say so
    to macOS, which then refuses to open it on an older system."""
    built_mac_app(canvas, plist={"LSMinimumSystemVersion": declared})
    with pytest.raises(SystemExit, match="LSMinimumSystemVersion"):
        build.verify("mac-arm64", PINS, canvas, archs_of=lambda path: "arm64")


@pytest.mark.parametrize(
    ("target", "machine", "builds"),
    [
        ("mac-arm64", ("Darwin", "arm64"), True),
        ("mac-arm64", ("Darwin", "x86_64"), False),
        ("mac-arm64", ("Linux", "aarch64"), False),
        ("linux", ("Linux", "x86_64"), True),
        ("linux", ("Darwin", "arm64"), False),
    ],
)
def test_a_target_builds_only_on_the_machine_it_is_for(target, machine, builds):
    """The Canvas fork packages its runtimes for the machine it builds on."""
    refusal = build.wrong_machine(target, *machine)
    assert (refusal is None) is builds
    if not builds:
        assert refusal.startswith(f"✗ desktop/build.py {target} builds for ")


def test_the_build_offers_no_universal_or_intel_mac_target():
    with pytest.raises(SystemExit):
        build.main(["mac-universal"])
    assert set(build.ARTIFACT_KINDS) == {"linux", "mac-arm64"}


# ── A hand or dispatch run's replaced pins (--canvas-commit, --sdk-commit) ─────────

NEW_CANVAS = "e" * 40
NEW_SDK = "f" * 40


def test_a_replaced_canvas_commit_skips_only_its_own_tag_and_branch_checks(
    canvas, repo
):
    pins = build.with_commits(PINS, canvas=NEW_CANVAS)
    assert pins.canvas_fork.commit == NEW_CANVAS
    assert problems(canvas, repo, pins) == []
    moved = problems(canvas, repo, pins, tags={"refs/tags/dr-2^{}": "b" * 40})
    assert moved == [build.tag_moved("SDK fork", "dr-2", "b" * 40, SDK_COMMIT)]


def test_a_replaced_sdk_commit_skips_only_its_own_tag_and_branch_checks(canvas, repo):
    pins = build.with_commits(PINS, sdk=NEW_SDK)
    rewire(canvas, agentServerGitRef=NEW_SDK)  # as checkout_canvas writes it
    assert problems(canvas, repo, pins) == []
    assert problems(canvas, repo, pins, on_branch={SDK_COMMIT, NEW_SDK}) == [
        build.off_branch("Canvas fork", CANVAS_COMMIT)
    ]


def test_a_replaced_canvas_commit_must_still_be_able_to_lock(canvas, repo):
    pins = build.with_commits(PINS, canvas=NEW_CANVAS)
    change_defaults(canvas, lambda defaults: defaults.pop("agent"))
    assert problems(canvas, repo, pins) == [
        build.fork_lacks_setting("eeeeeee", "agent.lockedProfile")
    ]


def test_the_launcher_installs_the_replaced_sdk_commit(tmp_path):
    fork = tmp_path / "canvas-fork"
    (fork / "config").mkdir(parents=True)
    (fork / "config" / "defaults.json").write_text(json.dumps(DEFAULTS))
    for argv in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "a fork"]):
        subprocess.run([*GIT, *argv], cwd=fork, check=True)
    head = build.git("rev-parse", "HEAD", cwd=fork).strip()
    pins = build.with_commits(
        dataclasses.replace(
            PINS, canvas_fork=build.ForkPin(str(fork), CANVAS_COMMIT, "dr-1")
        ),
        canvas=head,
        sdk=NEW_SDK,
    )
    checkout = build.checkout_canvas(pins, tmp_path / "work")
    defaults = json.loads((checkout / "config" / "defaults.json").read_text())
    assert defaults["sources"] == DEFAULTS["sources"] | {"agentServerGitRef": NEW_SDK}


def test_the_run_says_which_pins_it_replaced():
    pins = build.with_commits(PINS, canvas=NEW_CANVAS, sdk=NEW_SDK)
    assert build.replaced_pins(pins) == (
        "⚠ This run builds the Canvas fork at eeeeeee and the SDK fork at fffffff in "
        "place of desktop/pins.toml's, without their tag and branch checks: never a "
        "release."
    )


def test_a_replacement_that_is_not_a_full_commit_is_refused_before_anything_runs(
    capsys,
):
    assert build.main(["check", "--canvas-commit", "ee7a150"]) == 1
    assert "--canvas-commit must be a full 40-hex commit" in capsys.readouterr().err


def test_a_release_never_builds_from_replaced_pins():
    release = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text()
    assert "desktop/build.py" in release
    assert "--canvas-commit" not in release and "--sdk-commit" not in release


# The browser version's tarball (TASK-48 §3.3, §7.3).
SIRV_LOCK = {
    "lockfileVersion": 3,
    "packages": {
        "": {"dependencies": {"sirv": "3.0.2", "httpxy": "0.5.5", "vite": "6.0.0"}},
        "node_modules/sirv": {
            "version": "3.0.2",
            "dependencies": {
                "@polka/url": "^1.0.0-next.24",
                "mrmime": "^2.0.0",
                "totalist": "^3.0.0",
            },
        },
        "node_modules/@polka/url": {"version": "1.0.0-next.29"},
        "node_modules/mrmime": {"version": "2.0.1"},
        # sirv takes its own totalist; the hoisted one is vite's.
        "node_modules/sirv/node_modules/totalist": {"version": "3.0.1"},
        "node_modules/totalist": {"version": "1.1.0"},
        "node_modules/httpxy": {
            "version": "0.5.5",
            "optionalDependencies": {"mrmime": "*"},
        },
        "node_modules/vite": {"version": "6.0.0", "dependencies": {"totalist": "*"}},
    },
}
SIRV_CLOSURE = {
    "node_modules/sirv": "3.0.2",
    "node_modules/@polka/url": "1.0.0-next.29",
    "node_modules/mrmime": "2.0.1",
    "node_modules/sirv/node_modules/totalist": "3.0.1",
    "node_modules/httpxy": "0.5.5",
}
# The fork's two files W13 reads, as far as it reads them (dr-3's lines).
BUILDER_CONFIG = 'const RUNTIME_PACKAGES = ["sirv", "httpxy"];\n'
ELECTRON_MAIN = """async function startStack() {
  const result = await main({
    bannerTitle: "OpenHands Agent Canvas",
    staticMode: true,
    staticDir: buildDir,
    mode: "agent-canvas",
    isPublic: false,
    skipNpmCheck: true,
    agentServerReadyTimeoutMs: 10 * 60_000,
    onServiceLog: handleServiceLog,
  });
}
"""
COMMAND = ["sh", "-c", "script", "dr-app-bootstrap", "spec", "repo", "c" * 40]
# patch_defaults' output for PINS, never literals: a key it gains needs no edit here.
PATCHED = build.patch_defaults(
    DEFAULTS,
    state_dir=build.STATE_DIR,
    command=COMMAND,
    app_title=PINS.app.product_name,
    exclude_newer=PINS.app.uv_exclude_newer,
)


def test_the_runtime_closure_is_what_sirv_and_httpxy_resolve_to():
    assert build.runtime_closure(SIRV_LOCK, build.WEB_RUNTIME_PACKAGES) == SIRV_CLOSURE
    broken = copy.deepcopy(SIRV_LOCK)
    del broken["packages"]["node_modules/mrmime"]
    with pytest.raises(ValueError, match="mrmime"):
        build.runtime_closure(broken, build.WEB_RUNTIME_PACKAGES)


@pytest.fixture
def web_checkout(tmp_path: Path) -> tuple[Path, dict]:
    """A Canvas checkout as prepare() leaves it: built, its defaults patched, and its
    node_modules installed from SIRV_LOCK."""
    checkout = tmp_path / "work" / "canvas"
    defaults = copy.deepcopy(PATCHED)
    files = {
        "build/index.html": "<!doctype html>",
        "build/assets/app.js": "",
        "config/defaults.json": json.dumps(defaults, indent=2) + "\n",
        "scripts/dev-with-automation.mjs": "",
        "scripts/build-tools.cjs": "",
        "scripts/vercel-install.sh": "",
        "tools/canvas_ui_tool.py": "",
        "LICENSE": "MIT License\n",
        "package-lock.json": json.dumps(SIRV_LOCK),
        "electron-builder.config.mjs": BUILDER_CONFIG,
        "electron/main.mjs": ELECTRON_MAIN,
        "src/main.tsx": "",
    }
    for path, locked in SIRV_LOCK["packages"].items():
        if path:
            manifest = {"name": path.rsplit("node_modules/", 1)[1], **locked}
            files[f"{path}/package.json"] = json.dumps(manifest)
            files[f"{path}/index.js"] = ""
    for path, content in files.items():
        (checkout / path).parent.mkdir(parents=True, exist_ok=True)
        (checkout / path).write_text(content)
    return checkout, defaults


def tarball_paths(tarball: Path) -> set[str]:
    with tarfile.open(tarball) as archive:
        return {m.name for m in archive.getmembers() if m.isfile()}


def tarball_json(tarball: Path, path: str) -> dict:
    with tarfile.open(tarball) as archive:
        return json.load(archive.extractfile(f"package/{path}"))


@pytest.mark.skipif(shutil.which("npm") is None, reason="packs the tarball with npm")
def test_the_web_package_bundles_exactly_its_closure(tmp_path, web_checkout):
    canvas, defaults = web_checkout
    tarball = build.package_web(
        pins=PINS, repo=tmp_path, canvas=canvas, defaults=defaults
    )
    assert tarball == tmp_path / "dist" / "deep-reasoning-web-1.0.0-rc.1.tgz"
    modules = {p for p in tarball_paths(tarball) if "/node_modules/" in p}
    assert modules == {
        f"package/{path}/{file}"
        for path in SIRV_CLOSURE
        for file in ("package.json", "index.js")
    }
    assert tarball_paths(tarball) - modules == {
        "package/LICENSE",
        "package/package.json",
        "package/bin/deep-reasoning.mjs",
        "package/build/index.html",
        "package/build/assets/app.js",
        "package/config/defaults.json",
        "package/scripts/dev-with-automation.mjs",
        "package/scripts/build-tools.cjs",
        "package/tools/canvas_ui_tool.py",
    }
    assert tarball_json(tarball, "package.json") == build.web_package_json(
        "1.0.0-rc.1", SIRV_CLOSURE
    )
    assert build.web_package_json("1.0.0-rc.1", SIRV_CLOSURE)["dependencies"] == {
        "sirv": "3.0.2",
        "httpxy": "0.5.5",
    }
    assert tarball_json(tarball, "config/defaults.json") == PATCHED


@pytest.mark.parametrize(
    ("file", "changed", "problem"),
    [
        (
            "electron-builder.config.mjs",
            'const RUNTIME_PACKAGES = ["sirv", "httpxy", "winston"];\n',
            build.runtime_packages_changed(["sirv", "httpxy", "winston"]),
        ),
        (
            "electron/main.mjs",
            ELECTRON_MAIN.replace("10 * 60_000", "15 * 60_000"),
            build.electron_call_changed(["agentServerReadyTimeoutMs: 10 * 60_000"]),
        ),
        (
            "electron/main.mjs",
            ELECTRON_MAIN.replace("    skipNpmCheck: true,\n", ""),
            build.electron_call_changed(["skipNpmCheck: true"]),
        ),
    ],
    ids=["another-package", "another-timeout", "an-option-gone"],
)
def test_a_fork_that_changed_its_runtime_packages_or_electrons_call_is_refused(
    web_checkout, file, changed, problem
):
    canvas, _ = web_checkout
    assert build.check_web_contract(canvas) == []
    (canvas / file).write_text(changed)
    assert build.check_web_contract(canvas) == [problem]


ENTRY = (ROOT / "desktop" / "web.mjs").read_bytes()
GOOD_TARBALL = {
    "package/package.json": json.dumps(
        build.web_package_json("1.0.0-rc.1", SIRV_CLOSURE)
    ).encode(),
    "package/bin/deep-reasoning.mjs": ENTRY,
    "package/config/defaults.json": json.dumps(PATCHED).encode(),
    **{f"package/{path}/package.json": b"{}" for path in SIRV_CLOSURE},
}


@pytest.mark.parametrize(
    ("changed", "why"),
    [
        (
            {"package/build/deep_reasoner/v2.py": b""},
            "carries deep_reasoner: ['package/build/deep_reasoner/v2.py']",
        ),
        ({"elsewhere/x.js": b""}, "has a member outside package/: elsewhere/x.js"),
        (
            {"package/node_modules/vite/package.json": b"{}"},
            "bundles ['node_modules/vite'] beyond sirv's and httpxy's closure",
        ),
        (
            {"package/config/defaults.json": json.dumps(DEFAULTS).encode()},
            "carries other defaults than this build wrote",
        ),
        (
            {"package/bin/deep-reasoning.mjs": b"// another entry\n"},
            "carries another bin/deep-reasoning.mjs than desktop/web.mjs",
        ),
        (
            {
                "package/package.json": json.dumps(
                    {"name": "deep-reasoning-web"}
                ).encode()
            },
            "carries another package.json than the build writes",
        ),
    ],
    ids=[
        "deep-reasoner",
        "outside",
        "beyond-closure",
        "defaults",
        "entry",
        "package-json",
    ],
)
def test_a_web_tarball_is_refused_for_each_thing_it_must_not_carry(
    tmp_path, changed, why
):
    name = "deep-reasoning-web-1.0.0-rc.1.tgz"

    def verify(members: dict[str, bytes]) -> None:
        build.verify_web(
            write_tarball(tmp_path / name, members),
            version="1.0.0-rc.1",
            defaults=PATCHED,
            closure=SIRV_CLOSURE,
            entry=ENTRY,
        )

    verify(GOOD_TARBALL)
    with pytest.raises(SystemExit) as refused:
        verify(GOOD_TARBALL | changed)
    assert str(refused.value) == build.web_tarball_wrong(name, why)


def test_web_builds_on_any_machine_and_check_combines_with_no_target():
    """The tarball is static files and scripts, so no machine is the wrong one. check
    stands alone, and some target must be named."""
    machines = [
        ("Linux", "x86_64"),
        ("Darwin", "arm64"),
        ("Darwin", "x86_64"),
        ("Linux", "aarch64"),
    ]
    assert [build.wrong_machine("web", *machine) for machine in machines] == [None] * 4
    for together in (["check", "web"], ["linux", "check"], []):
        with pytest.raises(SystemExit) as refused:
            build.main(together)
        assert refused.value.code == 2
