"""dr-app's harness: a stub uv and git on PATH that record their argv, and a layout under
tmp_path (D5 §7.2)."""

import json
import os
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from dr_app.layout import AppLayout

REPO = "https://github.com/michaeltheologitis/deep-reasoning"
COMMIT = "a1b2c3d4" * 5
NEXT_COMMIT = "e5f6a7b8" * 5
DEV_BIN = Path(sys.executable).parent
DR_APP = str(DEV_BIN / "dr-app")
ROOT = Path(__file__).resolve().parents[2]

# Each stub appends {"tool", "argv", "env"} to $STUB_LOG, does what the real tool would
# leave behind, and exits with $STUB_<TOOL>_<COMMAND>_EXIT when that is set: the command
# is the first argument without its dashes, as in STUB_GIT_LS_REMOTE_EXIT.
STUB = """#!{python}
import json, os, pathlib, shutil, sys
tool, argv = pathlib.Path(sys.argv[0]).name, sys.argv[1:]
watched = ("GIT_TERMINAL_PROMPT", "GIT_SSH_COMMAND", "PATH", "UV_PROJECT_ENVIRONMENT")
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({{"tool": tool, "argv": argv,
                          "env": {{k: os.environ.get(k) for k in watched}}}}) + "\\n")
{body}
sys.exit(int(os.environ.get("STUB_" + tool.upper() + "_" + (argv[:1] or ["x"])[0].lstrip("-").upper().replace("-", "_") + "_EXIT", "0")))
"""
# A fetched commit's tree holds this repository's uv.lock.
GIT = """
if argv[:1] == ["--version"]:
    print("git version 2.39.5")
if argv[:1] == ["init"]:
    pathlib.Path(argv[-1]).mkdir(parents=True)
if argv[:1] == ["checkout"]:
    shutil.copy({uv_lock!r}, "uv.lock")
"""
# What uv writes at the head of a command in a --relocatable venv: sh starts the python
# beside the command's real path.
RELOCATABLE_HEAD = (
    "#!/bin/sh\n"
    '\'\'\'exec\' "$(dirname -- "$(realpath -- "$0")")"/\'python\' "$0" "$@"\n'
    "' '''\n"
)
# Like uv's, the commands uv sync writes start the venv's python by the absolute path it
# had then, unless the venv was made --relocatable.
UV = """
if argv[:1] == ["venv"]:
    venv = pathlib.Path(argv[-1])
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "python").write_text("#!/bin/sh\\nexec {python} \\"$@\\"\\n")
    (venv / "bin" / "python").chmod(0o755)
    relocatable = "--relocatable" in argv
    (venv / "pyvenv.cfg").write_text("relocatable = true\\n" if relocatable else "")
    print("Creating virtual environment at:", argv[-1])
if argv[:1] == ["sync"]:
    bin_ = pathlib.Path(os.environ["UV_PROJECT_ENVIRONMENT"]) / "bin"
    relocatable = "relocatable = true" in (bin_.parent / "pyvenv.cfg").read_text()
    head = {relocatable_head} if relocatable else "#!" + str(bin_ / "python") + "\\n"
    for name in ("dr-acp", "dr-library", "dr-app", "dr"):
        (bin_ / name).write_text(head + "print(" + repr(name) + ", 'ran')\\n")
        (bin_ / name).chmod(0o755)
    print("Resolved 173 packages")
    print("Installed 173 packages")
"""


@dataclass
class Stubs:
    bin: Path
    log_path: Path

    def calls(self, tool: str | None = None) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        lines = [json.loads(line) for line in self.log_path.read_text().splitlines()]
        return [c for c in lines if tool in (None, c["tool"])]

    def argvs(self, tool: str) -> list[list[str]]:
        return [c["argv"] for c in self.calls(tool)]


@pytest.fixture
def layout() -> Iterator[AppLayout]:
    """A home short enough for deep_reasoner's Claude sockets, which tmp_path is not."""
    with tempfile.TemporaryDirectory(prefix="dr-app-", dir="/tmp") as short:
        yield AppLayout(Path(short) / "home" / ".deep-reasoning")


@pytest.fixture
def stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Stubs:
    """uv and git first on PATH; whatever else PATH holds stays reachable."""
    bin_ = tmp_path / "stub-bin"
    bin_.mkdir()
    for tool, body in (("git", GIT), ("uv", UV)):
        path = bin_ / tool
        filled = body.format(
            python=sys.executable,
            relocatable_head=repr(RELOCATABLE_HEAD),
            uv_lock=str(ROOT / "uv.lock"),
        )
        path.write_text(STUB.format(python=sys.executable, body=filled))
        path.chmod(0o755)
    log = tmp_path / "stub-calls.jsonl"
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STUB_LOG", str(log))
    return Stubs(bin_, log)
