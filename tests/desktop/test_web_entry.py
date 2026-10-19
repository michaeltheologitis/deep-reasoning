"""desktop/web.mjs, the browser version's entry (TASK-48 §3.2, §7.2), run black-box on the
Node dr-web installs: each test builds a tarball's tree around it whose launcher is a
stub, puts stub uv, uvx and git on PATH, and reads what the stub's main() was given."""

import json
import shutil
import signal
import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from desktop import build
from tests.desktop.app import NODE, WEB_ENTRY, evaluate_web, web_text

VERSION = "1.0.0-rc.1"
RUN_S = 20.0
# The launcher's stand-in: main() records what it was given beside itself, then does what
# stub.json says. Like the real one it stops on SIGINT, SIGTERM and SIGHUP with exit 0.
STUB_LAUNCHER = """
import { readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
const here = new URL(".", import.meta.url);
const stub = JSON.parse(readFileSync(new URL("stub.json", here), "utf8"));
const record = (name, value) => writeFileSync(new URL(name, here), JSON.stringify(value));
function shutdown() {
  console.log("Shutting down...");
  record("stopped.json", true);
  process.exit(0);
}
for (const name of ["SIGINT", "SIGTERM", "SIGHUP"]) process.on(name, shutdown);
const listen = (port) => new Promise((done) => createServer((request, response) =>
  response.writeHead(request.url === "/server_info" ? 200 : 404).end("{}")).listen(port, "127.0.0.1", done));
export async function main(options) {
  record("record.json", { options, argv: process.argv.slice(2), env: process.env });
  console.log("Agent Canvas + Automation Stack (stub)");
  if (stub.does === "ready") {
    await listen(Number(process.argv[process.argv.indexOf("--port") + 1]));
    return { agentServerReady: true };
  }
  if (stub.does === "not-ready") {
    setInterval(() => {}, 1000);
    return { agentServerReady: false };
  }
  if (stub.does === "beaten") await listen(stub.agentServer);
  throw Object.assign(new Error(stub.message), { name: stub.name }, stub.details);
}
"""
TOOLS = {
    "uv": "echo 'uv 0.8.17 (8c62bb3 2025-09-10)'",
    "uvx": "echo 'uvx 0.8.17 (8c62bb3 2025-09-10)'",
    "git": "echo 'git version 2.43.0'",
}


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@contextmanager
def held(port: int) -> Iterator[None]:
    with socket.socket() as holder:
        holder.bind(("127.0.0.1", port))
        holder.listen()
        yield


@dataclass
class Running:
    process: subprocess.Popen[str]
    lines: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        for line in self.process.stdout:
            self.lines.append(line.rstrip("\n"))

    def wait_for(self, line: str, timeout_s: float = RUN_S) -> None:
        deadline = time.monotonic() + timeout_s
        while line not in self.lines:
            assert self.process.poll() is None, (
                f"exited {self.process.returncode}: {self.lines}"
            )
            assert time.monotonic() < deadline, f"no {line!r} in {self.lines}"
            time.sleep(0.05)

    def end(self, timeout_s: float = RUN_S) -> int:
        try:
            return self.process.wait(timeout=timeout_s)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()
            time.sleep(0.1)  # the reader's last lines


@dataclass
class Tree:
    """An unpacked tarball around desktop/web.mjs: its package/ folder."""

    package: Path
    tools: Path
    home: Path
    agent_server: int
    automation: int
    ingress: int

    @property
    def scripts(self) -> Path:
        return self.package / "scripts"

    def does(self, **stub: Any) -> None:
        (self.scripts / "stub.json").write_text(json.dumps(stub))

    def record(self) -> dict[str, Any] | None:
        recorded = self.scripts / "record.json"
        return json.loads(recorded.read_text()) if recorded.exists() else None

    def tool(self, name: str, script: str | None) -> None:
        """A stub tool on PATH that runs script; None removes it."""
        path = self.tools / name
        if script is None:
            path.unlink(missing_ok=True)
            return
        path.write_text(f"#!/bin/sh\n{script}\n")
        path.chmod(0o755)

    def start(self, *args: str, env: dict[str, str] | None = None) -> Running:
        environment = {"PATH": str(self.tools), "HOME": str(self.home)} | (env or {})
        process = subprocess.Popen(
            [str(NODE), str(self.package / "bin" / "deep-reasoning.mjs"), *args],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return Running(process)

    def run(
        self, *args: str, env: dict[str, str] | None = None
    ) -> tuple[int, list[str]]:
        running = self.start(*args, env=env)
        return running.end(), running.lines


@pytest.fixture
def tree(tmp_path: Path) -> Tree:
    package = tmp_path / "package"
    for folder in ("bin", "scripts", "config", "build"):
        (package / folder).mkdir(parents=True)
    shutil.copy(WEB_ENTRY, package / "bin" / "deep-reasoning.mjs")
    (package / "scripts" / "dev-with-automation.mjs").write_text(STUB_LAUNCHER)
    (package / "package.json").write_text(
        json.dumps({"name": build.WEB_PACKAGE_NAME, "version": VERSION})
    )
    agent_server, automation = free_port(), free_port()
    ports = {"agentServer": agent_server, "automation": automation, "proxy": 8000}
    (package / "config" / "defaults.json").write_text(json.dumps({"ports": ports}))
    made = Tree(
        package,
        tmp_path / "tools",
        tmp_path / "home",
        agent_server,
        automation,
        free_port(),
    )
    made.tools.mkdir()
    made.home.mkdir()
    for name, script in TOOLS.items():
        made.tool(name, script)
    made.does(does="ready")
    return made


def test_the_launcher_gets_electrons_options_one_port_and_a_clean_environment(tree):
    terminal = {
        "OH_AGENT_SERVER_GIT_REF": "main",
        "VITE_POSTHOG_API_KEY": "phc_test",
        "PORT": "9000",
        "PYTHONPATH": "/nonexistent",
        "VIRTUAL_ENV": "/nonexistent-venv",
        "NODE_OPTIONS": "--max-old-space-size=512",
        "UV_CACHE_DIR": str(tree.home / "uv-cache"),
    }
    running = tree.start("--port", str(tree.ingress), "--no-open", env=terminal)
    url = f"http://localhost:{tree.ingress}"
    running.wait_for(web_text("running", url))
    running.process.send_signal(signal.SIGTERM)
    assert running.end() == 0
    record = tree.record()
    electrons = evaluate_web(
        f"Object.assign({{}}, {', '.join(f'({{{f}}})' for f in build.ELECTRON_CALL)})"
    )
    assert record["options"] == electrons | {"staticDir": str(tree.package / "build")}
    assert record["argv"] == ["--port", str(tree.ingress)]
    left_out = sorted(set(terminal) - {"UV_CACHE_DIR"})
    assert not set(left_out) & set(record["env"])
    assert record["env"]["UV_CACHE_DIR"] == terminal["UV_CACHE_DIR"]
    assert record["env"]["DO_NOT_TRACK"] == "1"
    assert running.lines[:2] == [
        web_text("ready_line", VERSION, "22.12.0", "0.8.17", "2.43.0"),
        web_text("left_out", left_out),
    ]


def test_a_held_agent_server_port_is_refused_and_nothing_starts(tree):
    with held(tree.agent_server):
        code, lines = tree.run("--port", str(tree.ingress), "--no-open")
    assert (code, lines[-1]) == (20, web_text("already_running", tree.agent_server))
    assert tree.record() is None


def test_a_held_ingress_port_is_refused_with_a_free_one_to_use(tree):
    with held(tree.ingress):
        code, lines = tree.run("--port", str(tree.ingress), "--no-open")
    suggested = int(lines[-1].rsplit("--port ", 1)[1].split()[0])
    assert (code, lines[-1]) == (21, web_text("port_taken", tree.ingress, suggested))
    assert tree.record() is None
    with held(suggested):
        pass


def test_a_held_automation_port_moves_to_a_free_one(tree):
    with held(tree.automation):
        running = tree.start("--port", str(tree.ingress), "--no-open")
        running.wait_for(web_text("running", f"http://localhost:{tree.ingress}"))
        running.process.send_signal(signal.SIGINT)
        assert running.end() == 0
    moved = int(tree.record()["env"]["OH_CANVAS_SAFE_AUTOMATION_PORT"])
    assert moved not in (tree.automation, tree.ingress, tree.agent_server)
    with held(moved):
        pass


@pytest.mark.parametrize(
    ("tool", "script", "problem"),
    [
        ("uv", "echo 'uv 0.8.16'", ("uv_too_old", "0.8.16")),
        ("uv", None, ("NO_UV",)),
        ("uvx", None, ("NO_UV",)),
        ("git", None, ("NO_GIT",)),
        ("git", "exit 1", ("NO_GIT",)),
    ],
    ids=["old-uv", "no-uv", "no-uvx", "no-git", "git-shim"],
)
def test_a_missing_or_old_requirement_is_named_and_nothing_starts(
    tree, tool, script, problem
):
    tree.tool(tool, script)
    code, lines = tree.run("--port", str(tree.ingress), "--no-open")
    assert (code, lines) == (22, [web_text(*problem)])
    assert tree.record() is None


def test_a_node_older_than_the_apps_is_named():
    """Only a door other than dr-web (npx) can run the entry on another Node."""
    found = {"node": "20.11.1", "uv": "0.8.17", "uvx": True, "git": "2.43.0"}
    problems = evaluate_web(f"web.requirementProblems({json.dumps(found)})")
    assert problems == [web_text("node_too_old", "20.11.1")]


@pytest.mark.parametrize(
    ("details", "code", "line"),
    [
        (
            {"phase": "before-start", "reason": "exit", "exitCode": 10},
            10,
            ("setup_stopped_before", 10),
        ),
        (
            {"phase": "after-ready", "reason": "exit", "exitCode": 12},
            12,
            ("setup_stopped_after", 12),
        ),
        (
            {"phase": "before-start", "reason": "timeout", "exitCode": None},
            24,
            ("SETUP_TIMED_OUT",),
        ),
        (
            {"phase": "before-start", "reason": "signal", "signal": "SIGKILL"},
            24,
            ("setup_killed", "SIGKILL"),
        ),
        (
            {"phase": "before-start", "reason": "exit", "exitCode": 1},
            24,
            ("setup_stopped_before", 1),
        ),
    ],
    ids=["before-start-10", "after-ready-12", "timeout", "killed", "exit-1"],
)
def test_a_failed_setup_ends_in_one_line(tree, details, code, line):
    message = "Setup command `sh -c <the whole bootstrap script>` failed."
    tree.does(does="throw", name="SetupCommandError", message=message, details=details)
    exited, lines = tree.run("--port", str(tree.ingress), "--no-open")
    assert (exited, lines[-1]) == (code, web_text(*line))
    assert not [line for line in lines if "bootstrap" in line]


@pytest.mark.parametrize(
    ("does", "code", "line"),
    [
        ("throw", 24, ("could_not_start", "agent-server exited with code 2")),
        ("beaten", 20, ("started_elsewhere",)),
    ],
    ids=["agent-server-exited", "started-elsewhere"],
)
def test_a_launch_that_fails_otherwise_says_why_in_one_line(tree, does, code, line):
    """The second of two starts passes the port check, then its agent-server cannot bind
    the port the first one bound meanwhile."""
    message = "agent-server exited with code 2\n  last lines: …"
    tree.does(does=does, name="Error", message=message, agentServer=tree.agent_server)
    exited, lines = tree.run("--port", str(tree.ingress), "--no-open")
    assert (exited, lines[-1]) == (code, web_text(*line))


def test_an_agent_server_that_never_answers_stops_everything_and_exits_24(tree):
    tree.does(does="not-ready")
    code, lines = tree.run("--port", str(tree.ingress), "--no-open")
    assert code == 24
    assert web_text("NOT_READY") in lines
    assert (tree.scripts / "stopped.json").exists()


def test_once_ready_it_says_where_and_ctrl_c_exits_0(tree):
    running = tree.start("--port", str(tree.ingress), "--no-open")
    running.wait_for(web_text("running", f"http://localhost:{tree.ingress}"))
    running.process.send_signal(signal.SIGINT)
    assert running.end() == 0
    assert running.lines[-1] == "Shutting down..."


@pytest.mark.parametrize(
    ("args", "what"),
    [
        (["--x"], "Unknown option --x"),
        (["serve"], "Unknown option serve"),
        (["--no-open=1"], "Unknown option --no-open"),
        (["--port", "0"], "--port needs a number from 1 to 65535"),
        (["--port", "65536"], "--port needs a number from 1 to 65535"),
        (["--port", "eighty"], "--port needs a number from 1 to 65535"),
        (["--port"], "--port needs a number from 1 to 65535"),
        (["--port", "AGENT_SERVER"], None),
    ],
)
def test_unknown_options_and_bad_ports_are_refused(tree, args, what):
    args = [str(tree.agent_server) if a == "AGENT_SERVER" else a for a in args]
    what = what or (
        f"--port cannot be {tree.agent_server}: Deep Reasoning's agent-server uses it"
    )
    assert tree.run(*args) == (2, [web_text("usage", what)])
    assert tree.record() is None


@pytest.mark.parametrize(
    ("platform", "env", "command"),
    [
        ("darwin", {}, "open"),
        ("linux", {"DISPLAY": ":0"}, "xdg-open"),
        ("linux", {"WAYLAND_DISPLAY": "wayland-0"}, "xdg-open"),
        ("linux", {}, None),
        ("darwin", {"SSH_CONNECTION": "10.0.0.1 52000 10.0.0.2 22"}, None),
        ("linux", {"DISPLAY": ":0", "SSH_TTY": "/dev/pts/1"}, None),
    ],
    ids=["mac", "x11", "wayland", "no-display", "ssh-mac", "ssh-x11"],
)
def test_the_browser_opens_only_where_a_session_can_show_it(platform, env, command):
    assert (
        evaluate_web(f"web.opener({json.dumps(platform)}, {json.dumps(env)})")
        == command
    )


@pytest.mark.parametrize(
    ("found", "minimum", "at_least"),
    [
        ("22.12.0", "22.12.0", True),
        ("v22.22.0", "22.12.0", True),
        ("0.8.17 (8c62bb3 2025-09-10)", "0.8.17", True),
        ("22.9.1", "22.12.0", False),
        ("20.11.1", "22.12.0", False),
        ("0.10.0", "0.8.17", True),
        ("no version", "0.8.17", False),
    ],
)
def test_versions_compare_by_their_three_numbers(found, minimum, at_least):
    expression = f"web.versionAtLeast({json.dumps(found)}, {json.dumps(minimum)})"
    assert evaluate_web(expression) is at_least


def test_the_entrys_sentences_are_the_designs_verbatim():
    assert web_text("ready_line", "1.0.0", "22.12.0", "0.8.17", "2.43.0") == (
        "Deep Reasoning 1.0.0 · Node 22.12.0 ✓ · uv 0.8.17 ✓ · git 2.43.0 ✓"
    )
    assert web_text("already_running", 18000) == (
        "✗ Deep Reasoning is already running on this computer: port 18000 is in use (the "
        "app, another terminal, or an Agent Canvas). Stop it, then run this again. "
        "Nothing was changed."
    )
    assert web_text("port_taken", 8000, 8765) == (
        "✗ Port 8000 is in use by another program. Start Deep Reasoning on another: add "
        "--port 8765 to the command."
    )
    assert web_text("node_too_old", "20.11.1") == (
        "✗ Deep Reasoning needs Node 22.12 or later, and this is 20.11.1. Install it from "
        "https://nodejs.org, then run the same command."
    )
    assert web_text("NO_UV") == (
        "✗ uv was not found on PATH. Install it with: curl -LsSf "
        "https://astral.sh/uv/install.sh | sh  then open a new terminal and run the same "
        "command."
    )
    assert web_text("setup_stopped_before", 10) == (
        "✗ Setup stopped before anything started (exit 10): its last line above says why."
    )
    assert web_text("running_opened", "http://localhost:8000") == (
        "Deep Reasoning is running at http://localhost:8000, opened in your browser. "
        "Ctrl+C stops it."
    )
    assert web_text("usage", "Unknown option --x") == (
        "✗ Unknown option --x. The options are --port N and --no-open."
    )
