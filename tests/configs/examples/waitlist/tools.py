"""A tool factory of your own, in a file of your own.

`waitlist.yaml`, next to this file, reaches it with `factory_from: ./tools.py`. Nothing
here is registered in `TOOL_BUILDERS`, nothing in `deep_reasoner` imports it, and the
`dr` CLI is not forked. The path in that config is relative to the config, so this pair
of files travels together and works from whatever directory `dr` was run in.
"""
from __future__ import annotations

import json
from pathlib import Path

from deep_reasoner.primitives import Func
from deep_reasoner.tools import PersistentTool


class Waitlist(PersistentTool):
    """Course waitlists that survive the run.

    waitlist.join(student, course) -> str   "enrolled", or "waitlisted at N"
    waitlist.of(course)            -> list[str]  everyone queued, in joining order
    waitlist.enrolled(course)      -> list[str]  the ones who got a seat

    `PersistentTool` is the contract the run's end-of-run hook uses: a `persist_dir`
    and a `save()` taking no arguments. Inheriting it is the explicit way to say so;
    having both members is the other.
    """

    def __init__(self, capacity: int, persist: str | None = None):
        self.capacity = capacity
        self.persist_dir = Path(persist) if persist else None      # None -> never saved
        self.queues: dict[str, list[str]] = {}
        saved = self.persist_dir / "waitlist.json" if self.persist_dir else None
        if saved is not None and saved.exists():                   # resume the last run
            self.queues = json.loads(saved.read_text())

    def join(self, student: str, course: str) -> str:
        queue = self.queues.setdefault(course, [])
        if student not in queue:
            queue.append(student)
        place = queue.index(student) + 1
        if place <= self.capacity:
            return "enrolled"
        return f"waitlisted at {place - self.capacity}"

    def of(self, course: str) -> list[str]:
        return list(self.queues.get(course, []))

    def enrolled(self, course: str) -> list[str]:
        return self.of(course)[: self.capacity]

    def save(self) -> None:
        """Write the queues under `persist_dir`. Called with no arguments when the run ends."""
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        (self.persist_dir / "waitlist.json").write_text(json.dumps(self.queues, indent=2))


def build_waitlist(client, tool_cfg) -> Func:
    """Build the `waitlist` tool — the same `(client, tool_cfg) -> Func` shape every
    built-in builder has.

    `client` is the run's chat client, unused here because a waitlist calls no model. It
    stays in the signature so every factory has one shape. Every key of the YAML block
    except `factory` / `factory_from` arrives in `tool_cfg`.
    """
    return Func(
        Waitlist(tool_cfg["capacity"], tool_cfg.get("persist")),
        description=tool_cfg.get("description"),      # None -> the class docstring
    )
