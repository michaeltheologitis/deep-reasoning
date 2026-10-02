"""The run log: RunEvents, one JSON line each, and the session index (§4.4)."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter

from deep_reasoning.acp.costs import CostLedger

Mode = Literal["native", "flat"]
RunEndReason = Literal["closed", "stopped", "crashed", "failed", "build_failed", "lost"]


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
    text: str
    task: str
    decomposition: str | None


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
        raise NotImplementedError

    def run_dir(self, run: str) -> Path:
        raise NotImplementedError

    def session_file(self, session: str) -> Path:
        raise NotImplementedError


class RunLog:
    """The append side of runs/<run>/events.jsonl. The front is its only writer."""

    @classmethod
    def create(cls, home: Home, run_id: str) -> "RunLog":
        """A new, empty log; creates the run directory."""
        raise NotImplementedError

    @classmethod
    def open(cls, home: Home, run_id: str) -> "RunLog":
        """An existing log, appended after its last event (replay marks a lost run)."""
        raise NotImplementedError

    def append(self, ev: RunEvent) -> RunEvent:
        """Assign seq and t, write one line, flush."""
        raise NotImplementedError

    @staticmethod
    def read(home: Home, run_id: str) -> Iterator[RunEvent]:
        """Every event of the run, in order. Raises on v != 1."""
        raise NotImplementedError


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
        raise NotImplementedError

    def save(self, home: Home) -> None:
        """Atomic: a temp file, then rename."""
        raise NotImplementedError
