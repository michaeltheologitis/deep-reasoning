"""Runs: each message is one run of deep_reasoner in a worker subprocess, streamed as events.

A run lives in runs/<run>/ under the app's home: spec.json, what the worker runs;
events.jsonl, every event as one JSON line, appended as it happens; and worker.log, the
worker's stderr. The server numbers each event (seq, from 1) and stamps its time (t).
"""

import asyncio
import json
import math
import mmap
import os
import signal
import sys
import time
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path
from typing import Any, Literal

import jinja2
import structlog

log = structlog.get_logger()

Outcome = Literal["answered", "exhausted", "failed", "stopped"]
RUNS = "runs"
EVENTS = "events.jsonl"
RUN_ID = r"^\d{8}-\d{6}-\d{6}$"
STOP_GRACE_S = 5.0
MIB = 1024 * 1024
LINE_LIMIT = 64 * MIB
TOO_LONG = (
    f"The run sent an event longer than {LINE_LIMIT // MIB} MiB, more than the app "
    "reads as one event, so the app ended the run."
)
SHUT_DOWN = "Deep Reasoning shut down while the run was going."
LOST = "Deep Reasoning stopped while the run was going, so the run was lost."
RECAP = jinja2.Template(
    """\
This conversation began before this run. Its earlier runs have ended, so their \
variables and sub-agents are gone; below are the user's earlier messages, each with \
the answer it got.
{% for turn in turns %}
Message {{ loop.index }}: {{ turn.message }}
Answer {{ loop.index }}: {% if turn.outcome == "answered" %}{{ turn.answer or "" }}
{%- elif turn.outcome == "failed" %}(none: the run failed: {{ turn.detail }})
{%- elif turn.outcome == "stopped" %}(none: the user stopped the run before it answered)
{%- else %}(none: the run ended without a final answer){% endif %}
{% endfor %}
The user's next message follows.""",
    undefined=jinja2.StrictUndefined,
)


class RunInProgress(Exception):
    """The chat already has a run going."""


@dataclass(frozen=True)
class Turn:
    message: str
    outcome: Outcome
    answer: str | None
    detail: str | None


@dataclass
class _Live:
    chat: str
    events: list[dict[str, Any]] = field(default_factory=list)
    watchers: set[asyncio.Queue] = field(default_factory=set)
    process: asyncio.subprocess.Process | None = None
    pump: asyncio.Task | None = None
    stop_asked: bool = False
    kill_timer: asyncio.TimerHandle | None = None
    detail: str | None = None  # why the server ended it, if it did

    @property
    def ended(self) -> bool:
        """A turn.end is recorded; the worker may still be closing the run."""
        return self.events[-1]["kind"] == "turn.end"


def read_events(home: Path, run: str) -> Iterator[dict[str, Any]]:
    """The run's events, read from its file a line at a time."""
    with (home / RUNS / run / EVENTS).open(encoding="utf-8") as events:
        for line in events:
            yield json.loads(line)


def first_event(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as events:
        return json.loads(events.readline())


def last_event(path: Path) -> dict[str, Any]:
    """The last event of a non-empty events file, found from the end without reading
    the rest."""
    with (
        path.open("rb") as file,
        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data,
    ):
        return json.loads(data[data.rfind(b"\n", 0, len(data) - 1) + 1 :])


def cut_torn_line(path: Path) -> int:
    """Cut off a last line the app was killed while writing; the size left."""
    size = path.stat().st_size
    if size == 0:
        return 0
    with (
        path.open("rb") as file,
        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as data,
    ):
        whole = data.rfind(b"\n") + 1
    if whole < size:
        os.truncate(path, whole)
    return whole


def append_event(home: Path, run: str, event: dict[str, Any]) -> None:
    with (home / RUNS / run / EVENTS).open("a", encoding="utf-8") as events:
        events.write(json.dumps(event) + "\n")


def totals(events: Sequence[dict[str, Any]], until: float) -> dict[str, Any]:
    """A turn's cost, None when any call's is unknown, and its seconds until *until*."""
    costs = [event["cost"] for event in events if event["kind"] == "usage"]
    cost = None if None in costs else math.fsum(costs)
    return {"cost": cost, "seconds": until - events[0]["t"]}


def read_turn(home: Path, run: str) -> Turn:
    """An ended run's message, and how it ended, from its first and last events."""
    path = home / RUNS / run / EVENTS
    start, end = first_event(path), last_event(path)
    return Turn(start["prompt"], end["outcome"], end["answer"], end["detail"])


def turn_starts(home: Path, chat: str) -> list[dict[str, Any]]:
    """The turn.start of each of the chat's runs, oldest first."""
    starts = [first_event(path) for path in sorted((home / RUNS).glob(f"*/{EVENTS}"))]
    return [start for start in starts if start["chat"] == chat]


def end_unfinished(home: Path) -> list[str]:
    """End, as failed, every run the app stopped under without a turn.end; their ids.

    A last line the app was killed while writing is cut off first. A run left with no
    whole event loses its events file: as far as the app can tell, it never started.
    """
    ended = []
    for path in sorted((home / RUNS).glob(f"*/{EVENTS}")):
        if not cut_torn_line(path):
            path.unlink()
            continue
        if last_event(path)["kind"] == "turn.end":
            continue
        run = path.parent.name
        events = list(read_events(home, run))
        end = {"kind": "turn.end", "outcome": "failed", "answer": None, "detail": LOST}
        stamp = {"seq": len(events) + 1, "t": time.time()}
        append_event(home, run, stamp | end | totals(events, events[-1]["t"]))
        ended.append(run)
    return ended


def recap_of(turns: Sequence[Turn]) -> str | None:
    """The chat so far as one user message for a fresh run: every earlier message and
    its answer, whole. None before the first answer."""
    return RECAP.render(turns=turns) if turns else None


def new_run_id() -> str:
    """The start time in UTC, to the microsecond: run ids sort in the order the runs
    began, across a change of the local clock."""
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")


def kill_group(pid: int) -> None:
    """SIGKILL the process group the worker leads: the worker and all it started."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        return


class Runs:
    """The live runs: each one's worker, its events so far, and the streams watching it."""

    def __init__(self, home: Path, *, stop_grace_s: float = STOP_GRACE_S) -> None:
        self.home = home
        self._stop_grace_s = stop_grace_s
        self._live: dict[str, _Live] = {}

    def live(self, chat: str) -> str | None:
        """The chat's run that is going, if one is: one whose turn has not ended."""
        return next(
            (
                run
                for run, live in self._live.items()
                if live.chat == chat and not live.ended
            ),
            None,
        )

    def exists(self, run: str) -> bool:
        return (self.home / RUNS / run / EVENTS).is_file()

    def start(
        self,
        chat: str,
        prompt: str,
        config_for: Callable[[Path], dict[str, Any]],
        earlier: Sequence[Turn],
    ) -> str:
        """Start a run of *prompt* in *chat*, given the chat's *earlier* turns, and return
        its id. *config_for* gives the engine config for the run's folder. Raises
        RunInProgress while the chat has a run going."""
        if self.live(chat) is not None:
            raise RunInProgress(chat)
        run = new_run_id()
        folder = self.home / RUNS / run
        folder.mkdir(parents=True)
        config = config_for(folder)
        spec = {"chat": chat, "prompt": prompt, "recap": recap_of(earlier)}
        (folder / "spec.json").write_text(json.dumps(spec | {"config": config}))
        live = _Live(chat)
        # Recorded before the run is listed, so a start that fails holds up no chat.
        self._record(
            run,
            live,
            {
                "kind": "turn.start",
                "run": run,
                "chat": chat,
                "prompt": prompt,
                "namespace": config.get("entry_namespace"),
                "model": config.get("model"),
            },
        )
        self._live[run] = live
        live.pump = asyncio.create_task(self._pump(run, live))
        return run

    def stop(self, run: str) -> bool:
        """Ask a run to stop: its worker stops the agent tree and ends the turn, or the
        group is killed after the grace period. False when the run is not going."""
        live = self._live.get(run)
        if live is None or live.ended:
            return False
        if not live.stop_asked:
            live.stop_asked = True
            self._ask_to_stop(live)
        return True

    async def events(self, run: str, after: int = 0) -> AsyncIterator[dict[str, Any]]:
        """The run's events after seq *after*; for a run that is going, then each new one
        as it happens, until the run is over."""
        live = self._live.get(run)
        if live is None:
            for event in islice(read_events(self.home, run), after, None):
                yield event
            return
        # The backlog and the subscription are taken in one step on the event loop, so
        # no event is missed or repeated between them.
        queue = asyncio.Queue()
        backlog = live.events[after:]
        live.watchers.add(queue)
        try:
            for event in backlog:
                yield event
            while (event := await queue.get()) is not None:
                yield event
        finally:
            live.watchers.discard(queue)

    async def close(self) -> None:
        """End every run that is going: the app is shutting down."""
        lives = list(self._live.values())
        for live in lives:
            live.detail = SHUT_DOWN
            if live.process is None:
                live.pump.cancel()
            else:
                kill_group(live.process.pid)
        await asyncio.gather(*(live.pump for live in lives), return_exceptions=True)

    def _ask_to_stop(self, live: _Live) -> None:
        process = live.process
        if process is None or process.returncode is not None:
            return
        process.stdin.write(b"stop\n")
        self._kill_after_grace(live)

    def _kill_after_grace(self, live: _Live) -> None:
        """Kill the worker's group after the grace period, unless it exits first."""
        if live.kill_timer is not None:
            live.kill_timer.cancel()
        loop = asyncio.get_running_loop()
        live.kill_timer = loop.call_later(
            self._stop_grace_s, kill_group, live.process.pid
        )

    def _record(self, run: str, live: _Live, event: dict[str, Any]) -> None:
        event = {"seq": len(live.events) + 1, "t": time.time()} | event
        if event["kind"] == "turn.end":
            event |= totals(live.events, event["t"])
        append_event(self.home, run, event)
        live.events.append(event)
        for queue in live.watchers:
            queue.put_nowait(event)

    async def _pump(self, run: str, live: _Live) -> None:
        """Start the worker and record its events until it exits; then end the run."""
        folder = self.home / RUNS / run
        try:
            with (folder / "worker.log").open("ab") as worker_log:
                live.process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "deep_reasoning.worker",
                    str(folder),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=worker_log,
                    cwd=folder,
                    start_new_session=True,
                    limit=LINE_LIMIT,
                )
            if live.stop_asked:
                self._ask_to_stop(live)
            await self._read(run, live)
        except Exception as error:
            log.exception("runs.lost_the_worker", run=run)
            live.detail = f"The app lost the run's worker: {error}"
        finally:
            await self._end(run, live)

    async def _read(self, run: str, live: _Live) -> None:
        while True:
            try:
                line = await live.process.stdout.readline()
            except ValueError:
                live.detail = TOO_LONG
                return
            if not line:
                return
            self._record(run, live, json.loads(line))
            if live.ended:
                # The worker saves the run's tools as it closes: it gets the whole grace
                # period for that, even after a Stop that used up most of it.
                self._kill_after_grace(live)

    async def _end(self, run: str, live: _Live) -> None:
        """Kill what is left of the worker's group, wait for the worker, and end the
        turn if the worker didn't. The chat and the streams are let go whatever fails."""
        try:
            if live.process is not None:
                kill_group(live.process.pid)
                await live.process.wait()
            if live.kill_timer is not None:
                live.kill_timer.cancel()
            if not live.ended:
                self._record(run, live, self._turn_end(run, live))
        finally:
            del self._live[run]
            for queue in live.watchers:
                queue.put_nowait(None)

    def _turn_end(self, run: str, live: _Live) -> dict[str, Any]:
        """The turn.end of a run whose worker ended without writing one."""
        end = {"kind": "turn.end", "answer": None}
        if live.stop_asked:
            return end | {"outcome": "stopped", "detail": None}
        detail = live.detail
        if detail is None:
            code = live.process.returncode if live.process else None
            worker_log = self.home / RUNS / run / "worker.log"
            detail = (
                f"The run's worker exited with code {code} before the run ended; "
                f"its log is {worker_log}."
            )
        return end | {"outcome": "failed", "detail": detail}
