"""The run log: RunEvents, one JSON line each, and the session index (§4.4)."""

import os
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from deep_reasoning.acp.costs import CostLedger

Mode = Literal["native", "flat"]
RunEndReason = Literal["closed", "stopped", "crashed", "failed", "build_failed", "lost"]
DETAIL_CAP = 2000


def detail_of(exc: BaseException) -> str:
    """An exception in the form deep_reasoner gives agent.end's detail, capped: every
    detail in the log, and every sentence that quotes one, reads the same."""
    return f"{type(exc).__name__}: {exc}"[:DETAIL_CAP]


class _Ev(BaseModel):
    v: Literal[1] = 1
    seq: int = 0
    t: float = 0.0


class RunStart(_Ev):
    kind: Literal["run.start"] = "run.start"
    run: str
    session: str
    index: int
    after: RunEndReason | None
    cwd: str
    namespace: str
    mode: Mode
    decomposition: str | None
    source: dict[str, Any]


class PromptStart(_Ev):
    kind: Literal["prompt.start"] = "prompt.start"
    prompt: int
    text: str  # the user's own text
    task: str  # the text without its slash command
    decomposition: str | None
    dropped: list[str] = []  # the client's text blocks after the user's, never the task


class StopRequest(_Ev):
    kind: Literal["stop.request"] = "stop.request"
    node: int


class RunEnd(_Ev):
    kind: Literal["run.end"] = "run.end"
    reason: RunEndReason
    exit_code: int | None
    detail: str | None


class WorkerReady(_Ev):
    kind: Literal["worker.ready"] = "worker.ready"
    pid: int
    deep_reasoner: str
    stop_mode: Literal["dean", "interim"]


class AgentStart(_Ev):
    kind: Literal["agent.start"] = "agent.start"
    node: int
    parent: int | None
    ancestry: list[int]
    depth: int
    task: str
    namespace: str
    backbone: str
    max_iter: int | None
    drive: int
    parent_cell: int | None
    dr_run: str | None


class Thought(_Ev):
    kind: Literal["thought"] = "thought"
    node: int
    text: str


class CellStart(_Ev):
    kind: Literal["cell.start"] = "cell.start"
    node: int
    cell: int
    code: str
    origin: Literal["think", "puppeteered", "inferred"]


class CellEnd(_Ev):
    kind: Literal["cell.end"] = "cell.end"
    node: int
    cell: int
    code: str
    output: str
    interrupted: bool = False


class Usage(_Ev):
    kind: Literal["usage"] = "usage"
    node: int
    call: Literal["think", "tool", "claude"]
    model: str | None
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    cost_source: Literal["provider", "table", "claude"] | None
    context_window: int | None


class StopAccepted(_Ev):
    kind: Literal["stop.accepted"] = "stop.accepted"
    node: int
    mode: Literal["dean", "interim"]
    accepted: bool
    reason: str | None
    backbone: str | None


class AgentEnd(_Ev):
    kind: Literal["agent.end"] = "agent.end"
    node: int
    status: Literal["done", "exhausted", "failed", "stopped"]
    dr_status: str
    iter: int | None
    answer: str | None
    detail: str | None
    stopped_by: int | None
    collateral: bool = False


class PromptEnd(_Ev):
    kind: Literal["prompt.end"] = "prompt.end"
    prompt: int
    outcome: Literal["answered", "exhausted", "failed", "build_failed"]
    answer: str | None
    detail: str | None


RunEvent = Annotated[
    RunStart
    | PromptStart
    | StopRequest
    | RunEnd
    | WorkerReady
    | AgentStart
    | Thought
    | CellStart
    | CellEnd
    | Usage
    | StopAccepted
    | AgentEnd
    | PromptEnd,
    Field(discriminator="kind"),
]
RUN_EVENT: TypeAdapter[RunEvent] = TypeAdapter(RunEvent)


@dataclass(frozen=True)
class Home:
    root: Path

    @classmethod
    def resolve(cls, flag: Path | None) -> "Home":
        """flag, else $DR_HOME, else ~/.deep-reasoning."""
        if flag is not None:
            return cls(flag)
        if env := os.environ.get("DR_HOME"):
            return cls(Path(env))
        return cls(Path.home() / ".deep-reasoning")

    def run_dir(self, run: str) -> Path:
        return self.root / "runs" / run

    def session_file(self, session: str) -> Path:
        return self.root / "sessions" / f"{session}.json"


class RunLog:
    """The append side of runs/<run>/events.jsonl. The front is its only writer."""

    def __init__(self, path: Path, last_seq: int) -> None:
        self._path = path
        self._seq = last_seq

    @classmethod
    def create(cls, home: Home, run_id: str) -> "RunLog":
        """A new, empty log; creates the run directory."""
        home.run_dir(run_id).mkdir(parents=True, exist_ok=True)
        path = home.run_dir(run_id) / "events.jsonl"
        path.touch()
        return cls(path, 0)

    @classmethod
    def open(cls, home: Home, run_id: str) -> "RunLog":
        """An existing log, appended after its last event (replay marks a lost run)."""
        events = list(cls.read(home, run_id))
        return cls(
            home.run_dir(run_id) / "events.jsonl", events[-1].seq if events else 0
        )

    def append(self, ev: RunEvent) -> RunEvent:
        """Assign seq and t, write one line, flush."""
        self._seq += 1
        logged = ev.model_copy(update={"seq": self._seq, "t": time.time()})
        with self._path.open("a", encoding="utf-8") as out:
            out.write(logged.model_dump_json() + "\n")
        return logged

    @staticmethod
    def read(home: Home, run_id: str) -> Iterator[RunEvent]:
        """Every event of the run, in order. Raises on v != 1."""
        with (home.run_dir(run_id) / "events.jsonl").open(encoding="utf-8") as lines:
            for line in lines:
                yield RUN_EVENT.validate_json(line)


class SessionIndex(BaseModel):
    """sessions/<session>.json (§4.4)."""

    v: Literal[1] = 1
    session: str
    cwd: str
    namespace: str
    started: bool
    source: dict[str, Any]
    runs: list[str]
    cost: CostLedger
    last_end: RunEndReason | None
    created: datetime

    @classmethod
    def load(cls, home: Home, session: str) -> "SessionIndex | None":
        path = home.session_file(session)
        return cls.model_validate_json(path.read_text()) if path.exists() else None

    def save(self, home: Home) -> None:
        """Atomic: a temp file, then rename."""
        path = home.session_file(self.session)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(self.model_dump_json())
        temporary.replace(path)
