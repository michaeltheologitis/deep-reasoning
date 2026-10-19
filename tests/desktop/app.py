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
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

from dr_app.agent_server import AgentServer

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
# A command run after these words has loopback and no other network (Ubuntu 24.04 needs
# kernel.apparmor_restrict_unprivileged_userns=0).
NETWORK_CUT: Final = [
    *("unshare", "--map-root-user", "-n", "sh", "-c"),
    'ip link set lo up && exec "$@"',
    "offline",
]
# Where uv keeps a cached index answer's fetch time: a u64 of Unix seconds near its end.
ANSWER_TAIL_BYTES = 512
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
# The runner's own per-user directories (GitHub's runners set XDG_CONFIG_HOME): without
# them the app's config, cache, data and state live under the fresh HOME, Electron's
# profile with its localStorage included, so one launch's settings never reach the next.
XDG_BASE_DIRECTORIES = (
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
)


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
    the runner's uv settings, its per-user directories or this test environment's bin
    directory on PATH."""
    dev_bin = str(Path(sys.executable).parent)
    path = os.pathsep.join(
        p for p in os.environ.get("PATH", "").split(os.pathsep) if p != dev_bin
    )
    dropped = (*RUNNER_ONLY, *XDG_BASE_DIRECTORIES)
    env = {k: v for k, v in os.environ.items() if k not in dropped}
    return env | {"HOME": str(home), "PATH": path}


@dataclass
class LaunchedApp:
    process: subprocess.Popen[bytes]
    home: Path
    log: Path
    debug_port: int
    started_at: float = field(default_factory=time.time)  # made right after the Popen

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
        """The agent-server's REST API with the app's session key, as setup calls it."""
        return AgentServer(AGENT_SERVER, self.session_key).request(method, path, body)

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


def launch(home: Path, log: Path, *, network: bool = True) -> LaunchedApp:
    """The installed app with HOME home, its output in log: with a DevTools port, or,
    with network=False, inside NETWORK_CUT, where the port would be out of reach."""
    port = free_port() if network else 0
    argv = (
        [str(APP), f"--remote-debugging-port={port}"]
        if network
        else [*NETWORK_CUT, str(APP)]
    )
    if os.geteuid() == 0 or not network:
        argv.append("--no-sandbox")  # Chromium refuses root, the cut's mapped one too
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


def get_with_host(url: str, host: str, timeout_s: float = 10.0) -> tuple[int, str]:
    """GET url with the Host header host, as a page served from that name sends it
    (urllib sends the header as given), past any proxy: its status and body, an error's
    included."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers={"Host": host})
    try:
        with opener.open(request, timeout=timeout_s) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")


def age_uv_index_answers(cache: Path, since: float, seconds: int) -> int:
    """Move every index answer under cache/simple-v* back by seconds, as if uv had
    fetched it then: each u64 in an answer's last 512 bytes between since and now. The
    number aged; AssertionError naming the answers in which it found no such time, since
    then this uv keeps them otherwise and nothing was aged."""
    answers = sorted(cache.glob("simple-v*/**/*.rkyv"))
    assert answers, f"no index answers under {cache}/simple-v*"
    now = time.time()
    unaged = []
    for answer in answers:
        data = bytearray(answer.read_bytes())
        offset, aged = max(0, len(data) - ANSWER_TAIL_BYTES), False
        while offset + 8 <= len(data):
            (value,) = struct.unpack_from("<Q", data, offset)
            if since <= value <= now:
                struct.pack_into("<Q", data, offset, value - seconds)
                offset, aged = offset + 8, True
            else:
                offset += 1
        if aged:
            answer.write_bytes(data)
        else:
            unaged.append(str(answer))
    assert not unaged, f"no fetch time since {since:.0f} in {unaged}"
    return len(answers)


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


def conversation_events(app: LaunchedApp, conversation_id: str) -> list[dict]:
    """Every event the agent-server stored for the conversation, oldest first."""
    events, page = [], None
    while True:
        query = f"limit=100&page_id={page}" if page else "limit=100"
        found = app.request(
            "GET", f"/api/conversations/{conversation_id}/events/search?{query}"
        )
        events += found["items"]
        page = found.get("next_page_id")
        if not page:
            return events


def spend_caps(app: LaunchedApp) -> dict[str, float]:
    """Each root session's cap, as the key proxy's ledger in spend/ records it."""
    return {
        path.stem: json.loads(path.read_text())["cap_usd"]
        for path in (app.data / "spend").glob("*.json")
    }
