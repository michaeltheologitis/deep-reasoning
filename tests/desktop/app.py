"""The installed desktop app, and the browser command, launched as a user would launch
them, with a fresh HOME, and driven over the agent-server's REST API, Electron's DevTools
port or Playwright's own browsers (D5 §7.5, §7.6; TASK-48 §7.6).

DR_APP_EXECUTABLE names the installed executable; the default is where the .deb puts it.
"""

import hashlib
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
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, NoReturn

import nodejs_wheel
import yaml
from playwright.sync_api import BrowserContext, FrameLocator, Locator, Page, expect

from dr_app.agent_server import AgentServer
from dr_web.cli import command_for
from tests.acp.scenarios import repl

APP = Path(os.environ.get("DR_APP_EXECUTABLE", "/opt/Deep Reasoning/deep-reasoning"))
CANVAS_URL = "http://localhost:8000/"
AGENT_SERVER_PORT = 18000
AGENT_SERVER = f"http://127.0.0.1:{AGENT_SERVER_PORT}"
# A first launch installs Python, the runtime and the agent-server: C3 allows 15 minutes
# per setup phase, and the agent-server's own install comes between the two.
FIRST_LAUNCH_S = 25 * 60
QUIT_S = 6.0  # C3 v3 §4.4: the launcher in about 4 s, inside Electron's 6 s net
ANSI = re.compile(r"\x1b\[[0-9;]*m")
# The packaged app stays open on its failure screen after this line (Canvas's
# electron/main.mjs), so a wait for anything later can end there.
STARTUP_FAILED = "[desktop] Startup failed"
# The browser command's own last line when it fails (the launcher echoes setup's script,
# which holds the same mark mid-line).
WEB_FAILED = re.compile(r"^✗ ")
REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_ENTRY = REPO_ROOT / "desktop" / "web.mjs"
# The Node dr-web installs, as the dev group installs it.
NODE = Path(nodejs_wheel.__file__).parent / "bin" / "node"
SESSION = f"{AGENT_SERVER}/app-backends/dr-library/session"
LIBRARY_APP_VERSION = json.loads(
    (
        REPO_ROOT / "src" / "deep_reasoning" / "canvas_app" / "canvas-extension.json"
    ).read_text()
)["version"]
ONBOARDED_STORAGE_KEY = "openhands-onboarded"  # Canvas's use-onboarding-completion.ts
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
    # A line it matches ends a wait at once: the launch failed.
    failed: re.Pattern[str] = re.compile(re.escape(STARTUP_FAILED))
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
            if any(self.failed.search(line) for line in lines):
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


def evaluate_web(expression: str) -> Any:
    """expression, with desktop/web.mjs imported as web, evaluated by dr-web's Node."""
    script = (
        f"import * as web from {json.dumps(WEB_ENTRY.as_uri())};\n"
        f"console.log(JSON.stringify(await ({expression})));"
    )
    done = subprocess.run(
        [str(NODE), "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)


def web_text(name: str, *args: Any) -> str:
    """One of desktop/web.mjs's sentences, with its fields."""
    call = f"({', '.join(map(json.dumps, args))})" if args else ""
    return evaluate_web(f"web.texts.{name}{call}")


def web_command(commit: str, tarball: Path | None, *args: str) -> list[str]:
    """The README's browser command at commit, on a tarball build.py web made (or the
    release's, when tarball is None)."""
    command = command_for(commit).split()
    return [*command, *(("--tarball", str(tarball)) if tarball else ()), *args]


def launch_web(
    home: Path,
    log: Path,
    command: Sequence[str],
    *,
    env: dict[str, str] | None = None,
) -> LaunchedApp:
    """The browser command with HOME home, in a session of its own (a terminal's process
    group, for its Ctrl+C), its output in log."""
    with log.open("ab") as out:
        process = subprocess.Popen(
            list(command),
            env=env or user_environment(home),
            cwd=home,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return LaunchedApp(process, home, log, 0, failed=WEB_FAILED)


def interrupt(app: LaunchedApp) -> None:
    """Ctrl+C in the terminal: SIGINT to the command's process group."""
    os.killpg(app.process.pid, signal.SIGINT)


def parents() -> dict[int, int]:
    """Every live process's parent (Linux: /proc)."""
    found = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                stat = (entry / "stat").read_text()
            except OSError:
                continue
            found[int(entry.name)] = int(stat.rsplit(")", 1)[1].split()[1])
    return found


def descendants(pid: int) -> list[int]:
    """pid's children, their children and so on (Linux: /proc)."""
    of = parents()
    found: list[int] = []
    pending = [pid]
    while pending:
        parent = pending.pop()
        children = [child for child, its in of.items() if its == parent]
        found += children
        pending += children
    return found


def _socket_inodes(pid: int) -> set[str]:
    inodes = set()
    try:
        for fd in Path(f"/proc/{pid}/fd").iterdir():
            target = os.readlink(fd)
            if target.startswith("socket:["):
                inodes.add(target[len("socket:[") : -1])
    except OSError:
        pass
    return inodes


def _address(hex_address: str) -> str:
    """/proc/net/tcp's 0100007F:1F40, or tcp6's 32 hex digits, as 127.0.0.1:8000."""
    host, port = hex_address.split(":")
    raw = bytes.fromhex(host)
    words = b"".join(raw[i : i + 4][::-1] for i in range(0, len(raw), 4))
    family = socket.AF_INET if len(raw) == 4 else socket.AF_INET6
    return f"{socket.inet_ntop(family, words)}:{int(port, 16)}"


def listening_sockets(pids: Iterable[int]) -> dict[str, int]:
    """Each listening TCP socket the pids hold, as 'address:port', with the pid
    holding it (Linux: /proc/<pid>/fd and /proc/net/tcp, tcp6)."""
    owner = {inode: pid for pid in pids for inode in _socket_inodes(pid)}
    found = {}
    for table in ("tcp", "tcp6"):
        for line in Path(f"/proc/net/{table}").read_text().splitlines()[1:]:
            fields = line.split()
            local, state, inode = fields[1], fields[3], fields[9]
            if state == "0A" and inode in owner:  # TCP_LISTEN
                found[_address(local)] = owner[inode]
    return found


def _proc(pid: int, name: str) -> bytes:
    """/proc/<pid>/<name>; empty for a process that has gone meanwhile."""
    try:
        return Path(f"/proc/{pid}/{name}").read_bytes()
    except OSError:
        return b""


def environ(pid: int) -> dict[str, str]:
    """A process's environment as it started (Linux: /proc/<pid>/environ)."""
    raw = _proc(pid, "environ").decode(errors="replace")
    return dict(item.split("=", 1) for item in raw.split("\0") if "=" in item)


def cmdline(pid: int) -> str:
    return _proc(pid, "cmdline").replace(b"\0", b" ").decode(errors="replace")


def executable(pid: int) -> Path | None:
    """The file a process runs (Linux: /proc/<pid>/exe); None once it has gone."""
    try:
        return Path(os.readlink(f"/proc/{pid}/exe"))
    except OSError:
        return None


def snapshot(data: Path) -> dict[str, str]:
    """What a refused second start must not change under ~/.deep-reasoning: setup.json,
    runtime/'s entries and current's target, bin/, canvas-app/, and Canvas's settings,
    secrets and agent profiles. The rest of canvas/ is the running agent-server's."""
    kept: dict[str, str] = {}
    for path in sorted(data.rglob("*")):
        relative = path.relative_to(data).as_posix()
        top = relative.split("/", 1)[0]
        canvas_kept = relative in ("canvas/settings.json", "canvas/secrets.json") or (
            relative.startswith("canvas/agent-profiles")
        )
        if path.is_symlink():
            kept[relative] = f"-> {os.readlink(path)}"
        elif top == "runtime" and relative.count("/") == 1:
            kept[relative] = "dir" if path.is_dir() else "file"
        elif path.is_file() and (
            relative == "setup.json" or top in ("bin", "canvas-app") or canvas_kept
        ):
            kept[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return kept


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


def mark_onboarded(context: BrowserContext) -> None:
    """Canvas's onboarding done in this browser, as the user's first visit leaves it."""
    context.add_init_script(
        f"window.localStorage.setItem({json.dumps(ONBOARDED_STORAGE_KEY)}, '1')"
    )


def setup_lines(app: LaunchedApp, phase: str) -> list[str]:
    """What the setup command printed in a phase, without the launcher's prefixes."""
    marker = f"[setup {phase}] "
    return [line.split(marker, 1)[1] for line in app.lines() if marker in line]


def point_the_library_at(
    app: LaunchedApp,
    base_url: str,
    directory: Path,
    *,
    key: str,
    model: str,
    namespace: str,
    decomposition: dict,
) -> None:
    """The model key as a Canvas secret, and a Library whose run settings call the fake
    model at base_url, with its model priced for the spend cap, and namespace holding
    decomposition (an example())."""
    app.request(
        "PUT", "/api/settings/secrets", {"name": "OPENAI_API_KEY", "value": key}
    )
    config = directory / "main.yaml"
    client = {"base_url": base_url, "api_key_env": "OPENAI_API_KEY"}
    config.write_text(
        yaml.safe_dump(
            {
                "model": model,
                "client": client | {"max_retries": 0},
                "system_prompt": "You are a scripted test agent.",
                "max_iter": 6,
                "max_depth": 3,
                "entry_namespace": "root",
                "namespaces": {
                    "root": {},
                    namespace: {"decompositions": [decomposition]},
                },
            },
            sort_keys=False,
        )
    )
    price = {"input_per_mtok": 1.0, "output_per_mtok": 2.0, "context_window": 200000}
    (app.data / "prices.yaml").write_text(yaml.safe_dump({model: price}))
    subprocess.run(
        [app.runtime_bin / "dr-library", "import", config, "--home", app.data],
        env=user_environment(app.home),
        check=True,
        capture_output=True,
    )


def example(name: str, task: str) -> dict:
    """A decomposition: the task, then a turn that answers it."""
    return {
        "name": name,
        "messages": [
            {"role": "user", "content": task},
            {"role": "assistant", "content": repl("FinalAnswer('done')")},
        ],
    }


def run_ids(app: LaunchedApp) -> set[str]:
    return {path.parent.name for path in (app.data / "runs").glob("*/events.jsonl")}


def worker_environ(app: LaunchedApp, run_id: str | None = None) -> str:
    """The run's worker's environment, by the pid its run log records; the only run's
    when run_id is None."""
    if run_id is None:
        [run_id] = run_ids(app)
    events = app.data / "runs" / run_id / "events.jsonl"
    for line in events.read_text().splitlines():
        event = json.loads(line)
        if event["kind"] == "worker.ready":
            return Path(f"/proc/{event['pid']}/environ").read_bytes().decode()
    raise AssertionError("no worker.ready in the run log")


def eventually(check: Callable[[], bool], timeout_s: float = 60.0) -> None:
    """check() until it holds, or fail at timeout_s."""
    deadline = time.monotonic() + timeout_s
    while not check():
        assert time.monotonic() < deadline, f"not within {timeout_s} s"
        time.sleep(0.5)


def answer(page: Page, text: str) -> Locator:
    return page.get_by_test_id("agent-message").filter(has_text=text)


def pick_namespace(page: Page, namespace: str) -> None:
    """C2's option picker on the home screen: dr-acp's namespace option, picked and
    accepted by the agent's preview (the pill is disabled while one is pending)."""
    pill = page.get_by_test_id("agent-option-namespace")
    expect(pill).to_be_enabled()
    pill.click()
    page.get_by_test_id(f"agent-option-namespace-value-{namespace}").click()
    eventually(
        lambda: pill.is_enabled() and pill.get_attribute("data-value") == namespace
    )


def start_conversation(page: Page, text: str, namespace: str | None = None) -> str:
    """From the home screen, in namespace when one is named; the conversation's id."""
    page.goto(CANVAS_URL)
    if namespace is not None:
        pick_namespace(page, namespace)
    page.get_by_test_id("chat-input").fill(text)
    page.get_by_test_id("submit-button").click()
    page.wait_for_url(re.compile(r".*/conversations/[^/?]+$"))
    return page.url.rsplit("/", 1)[-1]


def library_frame(page: Page, session_key: str) -> tuple[FrameLocator, str | None]:
    """D3's panel in a frame over the page, through the bridge as C2's header panel opens
    it: a session made with credentials from the page, then the frame on its ingress URL.
    The frame once it shows the panel, and the text of the safety notice it cleared there,
    if one showed."""
    made = page.evaluate(
        """async ([url, key]) => {
            const r = await fetch(url, {method: "POST", credentials: "include",
                                        headers: {"X-Session-API-Key": key}});
            return {status: r.status, body: await r.json()};
        }""",
        [SESSION, session_key],
    )
    assert made["status"] == 200, made
    page.evaluate(
        """(src) => {
            const frame = document.createElement("iframe");
            frame.id = "dr-library-frame";
            frame.src = src;
            frame.style = "position:fixed;inset:0;width:100%;height:100%;z-index:99999";
            document.body.appendChild(frame);
        }""",
        made["body"]["ingress_url"] + "ui/?tab=namespaces&cap=5",
    )
    frame = page.frame_locator("#dr-library-frame")
    notice = frame.get_by_test_id("dr-notice")
    try:
        expect(
            frame.get_by_test_id("dr-notice-ack").or_(frame.locator("main")).first
        ).to_be_visible()
    except AssertionError as missing:
        shown = [(f.url, f.content()[:400]) for f in page.frames[1:]]
        raise AssertionError(f"the frame shows no panel: {shown}") from missing
    if not frame.get_by_test_id("dr-notice-ack").is_visible():
        return frame, None
    cleared = notice.inner_text()
    frame.get_by_test_id("dr-notice-ack").click()
    return frame, cleared


def processes_mentioning(text: str) -> list[str]:
    """The command lines of live processes that hold text (Linux: /proc; macOS: ps)."""
    if sys.platform == "darwin":
        listed = subprocess.run(
            ["ps", "-axww", "-o", "pid=,command="],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [line.strip() for line in listed.splitlines() if text in line]
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
