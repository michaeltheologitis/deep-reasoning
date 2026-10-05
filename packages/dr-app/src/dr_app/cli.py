"""dr-app: the setup command the app's launcher runs on every launch, and export and home
for the user (D5 §4.3.2, §4.4, §4.8)."""

import argparse
import fcntl
import os
import platform
import shutil
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Final

from dr_app import texts
from dr_app.layout import (
    EXIT_CHECK,
    EXIT_HOME,
    NETWORK_FILESYSTEMS,
    AppLayout,
    RuntimeRecord,
    SetupError,
    SetupState,
    check_socket_room,
    choose_home,
    filesystem_type,
)
from dr_app.profile import DEFAULT_SPEND_CAP_USD
from dr_app.runtime import (
    COMMIT,
    check_git,
    check_readable,
    deep_reasoner_pin,
    fetched_source,
    host_path,
    install_runtime,
    run_logged,
    runtime_is_current,
)

PHASES: Final = ("before-start", "after-ready")
PHASE_ENV: Final = "OH_CANVAS_SETUP_PHASE"
LINKED: Final = ("dr-app", "dr")  # in bin/, to the runtime's own


def say(line: str) -> None:
    """One line of the startup log."""
    print(line, flush=True)


def duration(seconds: float) -> str:
    """1m 52s, or 4s."""
    minutes, rest = divmod(round(seconds), 60)
    return f"{minutes}m {rest}s" if minutes else f"{rest}s"


@contextmanager
def setup_lock(layout: AppLayout) -> Iterator[None]:
    """setup.lock held exclusively: a terminal run and a launch never interleave."""
    layout.root.mkdir(mode=0o700, parents=True, exist_ok=True)
    layout.root.chmod(0o700)
    with layout.lock_file.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def before_start(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    env: Mapping[str, str],
) -> None:
    """§4.4: the data home, then the runtime when it is not current, then bin/'s links."""
    state = SetupState.load(layout.setup_file)
    choice = choose_home(
        layout,
        Path(state.dr_home) if state.dr_home else None,
        system=platform.system(),
        uid=os.getuid(),
    )
    if str(choice.path) != state.dr_home:
        say(
            texts.home_network(choice.filesystem or "", str(choice.path))
            if choice.reason == "network-home"
            else texts.home_local(str(choice.path))
        )
        state.dr_home = str(choice.path)
    if not COMMIT.fullmatch(commit):
        raise ValueError(f"not a full commit: {commit!r}")
    if not runtime_is_current(layout, state.runtime, commit):
        first = state.runtime is None
        state.runtime = install(layout, repo, commit, first=first, env=env)
    layout.bin_dir.mkdir(exist_ok=True)
    for name in LINKED:
        link = layout.bin_dir / name
        if not link.is_symlink():
            link.symlink_to(layout.current_runtime / "bin" / name)
    state.save(layout.setup_file)


def install(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    first: bool,
    env: Mapping[str, str],
) -> RuntimeRecord:
    """§4.4 steps 4 and 5: the checks, which leave nothing installed when one fails,
    then the runtime from the commit's own tree."""
    version = check_git()
    uv = shutil.which("uv", path=env.get("PATH"))
    if uv is None:
        raise SetupError(EXIT_CHECK, texts.NO_UV)
    with fetched_source(layout, repo, commit, log=say) as source:
        pin = deep_reasoner_pin(source)
        check_readable(pin.url)
        say(texts.checks_ok(version, host_path(pin.url)))
        if first:
            say(texts.safety(DEFAULT_SPEND_CAP_USD))
        say(texts.installing(commit[:7], pin.commit[:7]))
        started = time.monotonic()
        record = install_runtime(layout, source, commit, uv=uv, log=say)
    say(texts.installed(duration(time.monotonic() - started)))
    return record


def _setup(layout: AppLayout, args: argparse.Namespace, env: Mapping[str, str]) -> None:
    phase = args.phase or env.get(PHASE_ENV)
    with setup_lock(layout):
        if phase in (None, "before-start"):
            before_start(layout, args.repo, args.commit, env=env)


def _export(layout: AppLayout, args: argparse.Namespace, env: Mapping[str, str]) -> int:
    """dr-library export DIR --home DR_HOME from the runtime, its output and exit code
    passed through."""
    dr_library = layout.current_runtime / "bin" / "dr-library"
    home = SetupState.load(layout.setup_file).dr_home
    if not home or not dr_library.exists():
        raise SetupError(EXIT_HOME, texts.NOTHING_INSTALLED)
    namespace = ("--namespace", args.namespace) if args.namespace else ()
    argv = [str(dr_library), "export", str(args.dir), "--home", home, *namespace]
    return run_logged(argv, env=env, log=say)


def _home(layout: AppLayout, args: argparse.Namespace) -> None:
    """Without DIR: the data home and its filesystem. With DIR: recorded for the next
    launch, which moves nothing."""
    linux = platform.system() == "Linux"
    with setup_lock(layout):
        state = SetupState.load(layout.setup_file)
        current = Path(state.dr_home) if state.dr_home else layout.root
        if args.dir is None:
            fstype = filesystem_type(current) if linux else None
            say(f"{current} ({fstype})" if fstype else str(current))
            return
        if not args.dir.is_absolute():
            refusal = texts.home_refused(str(args.dir), "is not an absolute path")
            raise SetupError(EXIT_HOME, refusal)
        check_socket_room(args.dir, system=platform.system())
        args.dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        fstype = filesystem_type(args.dir) if linux else None
        if fstype in NETWORK_FILESYSTEMS:
            reason = f"is on a network filesystem ({fstype})"
            raise SetupError(EXIT_HOME, texts.home_refused(str(args.dir), reason))
        if not args.dir.is_dir() or args.dir.stat().st_uid != os.getuid():
            info = args.dir.stat()
            unsafe = texts.home_unsafe(
                str(args.dir), str(info.st_uid), oct(info.st_mode & 0o777)
            )
            raise SetupError(EXIT_HOME, unsafe)
        state.dr_home = str(args.dir)
        state.save(layout.setup_file)
        say(texts.home_set(str(args.dir), str(current)))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dr-app", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="install or repair; run by the launcher")
    setup.add_argument("--phase", choices=PHASES)
    setup.add_argument("--repo", required=True)
    setup.add_argument("--commit", required=True)
    exported = commands.add_parser("export", help="write the Library as a dr config")
    exported.add_argument("dir", type=Path)
    exported.add_argument("--namespace")
    home = commands.add_parser("home", help="show or choose where your data lives")
    home.add_argument("dir", type=Path, nargs="?")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """dr-app setup [--phase PHASE] --repo URL --commit SHA | export DIR [--namespace
    NAME] | home [DIR]."""
    args = _parser().parse_args(argv)
    layout = AppLayout.default()
    env = os.environ
    commands: dict[str, Callable[[], int | None]] = {
        "setup": lambda: _setup(layout, args, env),
        "export": lambda: _export(layout, args, env),
        "home": lambda: _home(layout, args),
    }
    try:
        return commands[args.command]() or 0
    except SetupError as error:
        say(error.message)
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
