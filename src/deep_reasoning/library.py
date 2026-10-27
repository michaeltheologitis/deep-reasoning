"""The app file: the Library (every namespace, decomposition and custom tool, and the run
settings) in one SQLite file, which also holds the chats, their runs' events and the app's
own settings, so a copy of it carries the whole app but for the keys and the runs' working
folders.

Each Library row holds the engine's own YAML, so the file turns back into a deep_reasoner
config at run start. chats.py, runs.py and settings.py keep the chats, the runs' events and
the app's settings; this module lays the whole file out.
"""

import ast
import inspect
import json
import re
import sqlite3
import sys
from collections import defaultdict
from contextlib import closing, contextmanager
from pathlib import Path

import structlog
import yaml
from deep_reasoner.config import load_cli_config
from deep_reasoner.namespaces import CONFIG_SOURCE, ROOT, NamespaceConfig
from deep_reasoner.prompt_config import Decomposition
from deep_reasoner.tools import TOOL_BUILDERS
from deep_reasoner.tools.base import DEFAULT_CLAUDE_DESCRIPTION, DEFAULT_RAG_DESCRIPTION
from deep_reasoner.tools.kg_main import KnowledgeGraph
from deep_reasoner.tools.safe_url import DEFAULT_SAFE_URL_DESCRIPTION
from deep_reasoner.v2.cli import (
    _DEFAULT_LLM_DESCRIPTION,
    V2Config,
    build_llm_tool,
    build_namespace_registry,
    declared_tool_names,
)
from pydantic import ValidationError

log = structlog.get_logger()

SCHEMA_VERSION = 3
# Version 1 held the Library alone, and version 2 added the chats and the app's settings;
# a file of either opens and gains the tables of the versions after it.
LIBRARY_ONLY = 1
BEFORE_EVENTS = 2
LIBRARY_SCHEMA = (
    "CREATE TABLE settings (key TEXT PRIMARY KEY, yaml TEXT NOT NULL)",
    "CREATE TABLE namespaces (name TEXT PRIMARY KEY, yaml TEXT NOT NULL)",
    (
        "CREATE TABLE decompositions (namespace TEXT NOT NULL, name TEXT NOT NULL,"
        " yaml TEXT NOT NULL, PRIMARY KEY (namespace, name))"
    ),
    "CREATE TABLE tools (name TEXT PRIMARY KEY, yaml TEXT NOT NULL, source TEXT)",
)
LIBRARY_TABLES = {"settings", "namespaces", "decompositions", "tools"}
APP_TABLES = {"chats", "app_settings"}
# A chat's choices are null until picked or run, and a null folder is its scratch folder.
# app_settings is the app's, as JSON: the Library's own settings table is the run settings.
APP_SCHEMA = (
    (
        "CREATE TABLE chats (id TEXT PRIMARY KEY, title TEXT NOT NULL, created REAL NOT NULL,"
        " namespace TEXT, provider TEXT, model TEXT, folder TEXT)"
    ),
    "CREATE TABLE app_settings (key TEXT PRIMARY KEY, json TEXT NOT NULL)",
)
RUN_TABLES = {"runs", "events"}
# Each run's chat, and its events as the JSON the page folds, numbered from 1 (seq).
RUN_SCHEMA = (
    "CREATE TABLE runs (id TEXT PRIMARY KEY, chat TEXT NOT NULL)",
    "CREATE INDEX runs_by_chat ON runs (chat)",
    (
        "CREATE TABLE events (run TEXT NOT NULL, seq INTEGER NOT NULL, data TEXT NOT NULL,"
        " PRIMARY KEY (run, seq))"
    ),
)
# The tables each version added, and how.
ADDED_IN = {
    LIBRARY_ONLY: (LIBRARY_TABLES, LIBRARY_SCHEMA),
    BEFORE_EVENTS: (APP_TABLES, APP_SCHEMA),
    SCHEMA_VERSION: (RUN_TABLES, RUN_SCHEMA),
}
# Upserts keep a row's place, so decompositions stay in the order they were added.
UPSERT_SETTING = "INSERT INTO settings VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET yaml = excluded.yaml"
UPSERT_NAMESPACE = "INSERT INTO namespaces VALUES (?, ?) ON CONFLICT (name) DO UPDATE SET yaml = excluded.yaml"
UPSERT_DECOMPOSITION = (
    "INSERT INTO decompositions VALUES (?, ?, ?)"
    " ON CONFLICT (namespace, name) DO UPDATE SET yaml = excluded.yaml"
)
UPSERT_TOOL = (
    "INSERT INTO tools VALUES (?, ?, ?)"
    " ON CONFLICT (name) DO UPDATE SET yaml = excluded.yaml, source = excluded.source"
)
# Granted at root, so every namespace below has them, as in the engine's example configs.
FRESH_ROOT = {"tools": ["llm", "history"]}
# library writes the Library, so it is granted in a namespace of its own, which a chat
# picks when it wants edits, and which no namespace inherits from.
LIBRARIAN = "librarian"
LIBRARY_TOOL = "library"
FRESH_LIBRARIAN = {"tools": [LIBRARY_TOOL]}
UNTOUCHED_ROOT = (
    "name = :root AND yaml = :empty"
    " AND NOT EXISTS (SELECT 1 FROM decompositions WHERE namespace = :root)"
)
SYSTEM_PROMPT_FILE = Path(__file__).with_name("system_prompt.yaml")
DEFAULT_SETTINGS = yaml.safe_load(SYSTEM_PROMPT_FILE.read_text(encoding="utf-8"))
# Each chat picks its model, and the provider that serves it; a Library made before that
# may still hold these, which are left unread.
CHATS_DECIDE = {"model", "client"}
# Every run has one, so the Library is checked and shown as a run sees it: with the llm
# tool a model brings.
A_MODEL = {"model": "the chat's model"}
# Left to the Library, not a config: content (own tables), per-run paths, and the model and its key.
NOT_IMPORTED = {
    "namespaces",
    "namespaces_dir",
    "decompositions",
    "tools",
    "config_path",
    "task",
    "task_id",
    "run_prefix",
    "log_dir",
    "load_dotenv",
    "model",
    "planner_model",
    "models",
    "llm_kwargs",
    "client",
    "reasoner",
}
ENTRY_NAMESPACE = "entry_namespace"
# The run settings the panel always lists, with the engine's default when unset.
SHOWN_SETTINGS = ("max_iter", "max_depth", ENTRY_NAMESPACE, "repl")
LINE_WIDTH = 88
NEL = "\x85"
ROLES = "user, assistant or system"
# make_tool builds `factory: llm` with v2's own builder, the rest from TOOL_BUILDERS.
BUILDERS = {**TOOL_BUILDERS, "llm": build_llm_tool}
BUILTIN_DESCRIPTIONS = {
    "llm": _DEFAULT_LLM_DESCRIPTION,
    "rag": DEFAULT_RAG_DESCRIPTION,
    "kg": inspect.getdoc(KnowledgeGraph),
    "safe_url": DEFAULT_SAFE_URL_DESCRIPTION,
    "claude_code": DEFAULT_CLAUDE_DESCRIPTION,
}
HISTORY_DESCRIPTION = """\
The `history` tool reads this chat's earlier messages and how you worked out each one, so \
you can explain your earlier reasoning. Its methods return plain data (lists of dicts): \
slice it in Python and print only what you need.
  history.turns(): the earlier messages, numbered from 1 as the chat's recap numbers them: \
turn, message, namespace, model, outcome, answer, detail, cost, seconds and agents (how \
many sub-agents it ran).
  history.agents(turn): each sub-agent drive of message number `turn`: node, parent, \
drive, task, namespace, status, result, cost (its own sub-agents' included) and steps \
(how many).
  history.steps(turn, node=None): the thoughts and cells, in order, of message `turn`'s \
top agent, or of the sub-agent whose node is `node`: {kind: "think", text} or \
{kind: "cell", code, output, status, agents: the nodes of the sub-agents it started}, \
each with its drive."""
LIBRARY_DESCRIPTION = """\
The `library` tool reads and writes the app's Library: its namespaces and the \
decompositions (worked examples) each one's agents are shown. A change applies from the \
user's next message, not in this run, and only a chat whose namespace grants this tool may \
make one. root is locked: you may read it, not write it.
  library.show(): every namespace, as plain data (a list of dicts): name, depth, yaml \
(the fields it sets itself), fields (each as the engine resolves it, with where it comes \
from) and decompositions (each with its name and yaml). Slice it in Python and print \
only what you need.
  library.write_decomposition(namespace, yaml): adds the decomposition written as YAML \
(a name: line, then messages:, a list of turns, each with a role and content) to \
namespace `namespace`, or replaces the one of that name there. Returns what it did: \
{done: "added" or "replaced", what, name, namespace}. A refusal raises ValueError saying \
why."""
# Added in code, never stored: a shared file mustn't choose the code they run.
APP_TOOLS_FILE = Path(__file__).with_name("app_tools.py")
APP_TOOLS = {
    "history": {"factory_from": str(APP_TOOLS_FILE), "factory": "build_history"},
    LIBRARY_TOOL: {"factory_from": str(APP_TOOLS_FILE), "factory": "build_library"},
}
APP_TOOL_DESCRIPTIONS = {
    "history": HISTORY_DESCRIPTION,
    LIBRARY_TOOL: LIBRARY_DESCRIPTION,
}
APP_TOOLS_MODULE = f"{__package__}.{APP_TOOLS_FILE.stem}"
APP = "Deep Reasoning"
# A new namespace's name, from the page: plain words, joined by dots for a child.
NAMESPACE_NAME = re.compile(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*")
NAME_IT = 'Name the namespace, like "research"; "research.papers" goes under research.'
NAME_SHAPE = (
    "A namespace name is words of letters, digits, _ and -, joined by dots,"
    ' like "research.papers".'
)
# What a namespace's YAML leaves to the panel: its name field, and the Decompositions tab.
NAMED_ELSEWHERE = {
    "name": 'Remove "name": a namespace is named in the name field, not in its YAML.',
    "decompositions": (
        'Remove "decompositions": a namespace\'s decompositions are added'
        " in the Decompositions tab."
    ),
}
NAMESPACE_KEYS = [
    key for key in NamespaceConfig.model_fields if key not in NAMED_ELSEWHERE
]
NAMESPACE_HOLDS = f"{', '.join(NAMESPACE_KEYS[:-1])} and {NAMESPACE_KEYS[-1]}"
SHAPES = {
    "tools": 'tools should be a list of tool names, like "tools: [llm]".',
    "spawn": 'spawn should be a list of namespace names, like "spawn: [research]", or [] for none.',
    "vars": 'vars should be a mapping of names to values, like "vars: {year: 2026}".',
    "system_suffix": 'system_suffix should be text; write "system_suffix: |" with the text indented below.',
    "reasoner": 'reasoner should be a mapping, like "reasoner: {type: claude_code}".',
}
# How a namespace that sets nothing is kept by an import, or a Library made before
# FRESH_ROOT; the panel saves one as blank text, so a root saved blank is never upgraded.
EMPTY_NAMESPACE = "{}\n"


class LibraryError(ValueError):
    """Something the Library refused, in words for the person who asked."""


class BlockDumper(yaml.SafeDumper):
    """Writes multi-line text as | blocks (text holding a NEL double-quoted), so stored YAML reads like the engine's configs."""


def represent_text(dumper, text):
    # PyYAML escapes a NEL only in double quotes, and reads a raw one as a line break.
    style = '"' if NEL in text else "|" if "\n" in text else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", text, style=style)


BlockDumper.add_representer(str, represent_text)


def dump(value):
    return yaml.dump(
        value, Dumper=BlockDumper, sort_keys=False, allow_unicode=True, width=LINE_WIDTH
    )


def flow(value):
    one_line = yaml.safe_dump(
        value,
        default_flow_style=True,
        sort_keys=False,
        allow_unicode=True,
        width=sys.maxsize,
    )
    return one_line.strip()


@contextmanager
def writing(connection):
    """One transaction that takes the write lock up front, so concurrent writers wait their turn instead of failing."""
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        yield


def schema_version(connection):
    return connection.execute("PRAGMA user_version").fetchone()[0]


def open_library(path):
    """The Library at *path*; a new file starts with a root namespace granting llm and the generic REPL prompt."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Autocommit: a read holds no lock once it has run; writes go through writing().
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        # Deleted rows are wiped, not left in free pages that a copy would carry.
        connection.execute("PRAGMA secure_delete = ON")
        distrust(connection)
        if schema_version(connection) != SCHEMA_VERSION:
            lay_out(connection, path)
        freshen_an_untouched_root(connection)
    except BaseException:
        connection.close()
        raise
    return connection


def distrust(connection):
    """Never run the file's own triggers and views: a shared file's could keep what is deleted."""
    connection.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_TRIGGER, False)
    connection.setconfig(sqlite3.SQLITE_DBCONFIG_ENABLE_VIEW, False)


def lay_out(connection, path):
    """Write the whole app file into an empty file, or add what a file of an earlier version
    lacks, keeping what it holds; refuse, untouched, a file that holds anything else."""
    with writing(connection):
        # Read again under the lock: another process may have just laid it out.
        found = schema_version(connection)
        if found == SCHEMA_VERSION:
            return
        names = {
            name for (name,) in connection.execute("SELECT name FROM sqlite_master")
        }
        if not written_by_an_earlier_version(found, names):
            raise LibraryError(
                f"{path} is not a Library this version of Deep Reasoning can open."
            )
        versions = range(found + 1, SCHEMA_VERSION + 1)
        added = [each for version in versions for each in ADDED_IN[version][1]]
        for statement in added:
            connection.execute(statement)
        if found == 0:
            seed_new_library(connection)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def written_by_an_earlier_version(found, names):
    """Whether a file at version *found*, holding *names*, is empty or one an earlier
    version wrote: every table of its version, and none of a later one's."""
    if found == 0:
        return not names
    return 0 < found < SCHEMA_VERSION and all(
        tables <= names if version <= found else not tables & names
        for version, (tables, _) in ADDED_IN.items()
    )


def seed_new_library(connection):
    connection.execute(UPSERT_NAMESPACE, (ROOT, dump(FRESH_ROOT)))
    connection.execute(UPSERT_NAMESPACE, (LIBRARIAN, dump(FRESH_LIBRARIAN)))
    settings = [(key, dump(value)) for key, value in DEFAULT_SETTINGS.items()]
    connection.executemany(UPSERT_SETTING, settings)


def freshen_an_untouched_root(connection):
    """Give a Library made with an empty root the root a new one starts with."""
    parameters = {"root": ROOT, "empty": dump({}), "fresh": dump(FRESH_ROOT)}
    found = connection.execute(
        f"SELECT 1 FROM namespaces WHERE {UNTOUCHED_ROOT}", parameters
    )
    if not found.fetchone():
        return
    try:
        with writing(connection):
            connection.execute(
                f"UPDATE namespaces SET yaml = :fresh WHERE {UNTOUCHED_ROOT}",
                parameters,
            )
    except sqlite3.OperationalError as error:
        # A file it can't write, such as a read-only copy, still opens as it is.
        log.warning("library.root_not_upgraded", error=str(error))


def tool_file(name):
    """A custom tool's file name; a Python name keeps it inside the folder it is written to."""
    if not name.isidentifier():
        raise LibraryError(f'Tool "{name}" needs a Python name, like "waitlist".')
    return f"{name}.py"


def stored_settings(connection):
    rows = connection.execute("SELECT key, yaml FROM settings ORDER BY rowid")
    return {key: yaml.safe_load(text) for key, text in rows if key not in CHATS_DECIDE}


def library_tools(connection):
    """The Library's own tools, each as its name, YAML and source. A row under an app
    tool's name, as a shared file may hold, is left out: the app's own takes its place."""
    rows = connection.execute("SELECT name, yaml, source FROM tools ORDER BY rowid")
    tools = []
    for name, text, source in rows:
        if name in APP_TOOLS:
            log.warning("library.tool_shadowed", tool=name)
            continue
        tools.append((name, text, source))
    return tools


def stored_config(connection):
    """The Library as a plain dict in the engine's config shape, the app's tools after its
    own; a custom tool's factory_from names its stored file."""
    tools = {name: yaml.safe_load(text) for name, text, _ in library_tools(connection)}
    tools |= {name: dict(block) for name, block in APP_TOOLS.items()}
    decompositions = defaultdict(list)
    rows = connection.execute(
        "SELECT namespace, yaml FROM decompositions ORDER BY rowid"
    )
    for namespace, text in rows:
        decompositions[namespace].append(yaml.safe_load(text))
    rows = connection.execute("SELECT name, yaml FROM namespaces ORDER BY rowid")
    namespaces = {
        name: {**(yaml.safe_load(text) or {}), "decompositions": decompositions[name]}
        for name, text in rows
    }
    return {**stored_settings(connection), "tools": tools, "namespaces": namespaces}


def engine_config(library_path, namespace, tools_dir, chat, run):
    """The Library as one plain dict that V2Config accepts, for run *run* of *chat*, which
    enters *namespace*; the run's model and client are the chat's to put in.

    Each custom tool's source is written into *tools_dir*, and its factory_from points at that file.
    Each of the app's tools is told the app file, the chat, the run and the namespace it enters.
    """
    tools_dir = Path(tools_dir).resolve()
    tools_dir.mkdir(parents=True, exist_ok=True)
    with closing(open_library(library_path)) as connection:
        config = stored_config(connection)
        tools = library_tools(connection)
    sources = [(name, source) for name, _, source in tools if source is not None]
    for name, source in sources:
        file = tools_dir / tool_file(name)
        file.write_text(source, encoding="utf-8")
        config["tools"][name]["factory_from"] = str(file)
    told = {
        "library": str(Path(library_path).resolve()),
        "chat": chat,
        "run": run,
        "namespace": namespace,
    }
    for name in APP_TOOLS:
        config["tools"][name] |= told
    return config | {"entry_namespace": namespace}


def default_namespace(library_path):
    """Where a new chat starts: the run settings' entry_namespace, root unless one is set."""
    with closing(open_library(library_path)) as connection:
        return stored_settings(connection).get(ENTRY_NAMESPACE, ROOT)


def has_namespace(connection, name):
    found = connection.execute("SELECT 1 FROM namespaces WHERE name = ?", (name,))
    return found.fetchone() is not None


def check_namespace(connection, name):
    """Raise unless the Library has a namespace *name*."""
    if not has_namespace(connection, name):
        raise LibraryError(
            f'The Library has no namespace "{name}"; pick one from the list.'
        )


def granted_tools(connection, namespace):
    """The tools *namespace* has, its own and its chain's, as the engine resolves them."""
    config = V2Config.model_validate(stored_config(connection) | A_MODEL)
    return build_namespace_registry(config).resolve(namespace).tools


def check(connection):
    """Raise unless the engine would accept the Library: every chain resolves and every tool granted exists."""
    config = V2Config.model_validate(stored_config(connection) | A_MODEL)
    build_namespace_registry(config).check(declared_tool_names(config))


def tool_row(name, block, config_dir):
    """A tool's row: its config block, and for a tool of your own its Python source."""
    if name in APP_TOOLS:
        raise LibraryError(
            f'Tool "{name}" has the name of one of the app\'s own tools; rename yours.'
        )
    factory = block.get("factory", name)
    factory_from = block.get("factory_from")
    if not isinstance(factory, str) or not isinstance(factory_from, str | None):
        raise LibraryError(f'Tool "{name}": factory and factory_from should be text.')
    if factory_from is None:
        if factory not in BUILDERS:
            raise LibraryError(
                f'Tool "{name}" names factory "{factory}", which is not built in; '
                "give its block a factory_from: file."
            )
        if factory == "llm":
            # It runs on the chat's model, as the chat does; the config's model or preset may not exist there.
            block = {key: value for key, value in block.items() if key != "model"}
        return name, dump(block), None
    stored_file = tool_file(name)
    file = config_dir / factory_from
    source = file.read_text(encoding="utf-8")
    try:
        ast.parse(source, filename=str(file))
    except SyntaxError as error:
        raise LibraryError(
            f"{file} is not valid Python (line {error.lineno}: {error.msg})."
        ) from error
    return name, dump({**block, "factory_from": stored_file}), source


def store_decompositions(connection, namespace, decompositions):
    rows = [(namespace, each.name, dump(each.model_dump())) for each in decompositions]
    connection.executemany(UPSERT_DECOMPOSITION, rows)


def import_config(connection, path):
    """Read the deep_reasoner config at *path* into the Library, replacing same-named items.

    It takes the config's namespaces (inline and from its namespaces_dir) with their
    decompositions, its tools with the Python files their factory_from: names, and its run
    settings but for the model and how to reach it. Top-level decompositions are left out:
    with namespaces they are only `dr --main-decomposition` openings, which a chat has none of.
    All of it lands, or none.
    """
    config = load_cli_config(path, schema=V2Config)
    registry = build_namespace_registry(config)
    settings = config.model_dump(exclude_unset=True, exclude=NOT_IMPORTED)
    tools = [
        tool_row(name, block, config.config_dir) for name, block in config.tools.items()
    ]
    # A root that sets nothing, like the bare one the engine adds, must not blank the Library's.
    namespaces = [
        namespace
        for namespace in map(registry.config, registry.names)
        if namespace.name != ROOT
        or namespace.decompositions
        or namespace.model_fields_set - {"name", "decompositions"}
    ]
    with writing(connection):
        connection.executemany(
            UPSERT_SETTING, [(k, dump(v)) for k, v in settings.items()]
        )
        connection.executemany(UPSERT_TOOL, tools)
        for namespace in namespaces:
            own = namespace.model_dump(
                exclude_unset=True, exclude={"name", "decompositions"}
            )
            connection.execute(UPSERT_NAMESPACE, (namespace.name, dump(own)))
            store_decompositions(connection, namespace.name, namespace.decompositions)
        check(connection)
    return {
        "namespaces": len(namespaces),
        "decompositions": sum(len(each.decompositions) for each in namespaces),
        "tools": len(tools),
    }


def problem(error):
    """One of the Decomposition model's validation errors, as the panel words it."""
    match error["loc"], error["type"]:
        case (key,), "extra_forbidden":
            return f'Remove "{key}": only name and messages go in the YAML; pick the namespace below.'
        case ("name",), "missing":
            return 'Add a name: line, like "name: count the open tickets".'
        case ("name",), _:
            return 'The name should be text, like "name: count the open tickets".'
        case ("messages",), "missing":
            return "Add messages: a list of turns, each with a role and content, as in the template."
        case ("messages",), _:
            return 'messages should be a list of at least one turn, each starting "- role:".'
        case ("messages", int(index)), _:
            return f"Message {index + 1} should be a mapping with role and content."
        case ("messages", int(index), key), "extra_forbidden":
            return f'Message {index + 1}: remove "{key}"; a message holds only role and content.'
        case ("messages", int(index), "role"), "missing":
            return f"Message {index + 1}: role should be {ROLES}."
        case ("messages", int(index), "role"), _:
            given = json.dumps(error["input"], default=str)
            return f"Message {index + 1}: role should be {ROLES}, not {given}."
        case ("messages", int(index), "content"), "missing":
            return f"Message {index + 1} needs content: the turn's text."
        case ("messages", int(index), "content"), _:
            return f'Message {index + 1}: content should be text; quote it, or write "content: |" with the text indented below.'
    return f"{'.'.join(map(str, error['loc']))}: {error['msg']}."


def loaded(text):
    """The YAML *text* as data, or a LibraryError saying where it doesn't parse."""
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f"line {mark.line + 1}: " if mark else ""
        reason = getattr(error, "problem", None) or error
        raise LibraryError(
            f"The YAML doesn't parse ({where}{reason}). Check the indentation and quoting on that line."
        ) from error


def parsed(text):
    """The decomposition the YAML *text* describes, checked by the engine's own model."""
    data = loaded(text)
    if not isinstance(data, dict):
        raise LibraryError(
            "The YAML should be a mapping: a name: line, then messages:, as in the template."
        )
    try:
        decomposition = Decomposition.model_validate(data)
    except ValidationError as error:
        raise LibraryError("\n".join(map(problem, error.errors()))) from error
    if not decomposition.name.strip():
        raise LibraryError(
            'The name should be text, like "name: count the open tickets".'
        )
    return decomposition


def add_decomposition(connection, namespace, text):
    """Store the decomposition written as YAML *text* under *namespace*, or raise LibraryError saying why not."""
    name = parsed(text).name
    stored = {"namespace": namespace, "name": name, "yaml": text}
    try:
        with writing(connection):
            # Under the lock, so a namespace deleted meanwhile leaves no decomposition behind.
            check_namespace(connection, namespace)
            connection.execute(
                "INSERT INTO decompositions VALUES (?, ?, ?)", tuple(stored.values())
            )
    except sqlite3.IntegrityError as error:
        raise LibraryError(
            f'{namespace} already has "{name}"; rename it, or pick another namespace.'
        ) from error
    return stored


def save_decomposition(connection, namespace, text):
    """Store the decomposition written as YAML *text* under *namespace*, replacing the one
    of its name there; its name, and the YAML it replaced (None when it is new). Raise
    LibraryError saying why not."""
    name = parsed(text).name
    with writing(connection):
        check_namespace(connection, namespace)
        found = connection.execute(
            "SELECT yaml FROM decompositions WHERE namespace = ? AND name = ?",
            (namespace, name),
        ).fetchone()
        connection.execute(UPSERT_DECOMPOSITION, (namespace, name, text))
    return name, None if found is None else found[0]


def namespace_problem(error):
    """One of the NamespaceConfig model's validation errors, as the panel words it."""
    match error["loc"], error["type"]:
        case (key,), "extra_forbidden":
            return f'Remove "{key}": a namespace\'s YAML holds only {NAMESPACE_HOLDS}.'
        case (str(key), *_), _ if key in SHAPES:
            return SHAPES[key]
    return f"{'.'.join(map(str, error['loc']))}: {error['msg']}."


def authored(name, text):
    """Namespace *name* as its YAML *text* describes it, checked by the engine's own model,
    and the YAML to store for it."""
    data = loaded(text)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise LibraryError(
            'The YAML should be a mapping of fields, like "tools: [llm]".'
        )
    problems = [NAMED_ELSEWHERE[key] for key in NAMED_ELSEWHERE if key in data]
    fields = {key: value for key, value in data.items() if key not in NAMED_ELSEWHERE}
    try:
        namespace = NamespaceConfig.model_validate(fields | {"name": name})
    except ValidationError as error:
        problems += map(namespace_problem, error.errors())
        raise LibraryError("\n".join(problems)) from error
    if problems:
        raise LibraryError("\n".join(problems))
    # As typed, comments and all, but for the one text an untouched root is kept as.
    return namespace, "" if text == EMPTY_NAMESPACE else text


def accepted(connection):
    """Raise unless the engine accepts the Library, in words for the panel."""
    try:
        check(connection)
    except ValueError as error:
        raise LibraryError(f"The engine refuses it: {error}") from error


def write_namespace(connection, namespace, text):
    """Store *namespace* as its YAML *text*, inside a transaction that keeps it only if
    every namespace it may spawn into is there and the engine accepts the Library."""
    connection.execute(UPSERT_NAMESPACE, (namespace.name, text))
    # The engine lets a spawn name no namespace, and fails only when the agent spawns there.
    missing = [
        each for each in namespace.spawn or [] if not has_namespace(connection, each)
    ]
    if missing:
        raise LibraryError(
            "\n".join(
                f'spawn names "{each}", which is not a namespace in the Library.'
                for each in missing
            )
        )
    accepted(connection)


def add_namespace(connection, name, text):
    """Store a new namespace *name* with the fields its YAML *text* gives, or raise
    LibraryError saying why not. Its decompositions are added afterwards."""
    if not name:
        raise LibraryError(NAME_IT)
    if not NAMESPACE_NAME.fullmatch(name):
        raise LibraryError(NAME_SHAPE)
    namespace, stored = authored(name, text)
    parent = name.rpartition(".")[0]
    with writing(connection):
        if has_namespace(connection, name):
            raise LibraryError(
                f'There is already a namespace "{name}"; open it and use Edit YAML.'
            )
        if parent and not has_namespace(connection, parent):
            raise LibraryError(
                f'Add namespace "{parent}" first: "{name}" goes under it.'
            )
        write_namespace(connection, namespace, stored)


def change_namespace(connection, name, text):
    """Give namespace *name* the fields its YAML *text* gives in place of its own, keeping
    its decompositions, or raise LibraryError saying why not."""
    namespace, stored = authored(name, text)
    with writing(connection):
        check_namespace(connection, name)
        write_namespace(connection, namespace, stored)


def delete_namespace(connection, name, decompositions):
    """Delete namespace *name* and its decompositions, as many as the caller was told it
    has, or raise LibraryError saying why not; if new chats started there, they start in root."""
    if name == ROOT:
        raise LibraryError("root can't be deleted: every namespace inherits from it.")
    with writing(connection):
        check_namespace(connection, name)
        rows = connection.execute("SELECT name, yaml FROM namespaces")
        namespaces = {each: yaml.safe_load(text) or {} for each, text in rows}
        children = [each for each in namespaces if each.startswith(f"{name}.")]
        if children:
            raise LibraryError(f"Delete its namespaces first: {', '.join(children)}.")
        # Else their spawn would name no namespace, which write_namespace refuses.
        spawners = [
            each
            for each, fields in namespaces.items()
            if each != name and name in (fields.get("spawn") or [])
        ]
        if spawners:
            raise LibraryError(
                f"First take {name} out of the spawn of {', '.join(spawners)}:"
                " they may spawn into it."
            )
        held = connection.execute(
            "SELECT count(*) FROM decompositions WHERE namespace = ?", (name,)
        ).fetchone()[0]
        if held != decompositions:
            raise LibraryError(
                f"{name} has {count(held, 'decomposition')} now, not {decompositions};"
                " look again before deleting it."
            )
        connection.execute("DELETE FROM decompositions WHERE namespace = ?", (name,))
        connection.execute("DELETE FROM namespaces WHERE name = ?", (name,))
        if stored_settings(connection).get(ENTRY_NAMESPACE) == name:
            connection.execute("DELETE FROM settings WHERE key = ?", (ENTRY_NAMESPACE,))
        accepted(connection)


def shown(value):
    if isinstance(value, dict | list):
        return flow(value)
    return "not set" if value is None else str(value)


def repl_text(repl):
    return flow(
        {"type": repl.type, **repl.model_dump(mode="json", exclude_defaults=True)}
    )


def count(number, noun):
    return f"{number} {noun}{'' if number == 1 else 's'}"


def cell(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    if isinstance(value, dict):
        return flow(value)[1:-1]
    return "" if value is None else str(value).strip()


def table(value):
    """A var that is records (a list of mappings, or mappings keyed by id) as columns and rows, else None."""
    if (
        isinstance(value, dict)
        and value
        and all(isinstance(row, dict) for row in value.values())
    ):
        value = [{"id": key, **row} for key, row in value.items()]
    if not (
        isinstance(value, list)
        and value
        and all(isinstance(row, dict) for row in value)
    ):
        return None
    columns = list(dict.fromkeys(key for row in value for key in row))
    return {
        "columns": columns,
        "rows": [[cell(row.get(column)) for column in columns] for row in value],
    }


def var_summary(value):
    rows = table(value)
    return count(len(rows["rows"]), "row") if rows else shown(value)


def located(value, level, namespace, verb="set"):
    """A namespace's value, and the level of its chain it comes from."""
    here = level == namespace
    source = f"{verb} here" if here else f"inherited from {level}"
    return {"value": value, "source": source, "here": here}


def backbone(resolved, run):
    if resolved.reasoner is not None:
        return located(
            shown(resolved.reasoner), resolved.sources.reasoner, resolved.name
        )
    if run.reasoner:
        return {"value": shown(run.reasoner), "source": "from the run settings"}
    return {"value": "chat", "source": "the run's default"}


def namespace_fields(registry, name, run):
    """Each field of namespace *name* as the engine resolves it, with where it comes from."""
    resolved = registry.resolve(name)
    sources = resolved.sources
    repl = repl_text(resolved.repl)
    if sources.repl == CONFIG_SOURCE:
        repl_item = {"value": repl, "source": "from the run settings"}
    else:
        repl_item = located(repl, sources.repl, name)
    if resolved.spawn is None:
        spawn = {"value": "any namespace", "source": "not set"}
    else:
        spawn = located(
            ", ".join(resolved.spawn) or "nowhere: a leaf", sources.spawn, name
        )
    tools = [
        located(tool, sources.tools[tool], name, "granted") for tool in resolved.tools
    ]
    variables = [
        located(f"{key} ({var_summary(value)})", sources.vars[key], name)
        for key, value in resolved.vars.items()
    ]
    suffixes = [
        located(registry.config(level).system_suffix.strip(), level, name)
        for level in sources.system_suffix
    ]
    return [
        {"label": "REPL", "items": [repl_item]},
        {"label": "Backbone", "items": [backbone(resolved, run)]},
        {"label": "May spawn into", "items": [spawn]},
        {"label": "Tools", "items": tools},
        {"label": "Variables", "items": variables},
        {"label": "System suffix", "items": suffixes},
    ]


def run_settings(connection):
    stored = stored_settings(connection)
    defaults = V2Config().model_dump(mode="json")
    rows = []
    for key in dict.fromkeys([*SHOWN_SETTINGS, *stored]):
        source = "set in the Library" if key in stored else "the engine's default"
        value = shown(stored.get(key, defaults.get(key)))
        rows.append({"label": key, "items": [{"value": value, "source": source}]})
    return rows


def class_docstring(source):
    """The first class's docstring: what the agent is told when a factory returns one and gives no description."""
    classes = [
        node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)
    ]
    return (ast.get_docstring(classes[0]) if classes else None) or ""


def origin(name, factory, block, source):
    """Where a tool comes from, as the panel shows it, and what the agent is told it does
    unless its block says."""
    if name in APP_TOOLS:
        made = {"file": APP_TOOLS_MODULE, "defined_in": APP, "badge": "the app's"}
        return made, APP_TOOL_DESCRIPTIONS[name]
    if source is None:
        made = {
            "file": BUILDERS[factory].__module__,
            "defined_in": None,
            "badge": "built-in",
        }
        return made, BUILTIN_DESCRIPTIONS[factory]
    made = {"file": block["factory_from"], "defined_in": "the Library", "badge": None}
    return made, class_docstring(source)


def tool_rows(config, registry, names, sources):
    rows = []
    for name in declared_tool_names(config):
        block = config.tools.get(name, {})
        factory = block.get("factory", name)
        made, description = origin(name, factory, block, sources.get(name))
        row = {
            "name": name,
            "factory": factory,
            **made,
            "granted_in": [
                each for each in names if name in registry.config(each).tools
            ],
            "description": block.get("description") or description,
            "config": dump({name: block}).rstrip() if block else None,
        }
        rows.append(row)
    return rows


def variables(registry, names):
    """Each namespace's own vars that are tables, for the Data tab."""
    tables = [
        (key, name, table(value))
        for name in names
        for key, value in registry.config(name).vars.items()
    ]
    return [
        {"name": key, "where": name, "summary": shape(rows)} | rows
        for key, name, rows in tables
        if rows
    ]


def shape(rows):
    return (
        f"{count(len(rows['rows']), 'row')} · {count(len(rows['columns']), 'column')}"
    )


def panel(connection):
    """What the Library panel shows: run settings, namespaces as the engine resolves them, tools, tabular vars."""
    config = V2Config.model_validate(stored_config(connection) | A_MODEL)
    registry = build_namespace_registry(config)
    names = sorted(registry.names, key=registry.chain)
    decompositions = defaultdict(list)
    rows = connection.execute(
        "SELECT namespace, name, yaml FROM decompositions ORDER BY rowid"
    )
    for namespace, name, text in rows:
        decompositions[namespace].append({"name": name, "yaml": text})
    # What each one's Edit YAML opens on: blank for a namespace that sets nothing.
    rows = connection.execute("SELECT name, yaml FROM namespaces")
    own = {name: "" if text == EMPTY_NAMESPACE else text for name, text in rows}
    namespaces = [
        {
            "name": name,
            "depth": len(registry.chain(name)) - 1,
            "fields": namespace_fields(registry, name, config),
            "decompositions": decompositions[name],
            "yaml": own.get(name, ""),
        }
        for name in names
    ]
    sources = {name: source for name, _, source in library_tools(connection)}
    return {
        "default_namespace": config.entry_namespace,
        "run_settings": run_settings(connection),
        "namespaces": namespaces,
        "tools": tool_rows(config, registry, names, sources),
        "variables": variables(registry, names),
    }
