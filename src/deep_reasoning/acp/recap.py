"""What a fresh run is given of its conversation: every earlier message and its answer, as
one user message (TASK-57).

The turns are read from the run logs, because nothing dr-acp holds in memory outlives the
run: after a Stop, the app restarts dr-acp and loads the session again. A turn that got no
answer is still given, with why it has none, so that "try that again" has the message.

One user message, not user and assistant pairs, reads the same on every backbone and
leaves the model's own turns as its REPL blocks. It says that the earlier runs' variables
are gone, so that the model does not reach for one an old answer names.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from deep_reasoning.acp.runlog import (
    Home,
    PromptEnd,
    PromptEndOutcome,
    PromptStart,
    RecapNote,
    RunEnd,
    RunEndReason,
    RunEvent,
    RunLog,
    RunStart,
)

TEXT_CAP = 4_000  # characters of one message or one answer; the rest is cut (R5)
RECAP_MAX_CHARS = 32_000  # characters of the kept turns' blocks, "\n\n"-joined (R5)

RECAP_HEAD = (
    "This conversation began before this run. Its earlier runs have ended, so their "
    "variables and sub-agents are gone; below are the user's earlier messages, each with "
    "the answer it got."
)
RECAP_TAIL = "The user's next message follows."
CUT_MARK = " … (cut short)"
EXHAUSTED = "(none: the run ended without a final answer)"
STOPPED = "(none: the user stopped the run before it answered)"
CUT_OFF = "(none: the run was cut off before it answered)"
_WITHOUT_ANSWER = {
    "exhausted": EXHAUSTED,
    "stopped": STOPPED,
    "crashed": CUT_OFF,
    "closed": CUT_OFF,
    "lost": CUT_OFF,
}


def left_out(n: int) -> str:
    if n == 1:
        return "Message 1 is left out, to fit."
    return f"Messages 1 to {n} are left out, to fit."


def failed(detail: str) -> str:
    return f"(none: the run failed: {detail})"


def could_not_start(detail: str) -> str:
    return f"(none: the run could not start: {detail})"


TurnEnd = PromptEndOutcome | RunEndReason


@dataclass(frozen=True)
class Turn:
    index: int  # 1-based across the conversation's runs, oldest first
    namespace: str  # its run's RunStart.namespace
    message: str  # PromptStart.task: the user's text without its slash command
    ended: TurnEnd  # PromptEnd.outcome; else the reason of the RunEnd under it; else "lost"
    answer: str | None  # PromptEnd.answer (answered, exhausted); else None
    detail: str | None  # PromptEnd.detail (failed, build_failed); else None


@dataclass(frozen=True)
class Recap:
    text: str | None  # the user message the run is seeded with; None: no turns
    note: RecapNote | None  # what RunStart records; None exactly when text is None


NO_RECAP = Recap(None, None)


def read_turns(home: Home, runs: Sequence[str]) -> list[Turn]:
    """Every run's turns, oldest first, numbered across the conversation. A log that cannot
    be read raises what RunLog.read raises, rather than leave a gap in the turns (R9)."""
    turns: list[Turn] = []
    for run in runs:
        turns += turns_of(RunLog.read(home, run), len(turns) + 1)
    return turns


def turns_of(events: Iterable[RunEvent], first: int = 1) -> list[Turn]:
    """One run's turns, numbered from first: each prompt.start, ended by its prompt.end, or by
    the run.end that came while it was open; one the log leaves open ended "lost"."""
    turns: list[Turn] = []
    namespace = ""
    asked: PromptStart | None = None
    for ev in events:
        if isinstance(ev, RunStart):
            namespace = ev.namespace
        elif isinstance(ev, PromptStart):
            asked = ev
        elif isinstance(ev, PromptEnd) and asked is not None:
            turns.append(
                Turn(
                    first + len(turns),
                    namespace,
                    asked.task,
                    ev.outcome,
                    ev.answer,
                    ev.detail,
                )
            )
            asked = None
        elif isinstance(ev, RunEnd) and asked is not None:
            turns.append(
                Turn(first + len(turns), namespace, asked.task, ev.reason, None, None)
            )
            asked = None
    if asked is not None:
        turns.append(
            Turn(first + len(turns), namespace, asked.task, "lost", None, None)
        )
    return turns


def recap_of(turns: Sequence[Turn], namespace: str) -> Recap:
    """RECAP_HEAD, the kept turns' blocks and RECAP_TAIL, blank lines between; NO_RECAP for
    no turns. The kept turns are the newest whose blocks fit in RECAP_MAX_CHARS, and always
    the newest; the head says how many older ones are left out. Each message and answer is
    cut at TEXT_CAP, so that one long text cannot crowd out the rest. A turn whose namespace
    is not namespace is labeled with it (R8)."""
    if not turns:
        return NO_RECAP
    kept: list[tuple[str, bool]] = []
    size = 0
    for turn in reversed(turns):
        block, shortened = _block(turn, namespace)
        size += len(block) + (len("\n\n") if kept else 0)
        if kept and size > RECAP_MAX_CHARS:
            break
        kept.insert(0, (block, shortened))
    omitted = len(turns) - len(kept)
    head = f"{RECAP_HEAD} {left_out(omitted)}" if omitted else RECAP_HEAD
    blocks = "\n\n".join(block for block, _ in kept)
    note = RecapNote(
        turns=len(kept),
        left_out=omitted,
        shortened=any(shortened for _, shortened in kept),
    )
    return Recap(f"{head}\n\n{blocks}\n\n{RECAP_TAIL}", note)


def _block(turn: Turn, namespace: str) -> tuple[str, bool]:
    """A turn's two lines, and whether either text was cut."""
    message, message_cut = _cut(turn.message)
    answer, answer_cut = _cut(_answer(turn))
    label = f" (namespace {turn.namespace})" if turn.namespace != namespace else ""
    block = f"Message {turn.index}{label}: {message}\nAnswer {turn.index}: {answer}"
    return block, message_cut or answer_cut


def _answer(turn: Turn) -> str:
    """What follows "Answer i:": the answer, or why the turn has none."""
    if turn.ended == "answered":
        return turn.answer or ""
    if turn.ended == "failed":
        return failed(turn.detail or "")
    if turn.ended == "build_failed":
        return could_not_start(turn.detail or "")
    return _WITHOUT_ANSWER[turn.ended]


def _cut(text: str) -> tuple[str, bool]:
    if len(text) <= TEXT_CAP:
        return text, False
    return text[:TEXT_CAP].rstrip() + CUT_MARK, True
