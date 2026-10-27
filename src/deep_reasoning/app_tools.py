"""The agent's own tools: the app gives every run these, besides the Library's.

The engine builds each from this file by its path (factory_from), in the worker, with only
what its block in the run's config holds: the app file's path, the chat and the run.

history reads the chat's earlier runs from the app file, read-only, as the page reads them:
runs.py checks each row, and folded() folds a run's events into its tree as fold.js does.
"""

import math
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from deep_reasoner.primitives import Func

from deep_reasoning.library import HISTORY_DESCRIPTION, distrust
from deep_reasoning.runs import chat_turns

Event = dict[str, Any]
STARTED_WITH = ("node", "parent", "drive", "task", "namespace")
AGENT_FIELDS = (*STARTED_WITH, "status", "result")
ENDED_WITH = ("outcome", "answer", "detail", "cost", "seconds")


@dataclass
class Tree:
    """A run's events folded: the root agent's drive, each sub-agent drive as a row, and
    for each node its current drive and its parent's node."""

    root: dict[str, Any] = field(
        default_factory=lambda: {"node": None, "drive": None, "steps": []}
    )
    rows: list[dict[str, Any]] = field(default_factory=list)
    drives: dict[Any, dict[str, Any]] = field(default_factory=dict)
    parents: dict[Any, Any] = field(default_factory=dict)
    cells: dict[Any, dict[str, Any]] = field(default_factory=dict)


def start_agent(tree: Tree, event: Event) -> None:
    node, parent = event.get("node"), event.get("parent")
    if parent is None:
        tree.root |= {"node": node, "drive": event.get("drive")}
        tree.drives[node] = tree.root
        return
    cell = tree.cells.get(event.get("cell"))
    if cell is None:
        return
    row = {key: event.get(key) for key in STARTED_WITH}
    row |= {"status": "running", "result": None, "costs": [], "steps": []}
    if node not in cell["agents"]:
        cell["agents"].append(node)
    tree.rows.append(row)
    tree.drives[node] = row
    tree.parents[node] = parent


def add_step(tree: Tree, node: Any, step: dict[str, Any]) -> None:
    holder = tree.drives.get(node)
    if holder is not None:
        step["drive"] = holder["drive"]
        holder["steps"].append(step)


def think(tree: Tree, event: Event) -> None:
    add_step(tree, event.get("node"), {"kind": "think", "text": event.get("text")})


def start_cell(tree: Tree, event: Event) -> None:
    cell = {"kind": "cell", "code": event.get("code"), "output": None}
    cell |= {"status": "running", "agents": []}
    tree.cells[event.get("cell")] = cell
    add_step(tree, event.get("node"), cell)


def end_cell(tree: Tree, event: Event) -> None:
    cell = tree.cells.get(event.get("cell"))
    if cell is not None:
        cell |= {key: event.get(key) for key in ("code", "output", "status")}


def add_usage(tree: Tree, event: Event) -> None:
    """A call's cost counts for its agent and every agent above it."""
    node, seen = event.get("node"), set()
    # Each once: a file from someone else may name a node its own ancestor.
    while node in tree.parents and node not in seen:
        seen.add(node)
        tree.drives[node]["costs"].append(event.get("cost"))
        node = tree.parents[node]


def end_agent(tree: Tree, event: Event) -> None:
    row = tree.drives.get(event.get("node"))
    if row is None or row is tree.root:
        return
    result = event.get("result")
    row["status"] = event.get("status")
    row["result"] = event.get("detail") if result is None else result


def end_turn(tree: Tree, event: Event) -> None:
    """What the run left going when it ended was stopped with it."""
    for each in [*tree.rows, *tree.cells.values()]:
        if each["status"] == "running":
            each["status"] = "stopped"


FOLDS = {
    "agent.start": start_agent,
    "think": think,
    "cell.start": start_cell,
    "cell.end": end_cell,
    "usage": add_usage,
    "agent.end": end_agent,
    "turn.end": end_turn,
}


def folded(events: list[Event]) -> Tree:
    """A run's events as the tree fold.js folds them into for the page."""
    tree = Tree()
    for event in events:
        fold = FOLDS.get(event["kind"])
        if fold is not None:
            fold(tree, event)
    return tree


def summed(costs: list[Any]) -> float | None:
    """The total of *costs*; None once any is unknown, as runs.totals counts a turn's."""
    if all(isinstance(cost, int | float) for cost in costs):
        return math.fsum(costs)
    return None


def turn_row(number: int, events: list[Event]) -> dict[str, Any]:
    start, end = events[0], events[-1]
    return {
        "turn": number,
        "message": start["prompt"],
        "namespace": start.get("namespace"),
        "model": start.get("model"),
        **{key: end.get(key) for key in ENDED_WITH},
        "agents": len(folded(events).rows),
    }


def agent_row(row: dict[str, Any]) -> dict[str, Any]:
    fields = {key: row[key] for key in AGENT_FIELDS}
    return fields | {"cost": summed(row["costs"]), "steps": len(row["steps"])}


def open_read_only(library: str | Path) -> sqlite3.Connection:
    """The app file at *library*, for reading only: it can't write the file, and runs
    none of the file's own triggers or views. In WAL mode it holds up no event the server
    saves meanwhile."""
    connection = sqlite3.connect(f"{Path(library).as_uri()}?mode=ro", uri=True)
    distrust(connection)
    return connection


def earlier_runs(library: str, chat: str, run: str) -> list[list[Event]]:
    """The events of each of *chat*'s runs but *run*, oldest first, as the page reads
    them: a run that didn't start is left out, and one with no turn.end ends failed."""
    with closing(open_read_only(library)) as connection:
        turns = chat_turns(connection, chat)
    return [turn["events"] for turn in turns if turn["run"] != run]


def build_history(client: Any, params: dict[str, Any]) -> Func:
    """The history tool of run *run* of *chat*, in the app file *library*, as its block
    in the run's config names them."""
    library, chat, run = params["library"], params["chat"], params["run"]

    def chosen(turn: int) -> list[Event]:
        runs = earlier_runs(library, chat, run)
        if not runs:
            raise ValueError("This chat has no earlier messages: this is its first.")
        if not isinstance(turn, int) or not 1 <= turn <= len(runs):
            raise ValueError(
                f"There is no message {turn!r}: this chat's earlier messages are"
                f" numbered 1 to {len(runs)}."
            )
        return runs[turn - 1]

    def turns() -> list[dict[str, Any]]:
        """This chat's earlier messages, numbered from 1, with how each ended."""
        runs = earlier_runs(library, chat, run)
        return [turn_row(number, events) for number, events in enumerate(runs, 1)]

    def agents(turn: int) -> list[dict[str, Any]]:
        """Each sub-agent drive of message *turn*."""
        return [agent_row(row) for row in folded(chosen(turn)).rows]

    def steps(turn: int, node: Any = None) -> list[dict[str, Any]]:
        """The thoughts and cells of message *turn*'s top agent, or of sub-agent *node*."""
        tree = folded(chosen(turn))
        if node is None or node == tree.root["node"]:
            return tree.root["steps"]
        drives = [row for row in tree.rows if row["node"] == node]
        if not drives:
            nodes = [
                tree.root["node"],
                *dict.fromkeys(row["node"] for row in tree.rows),
            ]
            raise ValueError(
                f"Message {turn} has no agent {node!r}: its agents' nodes are {nodes}."
            )
        return [step for row in drives for step in row["steps"]]

    history = SimpleNamespace(turns=turns, agents=agents, steps=steps)
    return Func(history, description=HISTORY_DESCRIPTION)
