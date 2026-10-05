"""The desktop app's build: check that the pins belong together, write D5's values into a
checkout of the Canvas fork, build the frontend and package it under our name (D5 §4.2).

uv run desktop/build.py {linux|mac-arm64|check} [--work DIR]

Standard library only. Neither fork gets a commit: every change is made to a build
checkout under --work.
"""

import argparse
import copy
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

REPO: Final = Path(__file__).resolve().parents[1]
# What every user's setup fetches (§4.2.3).
DEEP_REASONING: Final = "https://github.com/michaeltheologitis/deep-reasoning"
PINS: Final = REPO / "desktop" / "pins.toml"
BOOTSTRAP: Final = REPO / "desktop" / "bootstrap.sh"
WRAPPER_CONFIG: Final = REPO / "desktop" / "electron-builder.dr.mjs"
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
# (v2) The branch every pinned fork commit must be on (§4.2.2 check 8).
FORK_BRANCH: Final = "deep-reasoning"
STATE_DIR: Final = "~/.deep-reasoning/canvas/agent-canvas"
SETUP_PHASES: Final = ["before-start", "after-ready"]
BOOTSTRAP_NAME: Final = "dr-app-bootstrap"
TYPESCRIPT_CLIENT: Final = "@openhands/typescript-client"
ACP_PYTHON: Final = "agent-client-protocol"
ARTIFACT_KINDS: Final = {
    "linux": ("AppImage", "deb"),
    "mac-arm64": ("dmg",),
}
# The machine each target builds on (platform.system(), platform.machine()): the Canvas
# fork packages its uv and Node runtimes for the machine it runs on. Macs are Apple
# silicon only (Michael, 2026-10-04).
BUILD_MACHINES: Final = {
    "linux": ("Linux", "x86_64"),
    "mac-arm64": ("Darwin", "arm64"),
}
MAC_ARCH: Final = "arm64"
# The oldest macOS the runtime's locked arm64 wheels install on (onnxruntime's are
# macosx_14_0); the wrapper config declares it, so macOS refuses to open the app before.
MAC_MINIMUM: Final = "14.0"
# What the .app carries that must run on Apple silicon: Electron, uv and Node.
MAC_BINARIES: Final = (
    "MacOS/{product}",
    "Resources/bin/uv",
    "Resources/node/bin/node",
)
FORBIDDEN_IN_PAYLOAD: Final = "deep_reasoner"


@dataclass(frozen=True)
class ForkPin:
    repo: str
    commit: str
    tag: str


@dataclass(frozen=True)
class AppPin:
    product_name: str
    app_id: str
    executable_name: str
    version: str
    maintainer: str
    uv_version: str


@dataclass(frozen=True)
class Pins:
    canvas_fork: ForkPin
    sdk_fork: ForkPin
    app: AppPin


Target = Literal["linux", "mac-arm64"]


# The build's sentences (§6): each names the file and the two values that disagree.
def tag_moved(fork: str, tag: str, found: str | None, commit: str) -> str:
    return (
        f"✗ The {fork} tag {tag} resolves to {found[:7] if found else 'nothing'}, but "
        f"desktop/pins.toml pins {commit[:7]}. Move the tag, or the pin."
    )


def wired_elsewhere(canvas_tag: str, wired: str, sdk_tag: str, sdk: str) -> str:
    return (
        f"✗ Canvas fork {canvas_tag} runs the agent-server at {wired[:7]} (its wiring "
        f"commit), but desktop/pins.toml pins the SDK fork at {sdk_tag} ({sdk[:7]}). "
        "Bump both, or neither."
    )


def wired_to_another_repo(canvas_tag: str, wired_repo: str, sdk_repo: str) -> str:
    return (
        f"✗ Canvas fork {canvas_tag}'s config/defaults.json runs the agent-server from "
        f"{wired_repo}, but desktop/pins.toml pins the SDK fork {sdk_repo}."
    )


def client_from_elsewhere(canvas_tag: str, spec: str, sdk_tag: str) -> str:
    return (
        f"✗ Canvas fork {canvas_tag}'s package.json takes {TYPESCRIPT_CLIENT} from "
        f"{spec}, not from the SDK fork's release {sdk_tag}."
    )


def acp_differs(sdk_tag: str, theirs: str | None, ours: str | None) -> str:
    return (
        f"✗ The SDK fork's uv.lock at {sdk_tag} locks {ACP_PYTHON} {theirs}, but "
        f"deep-reasoning's uv.lock locks {ours}: both ends must run one ACP Python."
    )


def fork_sets_ours(canvas_tag: str, key: str, value: Any) -> str:
    return (
        f"✗ Canvas fork {canvas_tag}'s config/defaults.json sets {key} to "
        f"{json.dumps(value)}; the fork must leave it null, for this build to write."
    )


def checkout_dirty(changed: int) -> str:
    return (
        f"✗ This deep-reasoning checkout has {changed} uncommitted change(s): every "
        "user's setup fetches the commit, so build from a clean checkout."
    )


def head_unpushed(head: str) -> str:
    return (
        f"✗ deep-reasoning's HEAD ({head[:7]}) is on no branch of origin: every user's "
        "setup fetches it, so push it first."
    )


def off_branch(fork: str, commit: str) -> str:
    return (
        f"✗ The {fork} commit {commit[:7]} is not on its {FORK_BRANCH} branch: pin a "
        "commit its stacks merged there."
    )


def wrong_machine(target: Target, system: str, machine: str) -> str | None:
    """The refusal for a build on a machine the target is not for; None when it is."""
    want_system, want_machine = BUILD_MACHINES[target]
    if (system, machine) == (want_system, want_machine):
        return None
    return (
        f"✗ desktop/build.py {target} builds for {want_system} on {want_machine}, the "
        f"machine it runs on, and this one is {system} on {machine}."
    )


def not_arm64(binary: str, archs: str) -> str:
    return f"✗ {binary} is {archs}, not {MAC_ARCH} only: Macs are Apple silicon only."


def opens_too_early(declared: str | None) -> str:
    return (
        f"✗ The app's Info.plist declares LSMinimumSystemVersion {declared}, not "
        f"{MAC_MINIMUM}: desktop/electron-builder.dr.mjs's mac block sets it."
    )


def load_pins(path: Path) -> Pins:
    """Raises ValueError naming the key for a commit that is not 40 hex."""
    raw = tomllib.loads(path.read_text())
    for fork in ("canvas_fork", "sdk_fork"):
        if not COMMIT.fullmatch(raw[fork]["commit"]):
            raise ValueError(
                f"{path}: {fork}.commit must be a full 40-hex commit, "
                f"not {raw[fork]['commit']!r}"
            )
    return Pins(
        canvas_fork=ForkPin(**raw["canvas_fork"]),
        sdk_fork=ForkPin(**raw["sdk_fork"]),
        app=AppPin(**raw["app"]),
    )


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


def locked_version(lock: str, package: str) -> str | None:
    """The version uv.lock locks for package."""
    found = re.search(
        rf'^\[\[package\]\]\nname = "{re.escape(package)}"\nversion = "([^"]+)"',
        lock,
        re.MULTILINE,
    )
    return found[1] if found else None


def _tag_commit(refs: Mapping[str, str], tag: str) -> str | None:
    """The peeled line wins for an annotated tag."""
    return refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")


def check_pins(
    pins: Pins,
    *,
    canvas: Path,
    repo: Path,
    ls_remote: Callable[[str, Sequence[str]], Mapping[str, str]],
    read_sdk_file: Callable[[str], str],
    is_on_branch: Callable[[str, str, str], bool],
) -> list[str]:
    """§4.2.2's checks; the problems as sentences, empty when the pins belong together.
    is_on_branch(repo_url, branch, commit) answers check 8; build() passes one that fetches
    without blobs."""
    problems: list[str] = []
    canvas_pin, sdk_pin = pins.canvas_fork, pins.sdk_fork
    forks = (("Canvas fork", canvas_pin), ("SDK fork", sdk_pin))
    for fork, pin in forks:
        refs = ls_remote(
            pin.repo, [f"refs/tags/{pin.tag}", f"refs/tags/{pin.tag}^{{}}"]
        )
        found = _tag_commit(refs, pin.tag)
        if found != pin.commit:
            problems.append(tag_moved(fork, pin.tag, found, pin.commit))
    defaults = json.loads((canvas / "config" / "defaults.json").read_text())
    sources = defaults.get("sources") or {}
    if sources.get("agentServerGitRepo") != sdk_pin.repo:
        wired_repo = str(sources.get("agentServerGitRepo"))
        problems.append(wired_to_another_repo(canvas_pin.tag, wired_repo, sdk_pin.repo))
    if sources.get("agentServerGitRef") != sdk_pin.commit:
        wired = str(sources.get("agentServerGitRef"))
        problems.append(
            wired_elsewhere(canvas_pin.tag, wired, sdk_pin.tag, sdk_pin.commit)
        )
    package = json.loads((canvas / "package.json").read_text())
    spec = {**package.get("devDependencies", {}), **package.get("dependencies", {})}
    client = spec.get(TYPESCRIPT_CLIENT, "")
    if f"/releases/download/{sdk_pin.tag}/" not in client:
        problems.append(client_from_elsewhere(canvas_pin.tag, client, sdk_pin.tag))
    theirs = locked_version(read_sdk_file("uv.lock"), ACP_PYTHON)
    ours = locked_version((repo / "uv.lock").read_text(), ACP_PYTHON)
    if theirs is None or theirs != ours:
        problems.append(acp_differs(sdk_pin.tag, theirs, ours))
    ours_to_write = {
        "paths.stateDir": (defaults.get("paths") or {}).get("stateDir"),
        "setup.command": (defaults.get("setup") or {}).get("command"),
    }
    for key, value in ours_to_write.items():
        if value is not None:
            problems.append(fork_sets_ours(canvas_pin.tag, key, value))
    changed = git("status", "--porcelain", "--untracked-files=no", cwd=repo)
    if changed.strip():
        problems.append(checkout_dirty(len(changed.strip().splitlines())))
    if not git("branch", "-r", "--contains", "HEAD", cwd=repo).strip():
        problems.append(head_unpushed(git("rev-parse", "HEAD", cwd=repo).strip()))
    for fork, pin in forks:
        if not is_on_branch(pin.repo, FORK_BRANCH, pin.commit):
            problems.append(off_branch(fork, pin.commit))
    return problems


def setup_command(repo_url: str, commit: str, bootstrap: str) -> list[str]:
    """The setup command C3's launcher runs: sh -c <bootstrap> with the dr-app package,
    deep-reasoning's repository and the commit as $1, $2 and $3."""
    return [
        "sh",
        "-c",
        bootstrap,
        BOOTSTRAP_NAME,
        f"git+{repo_url}@{commit}#subdirectory=packages/dr-app",
        repo_url,
        commit,
    ]


def patch_defaults(
    defaults: Mapping[str, Any],
    *,
    state_dir: str,
    command: list[str],
) -> dict[str, Any]:
    """§4.2.3's four keys; every other key unchanged."""
    patched = copy.deepcopy(dict(defaults))
    patched.setdefault("paths", {})["stateDir"] = state_dir
    patched.setdefault("setup", {})["command"] = command
    patched["setup"]["phases"] = list(SETUP_PHASES)
    patched.setdefault("telemetry", {})["posthogApiKey"] = ""
    return patched


# The readers build() passes check_pins: git, with the runner's credentials.
def git_ls_remote(repo_url: str, refs: Sequence[str]) -> dict[str, str]:
    listed = git("ls-remote", repo_url, *refs)
    return {ref: sha for sha, ref in (line.split("\t") for line in listed.splitlines())}


def fork_cache(work: Path, repo_url: str) -> Path:
    """A blobless copy of the fork's deep-reasoning branch under work, fetched afresh:
    blobs arrive only when read. A bare clone keeps no fetch refspec, so the refetch
    names the branch's ref, or it would move only FETCH_HEAD."""
    cache = work / "forks" / re.sub(r"[^A-Za-z0-9]+", "-", repo_url).strip("-")
    if not cache.exists():
        git(
            "clone",
            "--bare",
            "--filter=blob:none",
            "--single-branch",
            "--branch",
            FORK_BRANCH,
            repo_url,
            str(cache),
        )
    else:
        branch = f"refs/heads/{FORK_BRANCH}"
        git("fetch", "--filter=blob:none", "origin", f"+{branch}:{branch}", cwd=cache)
    return cache


def fork_has(work: Path) -> Callable[[str, str, str], bool]:
    def is_on_branch(repo_url: str, branch: str, commit: str) -> bool:
        cache = fork_cache(work, repo_url)
        found = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, f"refs/heads/{branch}"],
            cwd=cache,
            capture_output=True,
            check=False,
        )
        return found.returncode == 0

    return is_on_branch


def run(
    argv: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None
) -> None:
    print("$", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, env=None if env is None else dict(env), check=True)


def checkout_canvas(pins: Pins, work: Path) -> Path:
    """The Canvas fork at its pinned commit under work/canvas, nothing else changed."""
    canvas = work / "canvas"
    if not (canvas / ".git").exists():
        canvas.mkdir(parents=True, exist_ok=True)
        git("init", "-q", cwd=canvas)
    git(
        "fetch",
        "-q",
        "--depth",
        "1",
        pins.canvas_fork.repo,
        pins.canvas_fork.commit,
        cwd=canvas,
    )
    git("checkout", "-q", "--force", "--detach", "FETCH_HEAD", cwd=canvas)
    git("clean", "-q", "-dffx", "-e", "node_modules", cwd=canvas)
    return canvas


def payload_paths(artifact: Path, canvas: Path) -> list[str]:
    """Every path the package carries: a .deb's listing; for the rest, the unpacked tree
    electron-builder made it from."""
    if artifact.suffix == ".deb":
        listed = subprocess.run(
            ["dpkg-deb", "-c", str(artifact)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        # mode, owner, size, date, time, then the path, which may hold spaces
        return [line.split(maxsplit=5)[-1] for line in listed.splitlines() if line]
    output = canvas / "dist-electron"
    unpacked = [p for p in output.iterdir() if p.is_dir() and "unpacked" in p.name]
    unpacked += [p for p in output.glob("mac*") if p.is_dir()]
    return [str(p) for tree in unpacked for p in tree.rglob("*")]


def macho_archs(path: Path) -> str:
    """The architectures of a Mach-O file, as lipo names them ("arm64", "x86_64 arm64")."""
    return subprocess.run(
        ["lipo", "-archs", str(path)], capture_output=True, text=True, check=True
    ).stdout.strip()


def verify(
    target: Target,
    pins: Pins,
    canvas: Path,
    *,
    archs_of: Callable[[Path], str] = macho_archs,
) -> list[Path]:
    """Exactly the expected artifacts, named deep-reasoning-<version>-<arch>.<ext> (the
    .dmg's arch arm64), no deep_reasoner inside any, and for the Mac the .app's Electron,
    uv and Node arm64 only, and its Info.plist's minimum macOS MAC_MINIMUM."""
    output = canvas / "dist-electron"
    arch = MAC_ARCH if target == "mac-arm64" else "[A-Za-z0-9_]+"
    name = re.compile(
        rf"{re.escape(pins.app.executable_name)}-{re.escape(pins.app.version)}-"
        rf"{arch}\.(AppImage|deb|dmg)"
    )
    artifacts = sorted(
        p for p in output.iterdir() if p.suffix in (".AppImage", ".deb", ".dmg")
    )
    kinds = sorted(p.suffix.lstrip(".") for p in artifacts)
    if kinds != sorted(ARTIFACT_KINDS[target]) or not all(
        name.fullmatch(p.name) for p in artifacts
    ):
        raise SystemExit(
            f"✗ unexpected artifacts in {output}: {[p.name for p in artifacts]}"
        )
    for artifact in artifacts:
        leaked = [
            p for p in payload_paths(artifact, canvas) if FORBIDDEN_IN_PAYLOAD in p
        ]
        if leaked:
            raise SystemExit(
                f"✗ {artifact.name} carries {FORBIDDEN_IN_PAYLOAD}: {leaked[:3]}"
            )
    if target == "mac-arm64":
        app = output / f"mac-{MAC_ARCH}" / f"{pins.app.product_name}.app" / "Contents"
        for binary in MAC_BINARIES:
            relative = binary.format(product=pins.app.product_name)
            archs = archs_of(app / relative)
            if archs != MAC_ARCH:
                raise SystemExit(not_arm64(relative, archs))
        info = plistlib.loads((app / "Info.plist").read_bytes())
        declared = info.get("LSMinimumSystemVersion")
        if declared != MAC_MINIMUM:
            raise SystemExit(opens_too_early(declared))
    return artifacts


def check_checkouts(pins: Pins, *, repo: Path, work: Path) -> tuple[Path, list[str]]:
    """The Canvas checkout under work, and check_pins with git as every reader."""
    canvas = checkout_canvas(pins, work)
    sdk_cache = fork_cache(work, pins.sdk_fork.repo)
    problems = check_pins(
        pins,
        canvas=canvas,
        repo=repo,
        ls_remote=git_ls_remote,
        read_sdk_file=lambda path: git(
            "show", f"{pins.sdk_fork.commit}:{path}", cwd=sdk_cache
        ),
        is_on_branch=fork_has(work),
    )
    return canvas, problems


def build(target: Target, *, pins: Pins, repo: Path, work: Path) -> list[Path]:
    """Check out the Canvas fork at its commit under work/, check, patch, build, verify;
    the artifacts, copied to <repo>/dist/."""
    refusal = wrong_machine(target, platform.system(), platform.machine())
    if refusal:
        raise SystemExit(refusal)
    canvas, problems = check_checkouts(pins, repo=repo, work=work)
    if problems:
        raise SystemExit("\n".join(problems))
    head = git("rev-parse", "HEAD", cwd=repo).strip()
    defaults_file = canvas / "config" / "defaults.json"
    defaults = patch_defaults(
        json.loads(defaults_file.read_text()),
        state_dir=STATE_DIR,
        command=setup_command(DEEP_REASONING, head, BOOTSTRAP.read_text()),
    )
    defaults_file.write_text(json.dumps(defaults, indent=2) + "\n")
    # ELECTRON_ARCH unset: the fork builds for, and downloads runtimes for, this machine.
    env = {k: v for k, v in os.environ.items() if k != "ELECTRON_ARCH"}
    run(["npm", "ci"], cwd=canvas)
    run(["npm", "run", "build:app"], cwd=canvas, env=env | {"VITE_DO_NOT_TRACK": "1"})
    downloads = env | {"UV_VERSION": pins.app.uv_version}
    run(["node", "scripts/download-uv.mjs"], cwd=canvas, env=downloads)
    run(["node", "scripts/download-node.mjs"], cwd=canvas, env=downloads)
    app = {
        "DR_CANVAS_DIR": str(canvas),
        "DR_APP_PRODUCT_NAME": pins.app.product_name,
        "DR_APP_ID": pins.app.app_id,
        "DR_APP_EXECUTABLE_NAME": pins.app.executable_name,
        "DR_APP_VERSION": pins.app.version,
        "DR_APP_MAINTAINER": pins.app.maintainer,
    }
    platform_flag = "--linux" if target == "linux" else "--mac"
    shutil.rmtree(canvas / "dist-electron", ignore_errors=True)
    run(
        [
            "npx",
            "electron-builder",
            "--config",
            str(WRAPPER_CONFIG),
            "--projectDir",
            str(canvas),
            "--publish",
            "never",
            platform_flag,
        ],
        cwd=canvas,
        env=env | app,
    )
    dist = repo / "dist"
    dist.mkdir(exist_ok=True)
    copied = []
    for artifact in verify(target, pins, canvas):
        copied.append(Path(shutil.copy2(artifact, dist / artifact.name)))
    return copied


def main(argv: Sequence[str] | None = None) -> int:
    """uv run desktop/build.py {linux|mac-arm64|check} [--work DIR]."""
    parser = argparse.ArgumentParser(prog="desktop/build.py", description=__doc__)
    parser.add_argument("target", choices=[*ARTIFACT_KINDS, "check"])
    parser.add_argument("--work", type=Path, default=REPO / ".desktop-work")
    args = parser.parse_args(argv)
    try:
        pins = load_pins(PINS)
    except ValueError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1
    args.work.mkdir(parents=True, exist_ok=True)
    if args.target == "check":
        _, problems = check_checkouts(pins, repo=REPO, work=args.work)
        print("\n".join(problems) if problems else "the pins belong together ✓")
        return 1 if problems else 0
    for artifact in build(args.target, pins=pins, repo=REPO, work=args.work):
        print(artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
