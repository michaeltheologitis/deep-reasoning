"""An agent-server from the SDK fork's pinned commit, started directly: no Canvas, no
launcher, no wiring (D5 §1.2 step 5).

DR_SDK_CHECKOUT names a checkout of desktop/pins.toml's [sdk_fork] commit, synced with
uv sync --frozen; DR_SDK_COMMIT, when set, names the commit it holds instead of the pin.
"""

import os
import secrets
import signal
import socket
import socketserver
import subprocess
import threading
import time
import tomllib
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from dr_app.agent_server import AgentServer, AgentServerError

ROOT = Path(__file__).resolve().parents[2]
SDK_PIN = tomllib.loads((ROOT / "desktop" / "pins.toml").read_text())["sdk_fork"]
CHECKOUT_ENV = "DR_SDK_CHECKOUT"
COMMIT_ENV = "DR_SDK_COMMIT"
STARTUP_S = 60.0
# Loopback, so never through a proxy.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
PROXY_VARIABLES = ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy")
LOOPBACK = {"NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"}
# LiteLLM's bundled price map, instead of the one it fetches from GitHub at start-up.
LOCAL_COST_MAP = {"LITELLM_LOCAL_MODEL_COST_MAP": "True"}
REFUSED = b"HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\nconnection: close\r\n\r\n"


def sdk_checkout() -> Path:
    """The checkout DR_SDK_CHECKOUT names, at the pinned commit (or DR_SDK_COMMIT's) when
    it is a git checkout; the test is skipped without one."""
    named = os.environ.get(CHECKOUT_ENV)
    if not named:
        pytest.skip(f"{CHECKOUT_ENV} names no checkout of the SDK fork at its pin")
    checkout = Path(named)
    if (checkout / ".git").exists():
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=checkout,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        expected = os.environ.get(COMMIT_ENV) or SDK_PIN["commit"]
        assert head == expected, f"{checkout} is at {head}, not {expected}"
    return checkout


class RunningAgentServer(AgentServer):
    """The agent-server's REST API, as setup calls it, and the checkout it runs from."""

    def __init__(self, url: str, session_key: str, checkout: Path) -> None:
        super().__init__(url, session_key)
        self.checkout = checkout
        self.python = str(checkout / ".venv" / "bin" / "python")

    def ask(self, conversation: str, text: str, deadline: float) -> None:
        """One user message, run; returns once the conversation has finished, by
        deadline (time.monotonic())."""
        self.request(
            "POST",
            f"/api/conversations/{conversation}/events",
            {"role": "user", "content": [{"type": "text", "text": text}], "run": True},
        )
        time.sleep(0.2)
        while (
            status := self.request("GET", f"/api/conversations/{conversation}")[
                "execution_status"
            ]
        ) not in ("finished", "error", "stuck"):
            assert time.monotonic() < deadline, f"still {status}"
            time.sleep(0.1)
        assert status == "finished", status


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@dataclass
class RecordingProxy:
    url: str
    attempts: list[str] = field(default_factory=list)


@contextmanager
def recording_proxy() -> Iterator[RecordingProxy]:
    """A loopback HTTP proxy that records each request line's target
    (api.openai.com:443 for a CONNECT), answers 403 and forwards nothing."""
    recorded: list[str] = []

    class Recorder(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            line = self.rfile.readline().decode(errors="replace").split()
            if len(line) > 1:
                recorded.append(line[1])
            self.wfile.write(REFUSED)

    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Recorder)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield RecordingProxy(f"http://127.0.0.1:{server.server_address[1]}", recorded)
    finally:
        server.shutdown()
        server.server_close()


def outbound_through(proxy: str, env: dict[str, str]) -> dict[str, str]:
    """env with every proxy variable set to proxy, loopback exempt, no *_API_KEY, and
    nothing fetched at start-up."""
    kept = {k: v for k, v in env.items() if not k.endswith("_API_KEY")}
    return kept | dict.fromkeys(PROXY_VARIABLES, proxy) | LOOPBACK | LOCAL_COST_MAP


@contextmanager
def agent_server(
    checkout: Path, root: Path, *, outbound_proxy: str | None = None
) -> Iterator[RunningAgentServer]:
    """python -m openhands.agent_server from the checkout's environment, with its
    persistence root, working directory and HOME under root; stopped on exit. With
    outbound_proxy, every outbound connection goes through it and no model key is
    inherited."""
    root.mkdir(parents=True, exist_ok=True)
    port, key = free_port(), f"session-{secrets.token_hex(16)}"
    inherited = dict(os.environ)
    if outbound_proxy is not None:
        inherited = outbound_through(outbound_proxy, inherited)
    env = {
        **inherited,
        "HOME": str(root),
        "OH_PERSISTENCE_DIR": str(root / "canvas"),
        "OH_SESSION_API_KEYS_0": key,
        "OH_APP_BACKEND_PUBLIC_URL": f"http://127.0.0.1:{port}",
    }
    log = (root / "agent-server.log").open("wb")
    process = subprocess.Popen(
        [
            str(checkout / ".venv" / "bin" / "python"),
            "-m",
            "openhands.agent_server",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    server = RunningAgentServer(f"http://127.0.0.1:{port}", key, checkout)
    try:
        deadline = time.monotonic() + STARTUP_S
        while True:
            try:
                server.request("GET", "/server_info")
                break
            except AgentServerError:
                assert process.poll() is None, (root / "agent-server.log").read_text()
                assert time.monotonic() < deadline, "the agent-server did not answer"
                time.sleep(0.2)
        yield server
    finally:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        log.close()


def conversation_events(server, conversation: str) -> list[dict[str, Any]]:
    """Every event the agent-server stored for the conversation, oldest first, asked
    through server.request(method, path)."""
    events: list[dict[str, Any]] = []
    page = None
    while True:
        query = "?limit=100" + (f"&page_id={page}" if page else "")
        found = server.request(
            "GET", f"/api/conversations/{conversation}/events/search{query}"
        )
        events += found["items"]
        page = found.get("next_page_id")
        if not page:
            return events
