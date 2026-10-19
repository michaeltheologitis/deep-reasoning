"""deep-reasoning [--port N] [--no-open] [--tarball FILE]: what uvx runs (TASK-48 §3.1).

It fetches and nothing else: Node and the release's tarball, each once, then execs the
tarball's entry on that Node, which checks, cleans the environment, takes the ports and
starts the stack as the desktop app does.
"""

import argparse
import os
import re
import shutil
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final

from dr_web import texts
from dr_web.cache import (
    FetchError,
    WebLayout,
    ensure_node,
    released_tarball,
    remove_leftovers,
    unpacked,
)

RELEASE: Final = "1.0.0-rc.1"  # desktop/pins.toml's [app] version
REPOSITORY: Final = "https://github.com/michaeltheologitis/deep-reasoning"
SUBDIRECTORY: Final = "packages/dr-web"
COMMAND: Final = "deep-reasoning"
EXIT_NEEDS: Final = 22  # web.mjs's EXIT.needs
EXIT_FETCH: Final = 23
COMMIT: Final = re.compile(r"[0-9a-f]{40}")


def command_for(commit: str) -> str:
    """The README's and the release notes' line. Raises ValueError for anything but a
    full 40-hex commit: a tag would need the network on every start."""
    if not COMMIT.fullmatch(commit):
        raise ValueError(f"not a full 40-hex commit: {commit!r}")
    return f"uvx --from git+{REPOSITORY}@{commit}#subdirectory={SUBDIRECTORY} {COMMAND}"


def find_uv(env: Mapping[str, str]) -> str:
    """env["UV"], which uvx sets to its own binary, else uv on env["PATH"]. Raises
    FetchError(22, texts.NO_UV)."""
    uv = env.get("UV") or shutil.which("uv", path=env.get("PATH", ""))
    if not uv:
        raise FetchError(EXIT_NEEDS, texts.NO_UV)
    return uv


def stack_path(path: str, *, node_bin: Path, tool_bin: Path, uv: str) -> str:
    """node_bin, then path without tool_bin (uvx's environment, whose python would
    shadow the user's in every conversation), then uv's folder when no uvx is on what is
    left."""
    rest = [
        entry for entry in path.split(os.pathsep) if entry and Path(entry) != tool_bin
    ]
    if shutil.which("uvx", path=os.pathsep.join(rest)) is None:
        rest.append(str(Path(uv).parent))
    return os.pathsep.join([str(node_bin), *rest])


def main(argv: Sequence[str] | None = None) -> int:
    """deep-reasoning [--port N] [--no-open] [--tarball FILE]. Execs Node on success, so
    returns only a failure's exit code (22 or 23); a bad option exits 2."""
    parser = argparse.ArgumentParser(prog=COMMAND, description=__doc__)
    parser.add_argument("--port", type=int, help="the page's port (default 8000)")
    parser.add_argument("--no-open", action="store_true", help="open no browser")
    parser.add_argument("--tarball", type=Path, help="a tarball build.py web made")
    args = parser.parse_args(argv)
    layout = WebLayout.default()
    try:
        uv = find_uv(os.environ)
        _make_root(layout)
        remove_leftovers(layout)
        node = ensure_node(layout, uv=uv, python=sys.executable, log=say)
        tarball = args.tarball or released_tarball(layout, RELEASE, log=say)
        expected = None if args.tarball else RELEASE
        package = unpacked(layout, tarball, expect_version=expected)
    except FetchError as error:
        say(error.message)
        return error.exit_code
    forward = [
        *(("--port", str(args.port)) if args.port is not None else ()),
        *(("--no-open",) if args.no_open else ()),
    ]
    path = stack_path(
        os.environ.get("PATH", ""),
        node_bin=node.parent,
        tool_bin=Path(sys.executable).parent,
        uv=uv,
    )
    entry = package / "bin" / "deep-reasoning.mjs"
    os.execve(str(node), [str(node), str(entry), *forward], os.environ | {"PATH": path})
    return 1  # execve does not return


def say(line: str) -> None:
    print(line, flush=True)


def _make_root(layout: WebLayout) -> None:
    """~/.deep-reasoning created private, as dr-app's setup lock makes it, then web/."""
    if not layout.root.parent.exists():
        layout.root.parent.mkdir(mode=0o700, parents=True)
    layout.root.mkdir(exist_ok=True)
