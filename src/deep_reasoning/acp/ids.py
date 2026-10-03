"""Ids derived from a run's log: the same run always yields the same ids (§5.1)."""

import re
import secrets
from datetime import UTC, datetime

RUN_ID = r"\d{8}-\d{6}-[0-9a-f]{6}"
_CHILD_FORMS = re.compile(rf"{RUN_ID}-n(\d+)(?:-([ca])(\d+))?")


def new_session_id() -> str:
    return f"s-{secrets.token_hex(8)}"


def new_run_id(now: datetime | None = None) -> str:
    """YYYYmmdd-HHMMSS-<6 hex>, deep_reasoner's run slug format."""
    return f"{now or datetime.now(UTC):%Y%m%d-%H%M%S}-{secrets.token_hex(3)}"


def child_session_id(run: str, node: int) -> str:
    return f"{run}-n{node}"


def cell_id(run: str, node: int, k: int) -> str:
    return f"{run}-n{node}-c{k}"


def card_id(run: str, node: int, drive: int) -> str:
    """A sub-agent's card in the flat stream."""
    return f"{run}-n{node}-a{drive}"


def task_message_id(run: str, node: int, drive: int) -> str:
    return f"{run}-n{node}-t{drive}"


def answer_message_id(run: str, node: int, drive: int) -> str:
    return f"{run}-n{node}-r{drive}"


def short(id_: str) -> str:
    """§5.1's display form: "n2" for <run>-n2, "c2.1" for <run>-n2-c1, "a2.1" for
    <run>-n2-a1, "root" for a root session ("s-..."); any other id unchanged."""
    if id_.startswith("s-"):
        return "root"
    match = _CHILD_FORMS.fullmatch(id_)
    if match is None:
        return id_
    node, form, k = match.groups()
    return f"n{node}" if form is None else f"{form}{node}.{k}"
