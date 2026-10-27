"""The agent's own tools: the app gives every run these, besides the Library's.

The engine builds each from this file by its path (factory_from), in the worker, with only
what its block in the run's config holds: the app file's path, the chat, the run, the chat's
namespace and the variables that hold keys. Each opens the app file as it is, never making
a moved or deleted one afresh.

history reads the chat's earlier runs from the app file, read-only, as the page reads them:
runs.py checks each row, and folded() folds a run's events into its tree as fold.js does.

library reads and writes the Library through library.py, with the panel's checks and
transactions; the locks are here, as the panel may still edit root, a namespace's repl and
reasoner, and which namespaces grant the app's own tools. It writes only in a run whose
chat's namespace grants it, so a sub-agent spawned into such a namespace from another chat
can't, and never a key. It guards the tool, not the file: a cell can open the file itself.
A tool it writes is built first, as a run builds it, from a file in the run's tools folder.
Each change is logged as library.change, which the worker records as a run event.
"""

import ast
import copy
import os
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from functools import cache
from itertools import count
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import structlog
from deep_reasoner.namespaces import ROOT, NamespaceConfig, NamespaceRegistry
from deep_reasoner.primitives import Func
from deep_reasoner.tools import ToolBuildError
from deep_reasoner.v2.cli import V2Config, make_tool

from deep_reasoning.library import (
    APP_TOOLS,
    BUILDERS,
    HISTORY_DESCRIPTION,
    LIBRARY_DESCRIPTION,
    LIBRARY_TOOL,
    LibraryError,
    add_decomposition,
    add_namespace,
    change_namespace,
    config_and_registry,
    distrust,
    dump,
    loaded,
    namespace_rows,
    store_tool,
    tool_file,
)
from deep_reasoning.runs import CHANGE_FIELDS, chat_turns, secrets_of, total_cost

log = structlog.get_logger()

Event = dict[str, Any]
Holder = dict[str, Any]
STARTED_WITH = ("node", "parent", "drive", "task", "namespace")
AGENT_FIELDS = (*STARTED_WITH, "status", "result")
ENDED_WITH = ("outcome", "answer", "detail", "cost", "seconds")
LOOKUP_FIELDS = ("node", "parent", "cell")
ROOT_LOCKED = (
    "root is locked: the library tool never writes it. Write into another namespace."
)
NOT_THIS_CHAT = (
    "The Library can be changed only in a chat whose namespace grants the library tool;"
    " pick librarian under the message box."
)
NOT_TEXT = "The namespace's name and the YAML should be text."
# As the panel's limit on a decomposition's file; past 64 MiB, its change event would end
# the run after the write.
MAX_YAML_CHARS = 1_000_000
TOO_LONG = f"The YAML may be at most {MAX_YAML_CHARS:,} characters."
HOLDS_A_KEY = (
    "What you wrote holds a provider's key, and the Library file is shared, so keys never"
    " go in it. Take the key out."
)
# reasoner: claude_code would bill the user's subscription.
LOCKED_FIELDS = ("repl", "reasoner")
USERS_CHOICE = "the user's choice, in the Library panel."
# A tool of this factory, or a reasoner of this type, runs on the user's subscription.
CLAUDE_CODE = "claude_code"
NOT_A_TOOL = (
    "name, source and factory should be text, and settings a dict of plain values (text,"
    " numbers, True, False, None, and lists and dicts of them keyed by text, each one"
    " used once), or None."
)
PLAIN = (str, int, float, bool, type(None))
# Deeper settings are refused, as YAML writes them by recursion.
MAX_NESTING = 20
# A run hands the factory every key of the tool's block but these.
OWN_KEYS = ("factory", "factory_from")
SETS_OWN_KEYS = "settings may not hold factory or factory_from: write_tool sets them."
RESERVED_TOOLS = (*BUILDERS, *APP_TOOLS)
TOOL_TOO_LONG = (
    f"The source, and the settings as YAML, may each be at most {MAX_YAML_CHARS:,}"
    " characters."
)
# Where a tool is built to check it, in the run's tools folder.
CHECKS = "checks"


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


def add_change(tree: Tree, event: Event) -> None:
    """A change the library tool made, as a step of the agent that made it."""
    change = {key: event.get(key) for key in CHANGE_FIELDS}
    add_step(tree, event.get("node"), {"kind": "change"} | change)


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
    "library.change": add_change,
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


def open_existing(library: str | Path, mode: str = "ro") -> sqlite3.Connection:
    """The app file at *library* as it is, to read ("ro") or to write ("rw"): unlike
    open_library, it never makes a moved or deleted file afresh. It runs none of the file's
    own triggers or views, and wipes what it deletes. In WAL mode a reader holds up no event
    the server saves meanwhile."""
    connection = sqlite3.connect(
        f"{Path(library).as_uri()}?mode={mode}", uri=True, isolation_level=None
    )
    connection.execute("PRAGMA secure_delete = ON")
    distrust(connection)
    return connection


@contextmanager
def app_file(library: str, mode: str) -> Iterator[sqlite3.Connection]:
    """The app file as it is, for one use; a SQLite failure (busy, read only, moved or
    deleted) as a LibraryError in words the model can pass on."""
    try:
        with closing(open_existing(library, mode)) as connection:
            yield connection
    except sqlite3.OperationalError as error:
        raise LibraryError(
            f"The Library file can't be used now ({error}); try again."
        ) from error


def earlier_runs(library: str, chat: str, run: str) -> list[list[Event]]:
    """The events of each of *chat*'s runs but *run*, oldest first, as the page reads
    them: a run that didn't start is left out, and one with no turn.end ends failed."""
    with closing(open_existing(library)) as connection:
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
        """The thoughts, cells and Library changes of message *turn*'s top agent, or of
        sub-agent *node*."""
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


def texts_in(data: Any) -> Iterator[str]:
    """Every text in parsed YAML *data*, keys included; each mapping or list once, as
    aliases may share or nest them."""
    stack, seen = [data], set()
    while stack:
        value = stack.pop()
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict | list) and id(value) not in seen:
            seen.add(id(value))
            stack.extend(
                [*value, *value.values()] if isinstance(value, dict) else value
            )


def check_no_key(texts: list[str], key_names: list[str]) -> None:
    """Raise if any of *texts* holds the value of a key variable in *key_names*."""
    secrets = secrets_of(os.environ, key_names)
    if any(secret in text for secret in secrets for text in texts):
        raise LibraryError(HOLDS_A_KEY)


def check_writable(namespace: str, yaml: str, key_names: list[str]) -> None:
    """Raise unless the tool may write *yaml* for the namespace named *namespace*."""
    # Exactly str: a subclass could compare unequal to "root" and still name it.
    if type(namespace) is not str or type(yaml) is not str:
        raise LibraryError(NOT_TEXT)
    if namespace == ROOT:
        raise LibraryError(ROOT_LOCKED)
    if len(yaml) > MAX_YAML_CHARS:
        raise LibraryError(TOO_LONG)
    # Parsed too, as an escape such as "\x73k-" spells a key the raw text doesn't hold.
    check_no_key([namespace, yaml, *texts_in(loaded(yaml))], key_names)


def plain(value: Any) -> bool:
    """Whether *value* is text, a number, True, False or None, or a list or dict of them
    keyed by text, nested at most MAX_NESTING deep, each list and dict in it once (so
    none holds itself)."""
    stack, seen = [(value, 0)], set()
    while stack:
        each, depth = stack.pop()
        if type(each) in PLAIN:
            continue
        if type(each) not in (list, dict) or id(each) in seen or depth == MAX_NESTING:
            return False
        seen.add(id(each))
        if type(each) is dict and any(type(key) is not str for key in each):
            return False
        items = each.values() if type(each) is dict else each
        stack.extend((item, depth + 1) for item in items)
    return True


def check_tool(
    name: str, source: str, factory: str, settings: Any, key_names: list[str]
) -> None:
    """Raise unless the tool may write tool *name*, built by the function *factory* in
    the Python *source* with *settings*, before it is built."""
    texts = [name, source, factory]
    is_plain = settings is None or type(settings) is dict and plain(settings)
    if any(type(each) is not str for each in texts) or not is_plain:
        raise LibraryError(NOT_A_TOOL)
    if settings and any(key in settings for key in OWN_KEYS):
        raise LibraryError(SETS_OWN_KEYS)
    tool_file(name)
    if name in RESERVED_TOOLS:
        raise LibraryError(
            f'"{name}" is the name of a built-in or app tool ({", ".join(RESERVED_TOOLS)});'
            " pick another."
        )
    if max(len(source), len(dump(settings))) > MAX_YAML_CHARS:
        raise LibraryError(TOOL_TOO_LONG)
    check_no_key([*texts, *texts_in(settings)], key_names)
    try:
        module = ast.parse(source)
    except SyntaxError as error:
        raise LibraryError(
            f"The source is not valid Python (line {error.lineno}: {error.msg})."
        ) from error
    # Its string literals too, as an escape can spell a key the raw text doesn't hold.
    literals = [
        node.value
        for node in ast.walk(module)
        if isinstance(node, ast.Constant) and type(node.value) is str
    ]
    check_no_key(literals, key_names)


def claude_code_tools(config: V2Config, tools: Iterable[str]) -> list[str]:
    """Those of *tools* that run Claude Code, sorted."""
    return sorted(
        tool
        for tool in tools
        if config.tools.get(tool, {}).get("factory", tool) == CLAUDE_CODE
    )


def check_locks(
    config: V2Config, registry: NamespaceRegistry, namespace: NamespaceConfig
) -> None:
    """Raise if *namespace* sets or changes what only the user may: its repl or reasoner,
    which of the app's own tools it grants, or a tool that runs Claude Code, granted
    afresh; or, when new, would inherit library or Claude Code."""
    name = namespace.name
    new = name not in registry.names
    stored = NamespaceConfig(name=name) if new else registry.config(name)
    for key in LOCKED_FIELDS:
        if getattr(namespace, key) != getattr(stored, key):
            raise LibraryError(
                f"{key} may not be set or changed: a namespace's repl and reasoner are"
                f" {USERS_CHOICE}"
            )
    changed = sorted((set(namespace.tools) ^ set(stored.tools)) & APP_TOOLS.keys())
    if changed:
        raise LibraryError(
            f"tools may not add or take out {' and '.join(changed)}: which namespaces"
            f" grant the app's own tools is {USERS_CHOICE}"
        )
    claude = claude_code_tools(config, set(namespace.tools) - set(stored.tools))
    if claude:
        raise LibraryError(
            f"tools may not add {' and '.join(claude)}, which runs Claude Code on the"
            f" user's subscription: granting it is {USERS_CHOICE}"
        )
    above = name.rpartition(".")[0] or ROOT
    # A change keeps its chain, and a missing parent is refused after this.
    if new and above in registry.names:
        check_inherited(config, registry, name, above)


def check_inherited(
    config: V2Config, registry: NamespaceRegistry, name: str, above: str
) -> None:
    """Raise if new namespace *name*, under *above*, would inherit library or Claude
    Code, as its backbone or a tool."""
    resolved = registry.resolve(above)
    if LIBRARY_TOOL in resolved.tools:
        raise LibraryError(
            f"{name} would inherit library from {resolved.sources.tools[LIBRARY_TOOL]}:"
            f" which namespaces grant the app's own tools is {USERS_CHOICE}"
        )
    if registry.backbone(above) == CLAUDE_CODE:
        level = resolved.sources.reasoner or "the run settings"
        raise LibraryError(
            f"{name} would inherit the claude_code reasoner from {level}, which runs on"
            f" the user's subscription: which namespaces run Claude Code is {USERS_CHOICE}"
        )
    claude = claude_code_tools(config, resolved.tools)
    if claude:
        tool = claude[0]
        raise LibraryError(
            f"{name} would inherit {tool}, which runs Claude Code on the user's"
            f" subscription, from {resolved.sources.tools[tool]}: which namespaces have it"
            f" is {USERS_CHOICE}"
        )


def logged(done: str, before: str | None, after: str, **change: str) -> Event:
    """Log a change the tool made as library.change; what it did, for the model."""
    log.info("library.change", **change, before=before, after=after)
    return {"done": done, **change}


def build_library(client: Any, params: dict[str, Any]) -> Func:
    """The library tool, over the app file *library* its block in the run's config names,
    for a run of a chat in *namespace*, whose worker holds keys in *key_names*; it builds
    a tool it writes with the run's *client*, in the run's *tools_dir*."""
    library, chat_namespace = params["library"], params["namespace"]
    key_names, tools_dir = params["key_names"], Path(params["tools_dir"])
    checks = count(1)

    def show() -> list[dict[str, Any]]:
        """Every namespace, as the Library panel shows it."""
        with app_file(library, "ro") as connection:
            return namespace_rows(connection, *config_and_registry(connection))

    def check_grant(registry: NamespaceRegistry) -> None:
        """Raise unless this run's chat is in a namespace that grants the library tool, as
        the Library stands under the write lock: a grant taken away meanwhile counts."""
        granted = chat_namespace in registry.names and (
            LIBRARY_TOOL in registry.resolve(chat_namespace).tools
        )
        if not granted:
            raise LibraryError(NOT_THIS_CHAT)

    def may_write(connection: sqlite3.Connection) -> None:
        check_grant(config_and_registry(connection)[1])

    def may_change(connection: sqlite3.Connection, namespace: NamespaceConfig) -> None:
        config, registry = config_and_registry(connection)
        check_grant(registry)
        check_locks(config, registry, namespace)

    def write_decomposition(namespace: str, yaml: str) -> dict[str, Any]:
        """Add the decomposition *yaml* to *namespace*, or replace the one of its name."""
        check_writable(namespace, yaml, key_names)
        with app_file(library, "rw") as connection:
            stored, before = add_decomposition(
                connection, namespace, yaml, replace=True, allowed=may_write
            )
        done = "added" if before is None else "replaced"
        return logged(
            done,
            before,
            yaml,
            what="decomposition",
            namespace=namespace,
            name=stored["name"],
        )

    def add(name: str, yaml: str) -> dict[str, Any]:
        """Add namespace *name* with the fields *yaml* sets."""
        check_writable(name, yaml, key_names)
        with app_file(library, "rw") as connection:
            stored = add_namespace(connection, name, yaml, allowed=may_change)
        return logged(
            "added", None, stored, what="namespace", namespace=name, name=name
        )

    def change(name: str, yaml: str) -> dict[str, Any]:
        """Give namespace *name* the fields *yaml* sets in place of its own."""
        check_writable(name, yaml, key_names)
        with app_file(library, "rw") as connection:
            before, stored = change_namespace(
                connection, name, yaml, allowed=may_change
            )
        return logged(
            "changed", before, stored, what="namespace", namespace=name, name=name
        )

    def check_builds(name: str, block: dict[str, Any], source: str) -> None:
        """Raise unless the engine builds tool *name* from *source*, as a run would."""
        # A folder of its own each time: the engine keeps each file it imported, by path.
        file = tools_dir / CHECKS / str(next(checks)) / tool_file(name)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(source, encoding="utf-8")
        try:
            make_tool(
                name,
                block | {"factory_from": str(file)},
                client=client,
                config_path=None,
            )
        except ToolBuildError as error:
            raise LibraryError(
                f"Tool {name} doesn't build, so it wasn't written: {error.detail}"
            ) from error

    def write_tool(
        name: str, source: str, factory: str, settings: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Add tool *name*, built by the function *factory* in the Python *source* with
        *settings* as its params, or replace the one of its name."""
        check_tool(name, source, factory, settings, key_names)
        # The grant first, before the tool's code runs; the build holds no write lock.
        with app_file(library, "ro") as connection:
            may_write(connection)
        block = {
            "factory": factory,
            "factory_from": tool_file(name),
            **(settings or {}),
        }
        check_builds(name, block, source)
        with app_file(library, "rw") as connection:
            before = store_tool(connection, name, block, source, allowed=may_write)
        done = "added" if before is None else "replaced"
        return logged(done, before, source, what="tool", name=name)

    tool = SimpleNamespace(
        show=show,
        write_decomposition=write_decomposition,
        add_namespace=add,
        change_namespace=change,
        write_tool=write_tool,
    )
    return Func(tool, description=LIBRARY_DESCRIPTION)
