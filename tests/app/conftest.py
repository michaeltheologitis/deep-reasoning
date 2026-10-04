"""dr-app's harness: a stub uv, uvx and git on PATH that record their argv, a layout under
tmp_path, and an in-test agent-server (D5 §7.2)."""

import json
import os
import secrets
import shutil
import sys
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from dr_app.layout import AppLayout
from tests.app.fake_agent_server import FakeAgentServer

REPO = "https://github.com/michaeltheologitis/deep-reasoning"
COMMIT = "a1b2c3d4" * 5
NEXT_COMMIT = "e5f6a7b8" * 5
DEV_BIN = Path(sys.executable).parent
DR_APP = str(DEV_BIN / "dr-app")
D3_APP = Path(__file__).resolve().parents[2] / "src" / "deep_reasoning" / "canvas_app"

# Each stub appends {"tool", "argv", "env"} to $STUB_LOG, does what the real tool would
# leave behind, and exits with $STUB_<TOOL>_<COMMAND>_EXIT when that is set: the command
# is the first argument without its dashes, as in STUB_GIT_LS_REMOTE_EXIT.
STUB = """#!{python}
import json, os, pathlib, sys
tool, argv = pathlib.Path(sys.argv[0]).name, sys.argv[1:]
watched = ("GIT_TERMINAL_PROMPT", "GIT_SSH_COMMAND", "PATH")
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({{"tool": tool, "argv": argv,
                          "env": {{k: os.environ.get(k) for k in watched}}}}) + "\\n")
{body}
sys.exit(int(os.environ.get("STUB_" + tool.upper() + "_" + (argv[:1] or ["x"])[0].lstrip("-").upper().replace("-", "_") + "_EXIT", "0")))
"""
GIT = """
if argv[:1] == ["--version"]:
    print("git version 2.39.5")
"""
UV = """
if argv[:1] == ["venv"]:
    bin_ = pathlib.Path(argv[-1]) / "bin"
    bin_.mkdir(parents=True)
    (bin_ / "python").write_text("#!/bin/sh\\nexec {python} \\"$@\\"\\n")
    (bin_ / "python").chmod(0o755)
    print("Creating virtual environment at:", argv[-1])
if argv[:2] == ["pip", "sync"]:
    bin_ = pathlib.Path(argv[argv.index("--python") + 1]).parent
    for name in ("dr-acp", "dr-library", "dr-app", "dr"):
        (bin_ / name).write_text("#!/bin/sh\\n")
        (bin_ / name).chmod(0o755)
    with open(os.environ["STUB_LOG"], "a") as log:
        log.write(json.dumps({{"requirements": pathlib.Path(argv[-1]).read_text()}}) + "\\n")
    print("Resolved 170 packages")
    print("Installed 170 packages")
"""
UVX = ""


@dataclass
class Stubs:
    bin: Path
    log_path: Path

    def calls(self, tool: str | None = None) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        lines = [json.loads(line) for line in self.log_path.read_text().splitlines()]
        return [c for c in lines if "tool" in c and tool in (None, c["tool"])]

    def requirements(self) -> list[str]:
        lines = [json.loads(line) for line in self.log_path.read_text().splitlines()]
        return [c["requirements"] for c in lines if "requirements" in c]

    def argvs(self, tool: str) -> list[list[str]]:
        return [c["argv"] for c in self.calls(tool)]


@pytest.fixture
def layout() -> Iterator[AppLayout]:
    """A home short enough for deep_reasoner's Claude sockets, which tmp_path is not."""
    with tempfile.TemporaryDirectory(prefix="dr-app-", dir="/tmp") as short:
        yield AppLayout(Path(short) / "home" / ".deep-reasoning")


@pytest.fixture
def stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Stubs:
    """uv, uvx and git first on PATH; whatever else PATH holds stays reachable."""
    bin_ = tmp_path / "stub-bin"
    bin_.mkdir()
    for tool, body in (("git", GIT), ("uv", UV), ("uvx", UVX)):
        path = bin_ / tool
        path.write_text(
            STUB.format(python=sys.executable, body=body.format(python=sys.executable))
        )
        path.chmod(0o755)
    log = tmp_path / "stub-calls.jsonl"
    monkeypatch.setenv("PATH", f"{bin_}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("STUB_LOG", str(log))
    return Stubs(bin_, log)


@pytest.fixture
def agent_server() -> Iterator[FakeAgentServer]:
    with FakeAgentServer(session_key=f"session-{secrets.token_hex(16)}") as fake:
        yield fake


@pytest.fixture
def app_files(tmp_path: Path) -> Path:
    """A copy of D3's built App, which a test may change."""
    copy = tmp_path / "canvas_app"
    shutil.copytree(D3_APP, copy, ignore=shutil.ignore_patterns("__pycache__"))
    return copy


@pytest.fixture
def runtime(layout: AppLayout, app_files: Path) -> AppLayout:
    """An installed runtime whose python answers where D3's files are with app_files."""
    bin_ = layout.runtime_dir / COMMIT / "bin"
    bin_.mkdir(parents=True)
    (bin_ / "python").write_text(f"#!/bin/sh\necho {app_files}\n")
    (bin_ / "python").chmod(0o755)
    (layout.current_runtime).symlink_to(COMMIT)
    return layout
