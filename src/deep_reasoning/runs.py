"""Runs: each message is one run of deep_reasoner in a worker subprocess, streamed as events.

A run's events are in the app file, saved as they happen, so a copy of the file carries
every chat's past turns: the runs table names each run's chat, and the events table holds
each event as the JSON the page folds. The server numbers each event (seq, from 1) and
stamps its time (t). runs/<run>/ in the file's data folder holds the run's working files:
spec.yaml, what the worker runs, with the engine config; worker.log, the worker's stderr;
and what the engine writes. The model's key reaches the worker in its environment only,
never the run's folder or the file. The worker works in the chat's folder: its cwd, where
the agent's Python reads and writes.
"""

import asyncio
import json
import math
import os
import re
import signal
import sqlite3
import sys
import time
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import jinja2
import structlog
import yaml

from deep_reasoning.folders import remove_unless_kept
from deep_reasoning.library import open_library, writing

log = structlog.get_logger()

Outcome = Literal["answered", "exhausted", "failed", "stopped"]
RUNS = "runs"
SPEC = "spec.yaml"
ADD_RUN = "INSERT INTO runs VALUES (?, ?)"
ADD_EVENT = "INSERT INTO events VALUES (?, ?, ?)"
FIRST_AND_LAST = (
    "SELECT data FROM events WHERE run = :run"
    " AND seq IN (1, (SELECT max(seq) FROM events WHERE run = :run)) ORDER BY seq"
)
LAST_EVENTS = (
    "SELECT id, (SELECT data FROM events WHERE run = id ORDER BY seq DESC LIMIT 1)"
    " FROM runs ORDER BY id"
)
# libyaml's where PyYAML has it: the pure-Python one takes ~0.6 s a MiB, on the loop.
YAML_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)
RUN_ID = r"^\d{8}-\d{6}-\d{6}$"
STOP_GRACE_S = 5.0
MIB = 1024 * 1024
LINE_LIMIT = 64 * MIB
TOO_LONG = (
    f"The run sent an event longer than {LINE_LIMIT // MIB} MiB, more than the app "
    "reads as one event, so the app ended the run."
)
# Never handed to a run: with it set, Claude Code bills that key instead of the subscription.
WITHHELD = "ANTHROPIC_API_KEY"
SHUT_DOWN = "Deep Reasoning shut down while the run was going."
LOST = "Deep Reasoning stopped while the run was going, so the run was lost."
LOST_END = {"kind": "turn.end", "outcome": "failed", "answer": None, "detail": LOST}
NOT_SAVED = "The app couldn't save the run in the Library file, so it ended the run"
RECAP = jinja2.Template(
    """\
This conversation began before this run. Its earlier runs have ended, so their \
variables and sub-agents are gone; below are the user's earlier messages, each with \
the answer it got.
{% for turn in turns %}
Message {{ loop.index }}{% if turn.namespace and turn.namespace != namespace %} (in namespace {{ turn.namespace }}){% endif %}: {{ turn.message }}
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
    namespace: str | None = None


@dataclass
class _Live:
    chat: str
    cwd: Path
    db: sqlite3.Connection  # the app file, which its events are saved in
    # for the worker's environment only, and in no repr a traceback might show
    keys: dict[str, str] = field(default_factory=dict, repr=False)
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


def open_events(library: Path) -> sqlite3.Connection:
    """The app file at *library*, to save a run's events in as they happen, one commit
    each, on the event loop: in WAL mode with synchronous NORMAL, a commit waits on no
    fsync, and a power cut may lose the last few, never the file."""
    connection = open_library(library)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
    except BaseException:
        connection.close()
        raise
    return connection


def save_event(connection: sqlite3.Connection, run: str, event: dict[str, Any]) -> None:
    """Add *event* to the run's in the app file; a turn.start adds the run to its chat."""
    with writing(connection):
        if event["kind"] == "turn.start":
            connection.execute(ADD_RUN, (run, event["chat"]))
        connection.execute(ADD_EVENT, (run, event["seq"], json.dumps(event)))


def read_events(
    connection: sqlite3.Connection, run: str, after: int = 0
) -> list[dict[str, Any]]:
    """The run's events after seq *after*, in order."""
    rows = connection.execute(
        "SELECT data FROM events WHERE run = ? AND seq > ? ORDER BY seq", (run, after)
    )
    return [json.loads(data) for (data,) in rows]


def totals(events: Sequence[dict[str, Any]], until: float) -> dict[str, Any]:
    """A turn's cost, None when any call's is unknown, and its seconds until *until*."""
    costs = [event["cost"] for event in events if event["kind"] == "usage"]
    cost = None if None in costs else math.fsum(costs)
    return {"cost": cost, "seconds": until - events[0]["t"]}


def read_turn(connection: sqlite3.Connection, run: str) -> Turn:
    """An ended run's message, how it ended and its namespace, from its first and last
    events; a run the app couldn't save the end of ended failed."""
    rows = connection.execute(FIRST_AND_LAST, {"run": run})
    start, *rest = [json.loads(data) for (data,) in rows]
    end = rest[0] if rest and rest[0]["kind"] == "turn.end" else LOST_END
    return Turn(
        start["prompt"],
        end["outcome"],
        end["answer"],
        end["detail"],
        start.get("namespace"),
    )


def chat_runs(connection: sqlite3.Connection, chat: str) -> list[str]:
    """The chat's runs, oldest first. A run's id names its folder, so one the app could
    not have made, as a file from someone else may hold, is left out."""
    rows = connection.execute("SELECT id FROM runs WHERE chat = ? ORDER BY id", (chat,))
    runs = []
    for (run,) in rows:
        if isinstance(run, str) and re.fullmatch(RUN_ID, run):
            runs.append(run)
        else:
            log.warning("runs.left_out", run=repr(run))
    return runs


def delete_runs(connection: sqlite3.Connection, chat: str) -> list[str]:
    """Delete the chat's runs and their events from the app file; their ids."""
    with writing(connection):
        runs = chat_runs(connection, chat)
        connection.execute(
            "DELETE FROM events WHERE run IN (SELECT id FROM runs WHERE chat = ?)",
            (chat,),
        )
        connection.execute("DELETE FROM runs WHERE chat = ?", (chat,))
    return runs


def end_unfinished(connection: sqlite3.Connection) -> list[str]:
    """End, as failed, every run the app stopped under without a turn.end; their ids."""
    rows = connection.execute(LAST_EVENTS).fetchall()
    unfinished = [run for run, last in rows if json.loads(last)["kind"] != "turn.end"]
    for run in unfinished:
        events = read_events(connection, run)
        stamp = {"seq": len(events) + 1, "t": time.time()}
        save_event(connection, run, stamp | LOST_END | totals(events, events[-1]["t"]))
    return unfinished


def recap_of(turns: Sequence[Turn], namespace: str | None) -> str | None:
    """The chat so far as one user message for a fresh run in *namespace*: every earlier
    message and its answer, whole, each marked when it ran in another namespace. None
    before the first answer."""
    return RECAP.render(turns=turns, namespace=namespace) if turns else None


def new_run_id() -> str:
    """The start time in UTC, to the microsecond: run ids sort in the order the runs
    began, across a change of the local clock."""
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")


def worker_env(keys: dict[str, str]) -> dict[str, str]:
    """The app's environment with the run's *keys* added, and never ANTHROPIC_API_KEY."""
    return {
        name: value for name, value in (os.environ | keys).items() if name != WITHHELD
    }


def kill_group(pid: int) -> None:
    """SIGKILL the process group the worker leads: the worker and all it started."""
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        return


class Runs:
    """The runs of the app file at *library*, with their folders in *home*, its data
    folder; and the live ones: each one's worker, its events so far, and the streams
    watching it."""

    def __init__(
        self, library: Path, home: Path, *, stop_grace_s: float = STOP_GRACE_S
    ) -> None:
        self.library = library
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
        with closing(open_library(self.library)) as connection:
            found = connection.execute("SELECT 1 FROM runs WHERE id = ?", (run,))
            return found.fetchone() is not None

    def start(
        self,
        chat: str,
        prompt: str,
        config_for: Callable[[Path], dict[str, Any]],
        earlier: Sequence[Turn],
        provider: str | None = None,
        keys: dict[str, str] | None = None,
        folder: Path | None = None,
    ) -> str:
        """Start a run of *prompt* in *chat*, given the chat's *earlier* turns, and return
        its id. *config_for* gives the engine config for the run's folder; *provider*
        names who serves its model, and *keys* go into the worker's environment only.
        The worker works in *folder*, the run's own folder unless given.
        Raises RunInProgress while the chat has a run going."""
        if self.live(chat) is not None:
            raise RunInProgress(chat)
        run = new_run_id()
        run_folder = self.home / RUNS / run
        run_folder.mkdir(parents=True)
        config = config_for(run_folder)
        namespace = config.get("entry_namespace")
        recap = recap_of(earlier, namespace)
        spec = {"chat": chat, "prompt": prompt, "recap": recap, "config": config}
        # YAML keeps dates and int keys; ASCII, as a raw NEL would read back as a space.
        spec_yaml = yaml.dump(spec, Dumper=YAML_DUMPER, sort_keys=False)
        (run_folder / SPEC).write_text(spec_yaml)
        live = _Live(chat, folder or run_folder, open_events(self.library), keys or {})
        start = {
            "kind": "turn.start",
            "run": run,
            "chat": chat,
            "prompt": prompt,
            "namespace": namespace,
            "model": config.get("model"),
            "provider": provider,
            "folder": str(live.cwd),
        }
        # Recorded before the run is listed, so a start that fails holds up no chat.
        try:
            self._record(run, live, start)
        except BaseException:
            live.db.close()
            raise
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
            with closing(open_library(self.library)) as connection:
                events = read_events(connection, run, after)
            for event in events:
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

    def folders_in_use(self, besides: str) -> list[str]:
        """The folders the runs of every chat but *besides* are working in."""
        return [str(live.cwd) for live in self._live.values() if live.chat != besides]

    async def remove(self, chat: str, keep: Sequence[str] = ()) -> None:
        """Delete the chat's runs, their events and their folders, stopping the one going,
        once each of their workers has exited: a worker writes into its run's folder until
        then, even after turn.end. A run's folder that is or holds a folder in *keep* is
        kept."""
        workers = []
        for run, live in self._live.items():
            if live.chat == chat:
                self.stop(run)
                workers.append(live.pump)
        if workers:
            await asyncio.wait(workers)
        with closing(open_library(self.library)) as connection:
            runs = delete_runs(connection, chat)
        for run in runs:
            remove_unless_kept(self.home / RUNS / run, keep)

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
        """Number and stamp *event*, send it to the run's streams, and save it. Sent
        first: a run whose event can't be saved ends, and its streams still see it end."""
        event = {"seq": len(live.events) + 1, "t": time.time()} | event
        if event["kind"] == "turn.end":
            event |= totals(live.events, event["t"])
        live.events.append(event)
        for queue in live.watchers:
            queue.put_nowait(event)
        save_event(live.db, run, event)

    async def _pump(self, run: str, live: _Live) -> None:
        """Start the worker and record its events until it exits; then end the run."""
        folder = self.home / RUNS / run
        try:
            with (folder / "worker.log").open("ab") as worker_log:
                # -P: a module in the chat's folder mustn't shadow the worker's own
                live.process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-P",
                    "-m",
                    "deep_reasoning.worker",
                    str(folder),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=worker_log,
                    cwd=live.cwd,
                    env=worker_env(live.keys),
                    start_new_session=True,
                    limit=LINE_LIMIT,
                )
            if live.stop_asked:
                self._ask_to_stop(live)
            await self._read(run, live)
        except sqlite3.Error as error:
            log.exception("runs.not_saved", run=run)
            live.detail = f"{NOT_SAVED}: {error}."
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
        except sqlite3.Error:
            # Its streams saw the turn.end; the file gets one when the app next starts.
            log.exception("runs.end_not_saved", run=run)
        finally:
            live.db.close()
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
