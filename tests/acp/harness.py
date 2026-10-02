"""Drive a real dr-acp over stdio, and check every message it sends (E2, E4)."""

import asyncio
import contextlib
import hashlib
import json
import os
import sys
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import acp
import yaml
from acp.client.connection import ClientSideConnection
from acp.connection import StreamDirection, StreamEvent
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from deep_reasoning.acp.runlog import Home, RunLog
from deep_reasoning.acp.testing.client import Caps, Printer, ShimConnection

REPO = Path(__file__).resolve().parents[2]
DR_ACP = str(Path(sys.executable).parent / "dr-acp")
SCHEMA_PATH = Path(__file__).parent / "schema" / "acp-1.24.1.unstable.json"
SCHEMA_SHA256 = "6449a87a3b3c42aa0abd30033fc9bd3236cd785078ad084ce3675766be09109e"
LINE_LIMIT = 256 * 1024 * 1024
RESPONSE_TYPES = {
    "initialize": "InitializeResponse",
    "session/new": "NewSessionResponse",
    "session/load": "LoadSessionResponse",
    "session/set_config_option": "SetSessionConfigOptionResponse",
    "session/prompt": "PromptResponse",
    "session/close": "CloseSessionResponse",
}
FAKE_PRICES = {
    "fake-model": {
        "input_per_mtok": 1.0,
        "output_per_mtok": 2.0,
        "context_window": 1000,
        "source": "tests",
        "as_of": "2026-10-02",
    }
}


# What OpenHands' bridge appends to a user's text in a prompt, as it renders them:
# per-turn extensions (MessageEvent.extended_content: a skill's knowledge, the agent
# context's user_message_suffix, a hook's additional_context), then, on the first
# prompt only, its system suffix (_build_acp_prompt, acp_agent.py:3572-3590).
BRIDGE_EXTENSION = (
    "<EXTRA_INFO>\n"
    'The following information has been included based on a keyword match for "courses".\n'
    "It may or may not be relevant to the user's request.\n\n"
    "Course codes are four letters and three digits.\n"
    "</EXTRA_INFO>"
)
BRIDGE_USER_SUFFIX = "Answer in one sentence."
BRIDGE_SYSTEM_SUFFIX = (
    "<CUSTOM_SECRETS>\n"
    "### Credential Access\n"
    "* If it still fails, report it to the user.\n\n"
    "You have access to the following environment variables\n"
    "\n* **$OPENAI_API_KEY**\n\n"
    "</CUSTOM_SECRETS>"
)


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    """Tests are plain functions; each runs its body on a fresh event loop."""
    return asyncio.run(coro)


class SchemaCheck:
    """Validates what dr-acp sends against the vendored ACP schema 1.24.1 (unstable)."""

    def __init__(self) -> None:
        data = SCHEMA_PATH.read_bytes()
        assert hashlib.sha256(data).hexdigest() == SCHEMA_SHA256, (
            "vendored schema changed"
        )
        self._registry = Registry().with_resource(
            "acp", Resource.from_contents(json.loads(data))
        )
        self._validators: dict[str, Draft202012Validator] = {}

    def errors(self, definition: str, obj: Any) -> list[str]:
        if definition not in self._validators:
            self._validators[definition] = Draft202012Validator(
                {"$ref": f"acp#/$defs/{definition}"}, registry=self._registry
            )
        return [e.message for e in self._validators[definition].iter_errors(obj)]

    def message_errors(self, message: dict[str, Any], method: str | None) -> list[str]:
        """A message dr-acp sent: a session/update, or the response to `method`."""
        if message.get("jsonrpc") != "2.0":
            return ["not JSON-RPC 2.0"]
        if message.get("method") == "session/update":
            return self.errors("SessionNotification", message.get("params"))
        if "method" in message:
            return [
                f"dr-acp sent an unexpected request or notification {message['method']}"
            ]
        if "error" in message:
            return self.errors("Error", message["error"])
        return self.errors(RESPONSE_TYPES[method], message.get("result"))


SCHEMA = SchemaCheck()


@dataclass
class DrAcp:
    """One dr-acp process and one client connection to it."""

    conn: ClientSideConnection
    printer: Printer
    proc: asyncio.subprocess.Process
    home: Path
    stderr: Path
    lines: list[bytes] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    _methods: dict[Any, str] = field(default_factory=dict)

    def observe(self, event: StreamEvent) -> None:
        message = event.message
        if event.direction is StreamDirection.OUTGOING:
            if "id" in message and "method" in message:
                self._methods[message["id"]] = message["method"]
            return
        method = (
            self._methods.get(message.get("id")) if "method" not in message else None
        )
        for error in SCHEMA.message_errors(message, method):
            self.violations.append(f"{json.dumps(message)[:300]}: {error}")

    async def open_session(self, cwd: Path) -> str:
        """session/new, then the menu that follows its response (§5.4 rule 5)."""
        response = await self.conn.new_session(cwd=str(cwd), mcp_servers=[])
        await self.printer.wait_until(
            lambda p: response.session_id in p.commands, timeout=30
        )
        return response.session_id

    async def ask(self, session_id: str, text: str) -> acp.schema.PromptResponse:
        return await self.conn.prompt(
            session_id=session_id, prompt=[acp.text_block(text)]
        )

    def run_log(self, run: str) -> list[Any]:
        return list(RunLog.read(Home(self.home), run))

    def updates_on(self, session_id: str) -> list[dict[str, Any]]:
        return [u for sid, u in self.printer.updates if sid == session_id]

    def stderr_text(self) -> str:
        return self.stderr.read_text(errors="replace")


def scripted_env(**extra: str) -> dict[str, str]:
    """dr-acp's environment: this one, with the repo importable (the fake of Dean's stop)
    and no real model key."""
    env = {
        k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "DR_HOME")
    }
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(REPO), env.get("PYTHONPATH")])
    )
    env.update(extra)
    return env


def write_prices(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / "prices.yaml").write_text(yaml.safe_dump(FAKE_PRICES))


@contextlib.asynccontextmanager
async def dr_acp(
    config: Path | None,
    home: Path,
    *,
    native: bool = True,
    args: tuple[str, ...] = (),
    env: dict[str, str] | None = None,
    command: tuple[str, ...] | None = None,
    initialize: bool = True,
) -> AsyncIterator[DrAcp]:
    """Spawn dr-acp (on the Library at home when config is None), connect, initialize;
    on exit close stdin and check what was sent."""
    write_prices(home)
    stderr = home / f"dr-acp-{len(list(home.glob('dr-acp-*.log')))}.log"
    argv = command or (DR_ACP,)
    with stderr.open("wb") as err:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            *(("--config", str(config)) if config is not None else ()),
            "--home",
            str(home),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=err,
            env=env or scripted_env(),
            limit=LINE_LIMIT,
        )
    feed = asyncio.StreamReader(limit=LINE_LIMIT)
    printer = Printer()
    conn = (ShimConnection if native else ClientSideConnection)(
        printer, proc.stdin, feed
    )
    client = DrAcp(conn=conn, printer=printer, proc=proc, home=home, stderr=stderr)
    conn._conn.add_observer(client.observe)

    async def tee() -> None:
        while line := await proc.stdout.readline():
            client.lines.append(line)
            feed.feed_data(line)
        feed.feed_eof()

    tee_task = asyncio.create_task(tee())
    try:
        if initialize:
            caps = Caps(subagents={}) if native else None
            await conn.initialize(protocol_version=1, client_capabilities=caps)
        yield client
    finally:
        await close_stdin(proc)
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(proc.wait(), 10)
        if proc.returncode is None:
            proc.kill()
            await proc.wait()
        await tee_task
        await conn.close()
    assert client.violations == [], client.violations[:5]
    assert_json_rpc_lines(client.lines)


async def close_stdin(proc: asyncio.subprocess.Process) -> None:
    with contextlib.suppress(OSError, RuntimeError):
        proc.stdin.write_eof()
    with contextlib.suppress(OSError, RuntimeError, ConnectionError):
        await proc.stdin.drain()
    proc.stdin.close()


def assert_json_rpc_lines(lines: list[bytes]) -> None:
    """Every line dr-acp wrote to its stdout is a JSON-RPC 2.0 message (E2)."""
    for line in lines:
        message = json.loads(line)
        assert message.get("jsonrpc") == "2.0", line[:200]


async def eventually(predicate: Callable[[], Any], timeout: float = 30) -> Any:
    """Poll predicate until it returns something truthy."""
    async with asyncio.timeout(timeout):
        while not (value := predicate()):
            await asyncio.sleep(0.02)
    return value


def run_ids(updates: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Every run id the updates mention, in order of first appearance."""
    seen: list[str] = []
    for _, update in updates:
        run = (update.get("_meta") or {}).get("deep_reasoner", {}).get("run")
        if run and run not in seen:
            seen.append(run)
    return seen


def write_config(path: Path, config: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    return path
