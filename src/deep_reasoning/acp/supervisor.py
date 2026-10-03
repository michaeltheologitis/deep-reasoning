"""A live run: the worker process, its two pipes, the pump (§4.2, §6.4)."""

import asyncio
import contextlib
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import structlog
from pydantic import BaseModel, ValidationError

from deep_reasoning.acp.catalog import RunSource
from deep_reasoning.acp.encoder import ChildRef, Encoder
from deep_reasoning.acp.route import ModelRoute, worker_env
from deep_reasoning.acp.runlog import (
    RUN_EVENT,
    Home,
    McpStatus,
    Mode,
    PromptEnd,
    PromptStart,
    RunEnd,
    RunEndReason,
    RunEvent,
    RunLog,
    RunStart,
    StopRequest,
)
from deep_reasoning.acp.wire import READER_LIMIT, Outbox
from deep_reasoning.acp.worker.protocol import Close, Prompt, Start, Stop
from deep_reasoning.mcp.wire import McpServerSpec, remember_seen

if TYPE_CHECKING:
    from deep_reasoning.acp.session import Session

logger = structlog.get_logger(__name__)

TERM_GRACE_S = 0.8  # SIGTERM, then SIGKILL the group (§6.4)
DRAIN_S = 0.3  # events the worker wrote before dying are still logged and sent
FLUSH_EVERY_S = 0.5
ENDS_WITH_ITS_PROMPT = ("failed", "build_failed")


class RunHandle:
    run_id: str
    encoder: Encoder

    def __init__(
        self,
        *,
        run_id: str,
        session: "Session",
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        heartbeat_s: float,
        log: RunLog,
        encoder: Encoder,
    ) -> None:
        self.run_id = run_id
        self.encoder = encoder
        self._session = session
        self._route = route
        self._outbox = outbox
        self._heartbeat_s = heartbeat_s
        self._log = log
        self._home = home
        self._worker_log = home.run_dir(run_id) / "worker.log"
        self._sending = asyncio.Lock()  # one RunEvent's updates go out together
        self._ended = asyncio.Event()
        self._end_logged = False
        self._asked: RunEndReason | None = None  # stopped or closed, by the front
        self._killing = False
        self._last_prompt_end: PromptEnd | None = None
        self._waiting: asyncio.Future[PromptEnd | RunEnd] | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._control_fd = -1
        self._pump: asyncio.Task[None] | None = None
        self._ticker: asyncio.Task[None] | None = None

    @classmethod
    async def start(
        cls,
        *,
        run_id: str,
        session: "Session",
        source: RunSource,
        after: RunEndReason | None,
        decomposition: str | None,
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        mode: Mode,
        heartbeat_s: float,
        mcp_servers: Sequence[McpServerSpec] = (),
    ) -> "RunHandle":
        """Create the run's log and worker, and start its pump and heartbeat.

        RunLog.create; append run.start (with after); grant = route.grant(session=...,
        run=run_id, upstream=source.client); spawn the worker: sys.executable -m
        deep_reasoning.acp.worker --control-fd C --events-fd E, pass_fds=(C, E),
        start_new_session=True, stdin=DEVNULL, stdout and stderr to runs/<run>/worker.log,
        cwd=session.cwd, env=worker_env(os.environ, grant); send
        Start(client_overrides=grant.client_overrides, mcp_servers=..., ...). The pump
        remembers the tools of each server a live mcp.status says is bound (D4 §4.7).
        """
        handle = cls(
            run_id=run_id,
            session=session,
            home=home,
            route=route,
            outbox=outbox,
            heartbeat_s=heartbeat_s,
            log=RunLog.create(home, run_id),
            encoder=Encoder(root=session.id, run=run_id, mode=mode, carry=session.cost),
        )
        await handle._log_and_send(
            RunStart(
                run=run_id,
                session=session.id,
                index=len(session.runs) + 1,
                after=after,
                cwd=str(session.cwd),
                namespace=source.namespace,
                mode=mode,
                decomposition=decomposition,
                source={
                    "config_path": str(source.config_path),
                    "namespace": source.namespace,
                    "client": dict(source.client),
                    "versions": dict(source.versions),
                },
            )
        )
        grant = route.grant(session=session.id, run=run_id, upstream=source.client)
        reader = await handle._spawn(session.cwd, worker_env(os.environ, grant))
        handle._send(
            Start(
                run=run_id,
                session=session.id,
                run_dir=str(home.run_dir(run_id)),
                config_path=str(source.config_path),
                namespace=source.namespace,
                client_overrides=dict(grant.client_overrides),
                mcp_servers=list(mcp_servers),
            )
        )
        handle._pump = asyncio.create_task(handle._pump_events(reader))
        handle._ticker = asyncio.create_task(handle._tick())
        return handle

    async def _spawn(self, cwd: Path, env: dict[str, str]) -> asyncio.StreamReader:
        control_read, self._control_fd = os.pipe()
        events_read, events_write = os.pipe()
        with self._worker_log.open("ab") as worker_log:
            self._process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "deep_reasoning.acp.worker",
                "--control-fd",
                str(control_read),
                "--events-fd",
                str(events_write),
                pass_fds=(control_read, events_write),
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=worker_log,
                stderr=worker_log,
                cwd=cwd,
                env=env,
            )
        os.close(control_read)
        os.close(events_write)
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader(limit=READER_LIMIT)
        await loop.connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader),
            os.fdopen(events_read, "rb", 0),
        )
        return reader

    def _send(self, message: BaseModel) -> None:
        """One control line; a worker that is gone is noticed by the pump, not here."""
        with contextlib.suppress(OSError):
            os.write(self._control_fd, (message.model_dump_json() + "\n").encode())

    async def _log_and_send(self, ev: RunEvent) -> RunEvent:
        async with self._sending:
            logged = self._log.append(ev)
            for session_id, update in self.encoder.feed(logged):
                await self._outbox.update(session_id, update)
        return logged

    async def _pump_events(self, reader: asyncio.StreamReader) -> None:
        while line := await reader.readline():
            try:
                ev = RUN_EVENT.validate_json(line)
            except ValidationError:
                logger.warning(
                    "dr_acp.unparseable_event", run=self.run_id, line=line[:200]
                )
                continue
            logged = await self._log_and_send(ev)
            if isinstance(logged, McpStatus):
                self._remember(logged)
            if isinstance(logged, PromptEnd):
                self._last_prompt_end = logged
                if logged.outcome not in ENDS_WITH_ITS_PROMPT:
                    self._answer_prompt(logged)
        code = await self._process.wait()
        await self._end(self._end_reason(), code)

    def _remember(self, status: McpStatus) -> None:
        """D4 §4.7: what each bound server told the agent, for the Tools tab."""
        try:
            remember_seen(
                self._home.root, self.run_id, status.servers, datetime.now(UTC)
            )
        except OSError:
            logger.exception("dr_acp.mcp_seen_failed", run=self.run_id)

    def _end_reason(self) -> RunEndReason:
        """The first that applies: the front asked; the last prompt failed; a crash."""
        if self._asked is not None:
            return self._asked
        last = self._last_prompt_end
        if last is not None and last.outcome in ENDS_WITH_ITS_PROMPT:
            return last.outcome
        return "crashed"

    async def _end(self, reason: RunEndReason, code: int | None) -> None:
        if self._end_logged:
            return
        self._end_logged = True
        detail = str(self._worker_log) if reason == "crashed" else None
        ended = await self._log_and_send(
            RunEnd(reason=reason, exit_code=code, detail=detail)
        )
        self._ticker.cancel()
        os.close(self._control_fd)
        self._control_fd = -1  # a late _send fails on this, never on a reused fd
        self._route.release(self.run_id)
        self._session.on_run_end(reason)
        last = self._last_prompt_end
        self._answer_prompt(last if reason in ENDS_WITH_ITS_PROMPT and last else ended)
        self._ended.set()

    def _answer_prompt(self, ev: PromptEnd | RunEnd) -> None:
        if self._waiting is not None and not self._waiting.done():
            self._waiting.set_result(ev)

    async def _tick(self) -> None:
        """Usage at most every FLUSH_EVERY_S; the root's on the heartbeat while a prompt
        is in flight and nothing else went out (the bridge's idle watchdog)."""
        while True:
            await asyncio.sleep(min(FLUSH_EVERY_S, self._heartbeat_s))
            async with self._sending:
                updates = self.encoder.flush_usage()
                idle = self._outbox.seconds_since_last_send >= self._heartbeat_s
                if not updates and idle and self.encoder.prompt_in_flight:
                    updates = [self.encoder.root_usage()]
                for session_id, update in updates:
                    await self._outbox.update(session_id, update)

    async def prompt(
        self,
        index: int,
        text: str,
        task: str,
        decomposition: str | None,
        dropped: list[str] | None = None,
    ) -> PromptEnd | RunEnd:
        """Log prompt.start, send Prompt, return the event that ended the prompt: its
        prompt.end, or the run.end of a run stopped, closed or crashed under it.

        After a failed or build_failed outcome, return only once run.end is logged.
        """
        self._waiting = asyncio.get_running_loop().create_future()
        await self._log_and_send(
            PromptStart(
                prompt=index,
                text=text,
                task=task,
                decomposition=decomposition,
                dropped=dropped or [],
            )
        )
        self._send(Prompt(prompt=index, task=task, decomposition=decomposition))
        return await self._waiting

    def stop_node(self, node: int) -> None:
        """Log stop.request and send Stop; return at once."""
        self._log.append(StopRequest(node=node))
        self._send(Stop(node=node))

    def _signal(self, sig: signal.Signals) -> None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(self._process.pid, sig)

    async def kill(self, reason: Literal["stopped", "closed"]) -> None:
        """End the worker's process group (§6.4). Idempotent."""
        if not self._killing and not self._end_logged:
            self._killing = True
            self._asked = reason
            self._signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(
                    asyncio.shield(self._process.wait()), TERM_GRACE_S
                )
            except TimeoutError:
                self._signal(signal.SIGKILL)
                await self._process.wait()
            try:
                await asyncio.wait_for(asyncio.shield(self._pump), DRAIN_S)
            except TimeoutError:
                self._pump.cancel()
                await self._end(reason, self._process.returncode)
        await self._ended.wait()

    async def close(self, grace_s: float = 2.0) -> None:
        """Send Close; kill("closed") if the worker has not exited after grace_s."""
        if self._end_logged:
            return
        self._asked = self._asked or "closed"
        self._send(Close())
        try:
            await asyncio.wait_for(asyncio.shield(self._ended.wait()), grace_s)
        except TimeoutError:
            await self.kill("closed")

    def child(self, session_id: str) -> ChildRef | None:
        """The live child with this session id, for cancel routing."""
        return self.encoder.child(session_id)
