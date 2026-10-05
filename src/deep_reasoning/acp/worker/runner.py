"""The worker: one deep_reasoner run, driven by control messages (§4.3).

python -m deep_reasoning.acp.worker --control-fd N --events-fd M
"""

import argparse
import asyncio
import contextlib
import logging
import os
import signal
import threading
import time
from collections.abc import Sequence
from importlib.metadata import version
from pathlib import Path
from typing import Any, NoReturn

import structlog
from deep_reasoner.core import (
    configure_structlog_fixture,
    quiet_http_client_logs,
    set_cache_dir,
)
from deep_reasoner.v2.cli import build_namespace_registry, build_reasoner, close_run
from deep_reasoner.v2.context import LogProcessor
from deep_reasoner.v2.decompositions import main_decomposition_turns
from structlog.contextvars import bound_contextvars

from deep_reasoning.acp.catalog import load_dr_config
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.runlog import Home, detail_of
from deep_reasoning.acp.worker.protocol import CONTROL, Close, Prompt, Start, Stop
from deep_reasoning.acp.worker.recorder import EventSink, Recorder
from deep_reasoning.acp.worker.stop import (
    DEAN_STOP_API,
    StopAdapter,
    resolve_stop_adapter,
)
from deep_reasoning.mcp.session import open_session

logger = structlog.get_logger(__name__)

CLOSE_RUN_WATCHDOG_S = 0.7
EXIT_CLOSED, EXIT_FAILED, EXIT_BUILD_FAILED, EXIT_TEARDOWN_HUNG = 0, 1, 2, 3


class RunKilled(BaseException):
    """Raised in the main thread by SIGTERM: the front ended the run."""


def as_text(value: Any) -> str:
    """value if it is a str, else its repr."""
    return value if isinstance(value, str) else repr(value)


def run_config(start: Start) -> Any:
    """The run's dr config: the file Start names, in Start's namespace, with the
    route's overrides merged over the main client and over each tool's own client."""
    cfg = load_dr_config(Path(start.config_path))
    cfg.entry_namespace = start.namespace
    cfg.client = cfg.client.model_copy(update=start.client_overrides)
    for name, overrides in start.tool_client_overrides.items():
        tool = cfg.tools[name]
        tool["client"] = {**tool["client"], **overrides}
    return cfg


class Worker:
    """One run across its control messages: built at the first prompt, kept between."""

    def __init__(self, control_fd: int, events_fd: int) -> None:
        self._control = os.fdopen(control_fd, "rb")
        self._sink = EventSink(events_fd)
        self._queue: asyncio.Queue[Start | Prompt | Close] = asyncio.Queue()
        self._start: Start | None = None
        self._recorder: Recorder | None = None
        self._adapter: StopAdapter | None = None
        self._reasoner: Any = None
        self._run_scope = contextlib.ExitStack()

    def read_control(self, loop: asyncio.AbstractEventLoop) -> None:
        """The reader thread. Stop is handled here (Dean's stop is callable from any
        thread); the rest goes to the main loop. EOF means the front died."""
        for line in self._control:
            message = CONTROL.validate_json(line)
            if isinstance(message, Stop):
                if self._adapter is not None:
                    self._adapter.stop(message.node)
                continue
            loop.call_soon_threadsafe(self._queue.put_nowait, message)
        os.killpg(0, signal.SIGKILL)

    async def serve(self) -> None:
        loop = asyncio.get_running_loop()
        threading.Thread(target=self.read_control, args=(loop,), daemon=True).start()
        while True:
            message = await self._queue.get()
            if isinstance(message, Start):
                self.start(message)
            elif isinstance(message, Prompt):
                await self.prompt(message)
            else:
                self.teardown(EXIT_CLOSED)

    def start(self, start: Start) -> None:
        """Logging, the recorder, the stop adapter and SIGTERM; then worker.ready."""
        self._start = start
        set_cache_dir(None)
        quiet_http_client_logs()
        run_dir = Path(start.run_dir)
        self._recorder = Recorder(self._sink, PriceTable.load(Home(run_dir.parents[1])))
        spec = os.environ.get("DR_ACP_STOP_API") or DEAN_STOP_API
        self._adapter = resolve_stop_adapter(self._recorder, spec)
        configure_structlog_fixture(
            console=False,
            extra_processors=[self._recorder, LogProcessor(run_dir.parent)],
            default_level=logging.WARNING,
        )
        signal.signal(signal.SIGTERM, self._killed)
        self._recorder.emit(
            "worker.ready",
            pid=os.getpid(),
            deep_reasoner=version("deep-reasoner"),
            stop_mode=self._adapter.mode,
        )

    def _killed(self, signum: int, frame: Any) -> None:
        self._recorder.mute()
        raise RunKilled

    def build(self, prompt: Prompt) -> None:
        """The reasoner, with the decomposition's turns puppeteered when there is one; its
        log context and model alias stay entered for the whole run."""
        start = self._start
        cfg = run_config(start)
        if prompt.decomposition is not None:
            cfg.task = prompt.task
            registry = build_namespace_registry(cfg)
            try:
                namespace_decompositions = registry.resolve(
                    start.namespace
                ).decompositions
            finally:
                registry.close()
            turns = main_decomposition_turns(
                prompt.decomposition,
                prompt.task,
                cfg.decompositions,
                namespace_decompositions,
                template_vars=cfg.prompt_template_variables,
            )
            self._recorder.set_puppeteer(turns)
        run_dir = Path(start.run_dir)
        # D4 §4.4: the granted servers are connected, all at once, before any tool is built.
        if statuses := open_session(cfg, start.mcp_servers, run_dir=run_dir):
            servers = [status.model_dump(mode="json") for status in statuses]
            self._recorder.emit("mcp.status", servers=servers)
        self._reasoner, alias = build_reasoner(
            cfg, run_dir=run_dir, main_decomposition=prompt.decomposition
        )
        self._run_scope.enter_context(
            bound_contextvars(task_id=start.run, log_dir=str(run_dir))
        )
        self._run_scope.enter_context(alias)

    async def prompt(self, prompt: Prompt) -> None:
        if self._reasoner is None:
            try:
                self.build(prompt)
            except Exception as exc:
                logger.exception("dr_acp.worker.build_failed")
                self._prompt_end(prompt, "build_failed", detail=detail_of(exc))
                self.teardown(EXIT_BUILD_FAILED)
        try:
            answer = await self._reasoner.acall(prompt.task)
        except Exception as exc:
            logger.exception("dr_acp.worker.drive_failed")
            self._prompt_end(prompt, "failed", detail=detail_of(exc))
            self.teardown(EXIT_FAILED)
        outcome = "exhausted" if self._reasoner.exhausted else "answered"
        self._prompt_end(prompt, outcome, answer=as_text(answer))

    def _prompt_end(
        self,
        prompt: Prompt,
        outcome: str,
        *,
        answer: str | None = None,
        detail: str | None = None,
    ) -> None:
        self._recorder.emit(
            "prompt.end",
            prompt=prompt.prompt,
            outcome=outcome,
            answer=answer,
            detail=detail,
        )

    def teardown(self, code: int) -> NoReturn:
        """close_run under a watchdog, then exit without waiting for sub-agent threads."""
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        threading.Thread(
            target=_exit_after, args=(CLOSE_RUN_WATCHDOG_S,), daemon=True
        ).start()
        if self._reasoner is not None:
            try:
                close_run(self._reasoner)
            except Exception:
                logger.exception("dr_acp.worker.close_run_failed")
        os._exit(code)


def _exit_after(seconds: float) -> None:
    time.sleep(seconds)
    os._exit(EXIT_TEARDOWN_HUNG)


def main(argv: Sequence[str] | None = None) -> int:
    """Read Start, then Prompts, until Close, a failure or SIGTERM; teardown ends the
    process with os._exit."""
    parser = argparse.ArgumentParser(prog="python -m deep_reasoning.acp.worker")
    parser.add_argument("--control-fd", type=int, required=True)
    parser.add_argument("--events-fd", type=int, required=True)
    args = parser.parse_args(argv)
    worker = Worker(args.control_fd, args.events_fd)
    try:
        asyncio.run(worker.serve())
    except RunKilled:
        worker.teardown(EXIT_CLOSED)
    return EXIT_CLOSED
