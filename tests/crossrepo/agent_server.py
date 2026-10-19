"""An agent-server from the SDK fork's pinned commit, started directly: no Canvas, no
launcher, no wiring (D5 §1.2 step 5).

DR_SDK_CHECKOUT names a checkout of desktop/pins.toml's [sdk_fork] commit, synced with
uv sync --frozen; DR_SDK_COMMIT, when set, names the commit it holds instead of the pin.
"""

import os
import secrets
import signal
import socket
import subprocess
import sys
import time
import tomllib
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from dr_app.agent_server import AgentServer, AgentServerError
from dr_app.profile import PROFILE_NAME, desired_profile

ROOT = Path(__file__).resolve().parents[2]
SDK_PIN = tomllib.loads((ROOT / "desktop" / "pins.toml").read_text())["sdk_fork"]
CHECKOUT_ENV = "DR_SDK_CHECKOUT"
COMMIT_ENV = "DR_SDK_COMMIT"
STARTUP_S = 60.0
# Loopback, so never through a proxy.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


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

    def open_conversation(self, home: Path, work: Path) -> str:
        """A conversation in work on the deep_reasoner profile setup writes, for this
        environment's dr-acp with home as its DR home."""
        dr_acp = Path(sys.executable).parent / "dr-acp"
        profile = desired_profile(None, dr_acp=dr_acp, home=home)
        self.request("POST", f"/api/agent-profiles/{PROFILE_NAME}", profile)
        saved = self.request("GET", f"/api/agent-profiles/{PROFILE_NAME}")["profile"]
        return self.request(
            "POST",
            "/api/conversations",
            {
                "agent_profile_id": saved["id"],
                "workspace": {"kind": "LocalWorkspace", "working_dir": str(work)},
            },
        )["id"]

    def post(self, conversation: str, text: str) -> None:
        """One user message, run; returns at once."""
        self.request(
            "POST",
            f"/api/conversations/{conversation}/events",
            {"role": "user", "content": [{"type": "text", "text": text}], "run": True},
        )

    def wait(
        self, conversation: str, statuses: tuple[str, ...], deadline: float
    ) -> str:
        """The conversation's execution_status, once it is one of statuses, by deadline
        (time.monotonic())."""
        while (
            status := self.request("GET", f"/api/conversations/{conversation}")[
                "execution_status"
            ]
        ) not in statuses:
            assert time.monotonic() < deadline, f"still {status}"
            time.sleep(0.1)
        return status

    def ask(self, conversation: str, text: str, deadline: float) -> None:
        """One user message, run; returns once the conversation has finished, by
        deadline (time.monotonic())."""
        self.post(conversation, text)
        time.sleep(0.2)
        status = self.wait(conversation, ("finished", "error", "stuck"), deadline)
        assert status == "finished", status


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def agent_server(checkout: Path, root: Path) -> Iterator[RunningAgentServer]:
    """python -m openhands.agent_server from the checkout's environment, with its
    persistence root, working directory and HOME under root; stopped on exit."""
    root.mkdir(parents=True, exist_ok=True)
    port, key = free_port(), f"session-{secrets.token_hex(16)}"
    env = {
        **os.environ,
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
