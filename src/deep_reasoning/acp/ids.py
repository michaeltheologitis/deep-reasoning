"""Ids derived from a run's log: the same run always yields the same ids (§5.1)."""

from datetime import datetime


def new_session_id() -> str:
    """'s-' + secrets.token_hex(8)."""
    raise NotImplementedError


def new_run_id(now: datetime | None = None) -> str:
    """YYYYmmdd-HHMMSS-<6 hex>, deep_reasoner's run slug format."""
    raise NotImplementedError


def child_session_id(run: str, node: int) -> str:
    """<run>-n<node>."""
    raise NotImplementedError


def cell_id(run: str, node: int, k: int) -> str:
    """<run>-n<node>-c<k>, k from 1 per node."""
    raise NotImplementedError


def card_id(run: str, node: int, drive: int) -> str:
    """<run>-n<node>-a<drive>: a sub-agent's card in the flat stream."""
    raise NotImplementedError


def task_message_id(run: str, node: int, drive: int) -> str:
    """<run>-n<node>-t<drive>."""
    raise NotImplementedError


def answer_message_id(run: str, node: int, drive: int) -> str:
    """<run>-n<node>-r<drive>."""
    raise NotImplementedError


def short(id_: str) -> str:
    """§5.1's display form: "n2" for <run>-n2, "c2.1" for <run>-n2-c1, "a2.1" for
    <run>-n2-a1, "root" for a root session ("s-..."); any other id unchanged."""
    raise NotImplementedError
