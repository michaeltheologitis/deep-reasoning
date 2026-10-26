"""The Library: every namespace, decomposition and custom tool, and the run settings, in one SQLite file.

Each row holds the engine's own YAML, so the file turns back into a deep_reasoner config at run start.
"""

import ast
import inspect
import json
import sqlite3
import sys
from collections import defaultdict
from contextlib import closing, contextmanager
from pathlib import Path

import yaml
from deep_reasoner.config import load_cli_config
from deep_reasoner.namespaces import CONFIG_SOURCE, ROOT
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

SCHEMA_VERSION = 1
SCHEMA = (
    "CREATE TABLE settings (key TEXT PRIMARY KEY, yaml TEXT NOT NULL)",
    "CREATE TABLE namespaces (name TEXT PRIMARY KEY, yaml TEXT NOT NULL)",
    (
        "CREATE TABLE decompositions (namespace TEXT NOT NULL, name TEXT NOT NULL,"
        " yaml TEXT NOT NULL, PRIMARY KEY (namespace, name))"
    ),
    "CREATE TABLE tools (name TEXT PRIMARY KEY, yaml TEXT NOT NULL, source TEXT)",
)
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
# The run settings the panel always lists, with the engine's default when unset.
SHOWN_SETTINGS = ("max_iter", "max_depth", "entry_namespace", "repl")
LINE_WIDTH = 88
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


class LibraryError(ValueError):
    """Something the Library refused, in words for the person who asked."""


class BlockDumper(yaml.SafeDumper):
    """Writes multi-line text as | blocks, so stored YAML reads like the engine's configs."""


BlockDumper.add_representer(
    str,
    lambda dumper, text: dumper.represent_scalar(
        "tag:yaml.org,2002:str", text, style="|" if "\n" in text else None
    ),
)


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
    """The Library at *path*; a new file starts with a root namespace and the generic REPL prompt."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Autocommit: a read holds no lock once it has run; writes go through writing().
    connection = sqlite3.connect(path, isolation_level=None)
    try:
        if schema_version(connection) != SCHEMA_VERSION:
            lay_out(connection, path)
    except BaseException:
        connection.close()
        raise
    return connection


def lay_out(connection, path):
    """Write a new Library into an empty file, or refuse a file that already holds something else."""
    with writing(connection):
        # Read again under the lock: another process may have just laid it out.
        found = schema_version(connection)
        if found == SCHEMA_VERSION:
            return
        if found or connection.execute("SELECT 1 FROM sqlite_master").fetchone():
            raise LibraryError(
                f"{path} is not a Library this version of Deep Reasoning can open."
            )
        for statement in SCHEMA:
            connection.execute(statement)
        connection.execute(UPSERT_NAMESPACE, (ROOT, dump({})))
        settings = [(key, dump(value)) for key, value in DEFAULT_SETTINGS.items()]
        connection.executemany(UPSERT_SETTING, settings)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def tool_file(name):
    """A custom tool's file name; a Python name keeps it inside the folder it is written to."""
    if not name.isidentifier():
        raise LibraryError(f'Tool "{name}" needs a Python name, like "waitlist".')
    return f"{name}.py"


def stored_settings(connection):
    rows = connection.execute("SELECT key, yaml FROM settings ORDER BY rowid")
    return {key: yaml.safe_load(text) for key, text in rows if key not in CHATS_DECIDE}


def stored_config(connection):
    """The Library as a plain dict in the engine's config shape; a custom tool's factory_from names its stored file."""
    rows = connection.execute("SELECT name, yaml FROM tools ORDER BY rowid")
    tools = {name: yaml.safe_load(text) for name, text in rows}
    decompositions = defaultdict(list)
    rows = connection.execute(
        "SELECT namespace, yaml FROM decompositions ORDER BY rowid"
    )
    for namespace, text in rows:
        decompositions[namespace].append(yaml.safe_load(text))
    rows = connection.execute("SELECT name, yaml FROM namespaces ORDER BY rowid")
    namespaces = {
        name: {**yaml.safe_load(text), "decompositions": decompositions[name]}
        for name, text in rows
    }
    return {**stored_settings(connection), "tools": tools, "namespaces": namespaces}


def engine_config(library_path, namespace, tools_dir):
    """The Library as one plain dict that V2Config accepts, for a run that enters *namespace*;
    the run's model and client are the chat's to put in.

    Each custom tool's source is written into *tools_dir*, and its factory_from points at that file.
    """
    tools_dir = Path(tools_dir).resolve()
    tools_dir.mkdir(parents=True, exist_ok=True)
    with closing(open_library(library_path)) as connection:
        config = stored_config(connection)
        rows = connection.execute(
            "SELECT name, source FROM tools WHERE source IS NOT NULL"
        )
        sources = rows.fetchall()
    for name, source in sources:
        file = tools_dir / tool_file(name)
        file.write_text(source, encoding="utf-8")
        config["tools"][name]["factory_from"] = str(file)
    return config | {"entry_namespace": namespace}


def default_namespace(library_path):
    """Where a new chat starts: the run settings' entry_namespace, root unless one is set."""
    with closing(open_library(library_path)) as connection:
        return stored_settings(connection).get("entry_namespace", ROOT)


def check_namespace(connection, name):
    """Raise unless the Library has a namespace *name*."""
    found = connection.execute("SELECT 1 FROM namespaces WHERE name = ?", (name,))
    if not found.fetchone():
        raise LibraryError(
            f'The Library has no namespace "{name}"; pick one from the list.'
        )


def check(connection):
    """Raise unless the engine would accept the Library: every chain resolves and every tool granted exists."""
    config = V2Config.model_validate(stored_config(connection) | A_MODEL)
    build_namespace_registry(config).check(declared_tool_names(config))


def tool_row(name, block, config_dir):
    """A tool's row: its config block, and for a tool of your own its Python source."""
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
    # The engine adds a bare root when a config writes none; it must not blank the Library's.
    namespaces = [
        namespace
        for namespace in map(registry.config, registry.names)
        if namespace.name != ROOT or namespace.model_fields_set != {"name"}
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


def parsed(text):
    """The decomposition the YAML *text* describes, checked by the engine's own model."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f"line {mark.line + 1}: " if mark else ""
        reason = getattr(error, "problem", None) or error
        raise LibraryError(
            f"The YAML doesn't parse ({where}{reason}). Check the indentation and quoting on that line."
        ) from error
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
    check_namespace(connection, namespace)
    stored = {"namespace": namespace, "name": name, "yaml": text}
    try:
        with writing(connection):
            connection.execute(
                "INSERT INTO decompositions VALUES (?, ?, ?)", tuple(stored.values())
            )
    except sqlite3.IntegrityError as error:
        raise LibraryError(
            f'{namespace} already has "{name}"; rename it, or pick another namespace.'
        ) from error
    return stored


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


def tool_rows(config, registry, names, sources):
    rows = []
    for name in declared_tool_names(config):
        block = config.tools.get(name, {})
        factory = block.get("factory", name)
        source = sources.get(name)
        builtin = source is None
        description = block.get("description") or (
            BUILTIN_DESCRIPTIONS[factory] if builtin else class_docstring(source)
        )
        row = {
            "name": name,
            "factory": factory,
            "file": BUILDERS[factory].__module__ if builtin else block["factory_from"],
            "defined_in": None if builtin else "the Library",
            "granted_in": [
                each for each in names if name in registry.config(each).tools
            ],
            "description": description,
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
    namespaces = [
        {
            "name": name,
            "depth": len(registry.chain(name)) - 1,
            "fields": namespace_fields(registry, name, config),
            "decompositions": decompositions[name],
        }
        for name in names
    ]
    sources = dict(connection.execute("SELECT name, source FROM tools"))
    return {
        "default_namespace": config.entry_namespace,
        "run_settings": run_settings(connection),
        "namespaces": namespaces,
        "tools": tool_rows(config, registry, names, sources),
        "variables": variables(registry, names),
    }
