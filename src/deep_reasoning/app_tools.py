"""The agent's own tools: the app gives every run these, besides the Library's.

The engine builds each from this file by its path (factory_from), in the worker, with only
what its block in the run's config holds: the app file's path, the chat and the run.

history reads the chat's earlier runs from the app file, read-only, as the page reads them:
runs.py checks each row, and folded() folds a run's events into its tree as fold.js does.
"""

import copy
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import structlog
from deep_reasoner.primitives import Func

from deep_reasoning.library import HISTORY_DESCRIPTION, distrust
from deep_reasoning.runs import chat_turns, total_cost

log = structlog.get_logger()

Event = dict[str, Any]
Holder = dict[str, Any]
STARTED_WITH = ("node", "parent", "drive", "task", "namespace")
AGENT_FIELDS = (*STARTED_WITH, "status", "result")
ENDED_WITH = ("outcome", "answer", "detail", "cost", "seconds")
LOOKUP_FIELDS = ("node", "parent", "cell")


@dataclass
class Tree:
    """A run's events folded: the root agent's drive, each sub-agent drive as a row, and
    each node's current drive (its holder) with its parent's node."""

    root: Holder = field(
        default_factory=lambda: {"node": None, "drive": None, "costs": [], "steps": []}
    )
    rows: list[Holder] = field(default_factory=list)
    nodes: dict[Any, tuple[Holder, Any]] = field(default_factory=dict)
    cells: dict[Any, dict[str, Any]] = field(default_factory=dict)


def start_agent(tree: Tree, event: Event) -> None:
    node, parent = event.get("node"), event.get("parent")
    if parent is None:
        tree.root |= {"node": node, "drive": event.get("drive")}
        tree.nodes[node] = (tree.root, None)
        return
    cell = tree.cells.get(event.get("cell"))
    if cell is None:
        return
    row = {key: event.get(key) for key in STARTED_WITH}
    row |= {"status": "running", "result": None, "costs": [], "steps": []}
    if node not in cell["agents"]:
        cell["agents"].append(node)
    tree.rows.append(row)
    tree.nodes[node] = (row, parent)


def holder_of(tree: Tree, node: Any) -> Holder | None:
    return tree.nodes.get(node, (None, None))[0]


def add_step(tree: Tree, node: Any, step: dict[str, Any]) -> None:
    holder = holder_of(tree, node)
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
    while node in tree.nodes and node not in seen:
        seen.add(node)
        holder, node = tree.nodes[node]
        holder["costs"].append(event.get("cost"))


def end_agent(tree: Tree, event: Event) -> None:
    row = holder_of(tree, event.get("node"))
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


def well_keyed(event: Event) -> bool:
    """Whether *event*'s node, parent and cell are ones a run of the app's could have."""
    return all(isinstance(event.get(key), int | str | None) for key in LOOKUP_FIELDS)


def folded(events: list[Event]) -> Tree:
    """A run's events as the tree fold.js folds them into for the page. An event that
    isn't well keyed, as a file from someone else may hold, is left out."""
    tree = Tree()
    for event in events:
        fold = FOLDS.get(event["kind"])
        if fold is None:
            continue
        if not well_keyed(event):
            log.warning("history.event_left_out", seq=event["seq"])
            continue
        fold(tree, event)
    return tree


def turn_row(number: int, events: list[Event], tree: Tree) -> dict[str, Any]:
    start, end = events[0], events[-1]
    return {
        "turn": number,
        "message": start["prompt"],
        "namespace": start.get("namespace"),
        "model": start.get("model"),
        **{key: end.get(key) for key in ENDED_WITH},
        "agents": len(tree.rows),
    }


def agent_row(row: Holder) -> dict[str, Any]:
    fields = {key: row[key] for key in AGENT_FIELDS}
    return fields | {"cost": total_cost(row["costs"]), "steps": len(row["steps"])}


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

    @cache
    def earlier() -> list[tuple[list[Event], Tree]]:
        # Read once: no run of the chat's starts or ends while this one is going.
        return [(events, folded(events)) for events in earlier_runs(library, chat, run)]

    def chosen(turn: int) -> Tree:
        runs = earlier()
        if not runs:
            raise ValueError("This chat has no earlier messages: this is its first.")
        if not isinstance(turn, int) or not 1 <= turn <= len(runs):
            raise ValueError(
                f"There is no message {turn!r}: this chat's earlier messages are"
                f" numbered 1 to {len(runs)}."
            )
        return runs[turn - 1][1]

    def turns() -> list[dict[str, Any]]:
        """This chat's earlier messages, numbered from 1, with how each ended."""
        return [turn_row(number, *each) for number, each in enumerate(earlier(), 1)]

    def agents(turn: int) -> list[dict[str, Any]]:
        """Each sub-agent drive of message *turn*."""
        return [agent_row(row) for row in chosen(turn).rows]

    def steps(turn: int, node: Any = None) -> list[dict[str, Any]]:
        """The thoughts and cells of message *turn*'s top agent, or of sub-agent *node*."""
        tree = chosen(turn)
        top = node is None or node == tree.root["node"]
        drives = (
            [tree.root] if top else [row for row in tree.rows if row["node"] == node]
        )
        if not drives:
            nodes = [
                tree.root["node"],
                *dict.fromkeys(row["node"] for row in tree.rows),
            ]
            raise ValueError(
                f"Message {turn} has no agent {node!r}: its agents' nodes are {nodes}."
            )
        # A copy: the folded runs are kept for the next call.
        return copy.deepcopy([step for row in drives for step in row["steps"]])

    history = SimpleNamespace(turns=turns, agents=agents, steps=steps)
    return Func(history, description=HISTORY_DESCRIPTION)
