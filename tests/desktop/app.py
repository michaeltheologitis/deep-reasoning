"""The installed desktop app, launched as a user would launch it, with a fresh HOME, and
driven over the agent-server's REST API and Electron's DevTools port (D5 §7.5, §7.6).

DR_APP_EXECUTABLE names the installed executable; the default is where the .deb puts it.
"""

import json
import os
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

APP = Path(os.environ.get("DR_APP_EXECUTABLE", "/opt/Deep Reasoning/deep-reasoning"))
CANVAS_URL = "http://localhost:8000/"
AGENT_SERVER = "http://127.0.0.1:18000"
# A first launch installs Python, the runtime and the agent-server: C3 allows 15 minutes
# per setup phase, and the agent-server's own install comes between the two.
FIRST_LAUNCH_S = 25 * 60
QUIT_S = 6.0  # C3 v3 §4.4: the launcher in about 4 s, inside Electron's 6 s net
ANSI = re.compile(r"\x1b\[[0-9;]*m")
# The packaged app stays open on its failure screen after this line (Canvas's
# electron/main.mjs), so a wait for anything later can end there.
STARTUP_FAILED = "[desktop] Startup failed"
LOG_TAIL_LINES = 40  # of the app's log, in a failed wait's message
# An empty helper resets git's list of credential helpers, the system's included.
NO_CREDENTIAL_HELPER = "\n[credential]\n\thelper =\n"
# The test runner's own uv and venv settings, which a user's environment does not hold.
RUNNER_ONLY = (
    "VIRTUAL_ENV",
    "PYTHONPATH",
    "UV_CACHE_DIR",
    "UV_PYTHON",
    "UV_PYTHON_INSTALL_DIR",
    "UV_TOOL_DIR",
    "UV_TOOL_BIN_DIR",
    "UV_PROJECT_ENVIRONMENT",
)
# Loopback, so never through a proxy.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@contextmanager
def fresh_home() -> Iterator[Path]:
    """An empty HOME, short enough for deep_reasoner's Claude sockets, holding the
    runner's git config: the insteadOf line that lets setup read the private
    deep_reasoner_beta, as a user's own credentials would. Its git keeps no credentials:
    a system helper (the macOS runner's osxkeychain) has no keychain under this
    HOME, and its store waits on a dialog no one answers."""
    with tempfile.TemporaryDirectory(prefix="e12-", dir="/tmp") as short:
        home = Path(short) / "home"
        home.mkdir()
        gitconfig = Path.home() / ".gitconfig"
        if gitconfig.exists():
            shutil.copy(gitconfig, home / ".gitconfig")
        with (home / ".gitconfig").open("a") as config:
            config.write(NO_CREDENTIAL_HELPER)
        yield home


def user_environment(home: Path) -> dict[str, str]:
    """This process's environment as a user's would be: HOME the fresh one, and without
    the runner's uv settings or this test environment's bin directory on PATH."""
    dev_bin = str(Path(sys.executable).parent)
    path = os.pathsep.join(
        p for p in os.environ.get("PATH", "").split(os.pathsep) if p != dev_bin
    )
    env = {k: v for k, v in os.environ.items() if k not in RUNNER_ONLY}
    return env | {"HOME": str(home), "PATH": path}


@dataclass
class LaunchedApp:
    process: subprocess.Popen[bytes]
    home: Path
    log: Path
    debug_port: int

    @property
    def data(self) -> Path:
        """~/.deep-reasoning, the app's root and (on a local home) DR_HOME."""
        return self.home / ".deep-reasoning"

    @property
    def runtime_bin(self) -> Path:
        return self.data / "runtime" / "current" / "bin"

    @property
    def session_key(self) -> str:
        return (
            (self.data / "canvas" / "agent-canvas" / "api-key.txt").read_text().strip()
        )

    @property
    def secret_key(self) -> str:
        return (
            (self.data / "canvas" / "agent-canvas" / "secret-key.txt")
            .read_text()
            .strip()
        )

    def lines(self) -> list[str]:
        """The launcher's log so far, without its colours."""
        text = self.log.read_bytes().decode(errors="replace")
        return [ANSI.sub("", line) for line in text.splitlines()]

    def wait_for_line(self, fragment: str, timeout_s: float) -> str:
        """The first log line holding fragment; fails, with the log's last lines, if
        the app exits or reports its launch failed first."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            lines = self.lines()
            for line in lines:
                if fragment in line:
                    return line
            if self.process.poll() is not None:
                self.fail(f"the app exited {self.process.returncode}")
            if any(STARTUP_FAILED in line for line in lines):
                self.fail("the app reported its launch failed")
            time.sleep(1.0)
        self.fail(f"no {fragment!r} in the app's log in {timeout_s} s")

    def fail(self, why: str) -> NoReturn:
        tail = "\n".join(self.lines()[-LOG_TAIL_LINES:])
        raise AssertionError(f"{why}; the end of {self.log}:\n{tail}")

    def request(self, method: str, path: str, body: Any = None) -> Any:
        """The agent-server's REST API with the app's session key; non-2xx raises."""
        request = urllib.request.Request(
            AGENT_SERVER + path,
            data=None if body is None else json.dumps(body).encode(),
            method=method,
            headers={
                "X-Session-API-Key": self.session_key,
                "Content-Type": "application/json",
            },
        )
        with OPENER.open(request, timeout=60) as response:
            raw = response.read()
        return json.loads(raw) if raw else None

    def stop(self) -> None:
        """SIGTERM, the signal the app's own quit sends itself; its handler stops every
        service it started."""
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


def launch(home: Path, log: Path) -> LaunchedApp:
    """The installed app with HOME home and a DevTools port, its output in log."""
    port = free_port()
    argv = [str(APP), f"--remote-debugging-port={port}"]
    if os.geteuid() == 0:
        argv.append("--no-sandbox")  # Chromium refuses root without it
    with log.open("wb") as out:
        process = subprocess.Popen(
            argv,
            env=user_environment(home),
            cwd=home,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
        )
    return LaunchedApp(process, home, log, port)


def processes_mentioning(text: str) -> list[str]:
    """The command lines of live processes that hold text (Linux: /proc)."""
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        except OSError:
            continue
        if text in argv:
            found.append(f"{entry.name}: {argv}")
    return found


def secret(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(16)}"
