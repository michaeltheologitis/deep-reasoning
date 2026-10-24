"""Build the prototype's mock Library from deep_reasoner's example configs.

Writes prototype/data/library.json. Run from the repo root:
uv run --with pyyaml python scripts/mock_library.py [ENGINE_CHECKOUT, default ../deep_reasoner_beta]
"""

import ast
import json
import re
import sys
import textwrap
from pathlib import Path

import yaml

ENGINE = Path(sys.argv[1] if len(sys.argv) > 1 else "../deep_reasoner_beta")
OUT = Path(__file__).resolve().parents[1] / "prototype" / "data" / "library.json"
ROOT = "root"
REVISION = 14
# The configs the Library is made of, and the namespace each one's `root` becomes:
# "root" shares it, None keeps only its decompositions, unattached. The first config's
# run settings are the Library's.
SOURCES = {
    "docs/configs/catalog/advisors.yaml": ROOT,
    "docs/configs/catalog/llm_tool.yaml": ROOT,
    "docs/configs/catalog/namespaces_dir.yaml": ROOT,
    "docs/configs/examples/cruncher/cruncher.yaml": ROOT,
    "docs/configs/examples/experience/experience.yaml": ROOT,
    "docs/configs/catalog/kg_agent.yaml": "kg_agent",
    "docs/configs/examples/waitlist/waitlist.yaml": "waitlist",
    "docs/configs/catalog/kg_query.yaml": None,
    "docs/configs/incidents/triage.yaml": ROOT,
}
# MainConfig's defaults, deep_reasoner/config.py
RUN_DEFAULTS = {
    "model": None,
    "max_iter": 30,
    "max_depth": 8,
    "entry_namespace": ROOT,
    "repl": {"type": "local"},
}
# Where each built-in factory's agent-facing description lives: a constant or a class.
BUILTINS = {
    "llm": ("deep_reasoner/tools/base.py", "DEFAULT_LLM_DESCRIPTION"),
    "rag": ("deep_reasoner/tools/base.py", "DEFAULT_RAG_DESCRIPTION"),
    "kg": ("deep_reasoner/tools/kg_main.py", "KnowledgeGraph"),
    "safe_url": ("deep_reasoner/tools/safe_url.py", "DEFAULT_SAFE_URL_DESCRIPTION"),
    "claude_code": ("deep_reasoner/tools/base.py", "DEFAULT_CLAUDE_DESCRIPTION"),
}
# The Library's own fields, which no config holds: mock.
USE_WHEN = {
    "full_triage": ("the incidents' rule is fixed, so code alone answers", "the task"),
    "survey_only": ("gather the incidents, then let the model decide", "the task"),
    "triage the TA inbox": ("a gist for many messages, a review for any code", None),
    "route a course question": ("a question about courses or the catalog", None),
    "route a wellbeing question": ("a student asks for wellbeing advice", None),
    "decline anything else": ("neither courses nor wellbeing", None),
    "catalog lookup": ("one course at a time", "the course question"),
    "answer then sanitize": ("advice that must stay non-clinical", "the question"),
    "delegate the crunch": ("number-crunching over the dataset", None),
    "crunch the sales with pandas": ("aggregates over the `sales` table", None),
    "parse a drug label into the graph": ("a new document to add as facts", "the text"),
    "answer with a cited proof": ("a question whose answer needs its source", None),
}
VERSIONS = {"catalog lookup": 2, "answer then sanitize": 3, "code_reviewer": 2}
THINK = re.compile(r"<think>(.*?)</think>", re.DOTALL)
CODE = re.compile(r"<repl>(.*?)</repl>", re.DOTALL)
OBSERVATION = re.compile(r"<observation>(.*?)</observation>", re.DOTALL)


def literal_block(dumper, text):
    style = "|" if "\n" in text else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", text, style=style)


yaml.add_representer(str, literal_block, Dumper=yaml.SafeDumper)


def read(path):
    return yaml.safe_load(path.read_text()) or {}


def dump(value):
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=88)


def flow(value):
    one_line = yaml.safe_dump(
        value, default_flow_style=True, sort_keys=False, width=sys.maxsize
    )
    return one_line.strip()


def count(number, noun):
    return f"{number} {noun}{'' if number == 1 else 's'}"


def described(path, name):
    """The constant *name* in *path*, or the docstring of its class *name* (None: the first)."""
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.ClassDef) and name in (None, node.name):
            return ast.get_docstring(node)
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            return ast.literal_eval(node.value)
    raise LookupError(f"{name} is not in {path}")


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def chain(name):
    """[root, ..., name]: the levels a namespace inherits along."""
    parts = [] if name == ROOT else name.split(".")
    return [ROOT] + [".".join(parts[: i + 1]) for i in range(len(parts))]


def own_namespaces(path, data):
    found = dict(data.get("namespaces") or {})
    if "namespaces_dir" in data:
        folder = path.parent / data["namespaces_dir"]
        names = {
            ".".join(f.relative_to(folder).with_suffix("").parts): f
            for f in folder.rglob("*.yaml")
        }
        for name in sorted(names, key=lambda name: (name.count("."), name)):
            found[name] = read(names[name])
    return found


def merge(into, level):
    """Lay one config's namespace over the Library's one of the same name."""
    for key, value in level.items():
        if key == "tools":
            into["tools"] = list(dict.fromkeys(into.get("tools", []) + value))
        elif key == "decompositions":
            into["decompositions"] = into.get("decompositions", []) + value
        elif key == "vars":
            into["vars"] = into.get("vars", {}) | value
        else:
            into.setdefault(key, value)


def composed(path):
    """Each file of a config, the ones it composes first."""
    data = read(path)
    for name in data.get("_compose", []):
        yield from composed(path.parent / name)
    yield path, data


def run_settings(path):
    settings = {key: (value, "default") for key, value in RUN_DEFAULTS.items()}
    for file, data in composed(path):
        for key in settings.keys() & data.keys():
            settings[key] = (data[key], f"set in {file.name}")
    return settings


def table(value):
    """A var or store that is records (a list, or keyed by id) as columns and rows."""
    if (
        isinstance(value, dict)
        and value
        and all(isinstance(v, dict) for v in value.values())
    ):
        value = [{"id": key, **row} for key, row in value.items()]
    if not (
        isinstance(value, list) and value and all(isinstance(v, dict) for v in value)
    ):
        return None
    columns = list(dict.fromkeys(key for row in value for key in row))
    return {
        "columns": columns,
        "rows": [[cell(row.get(c)) for c in columns] for row in value],
    }


def cell(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    if isinstance(value, dict):
        return flow(value)[1:-1]
    return "" if value is None else str(value).strip()


def steps(messages):
    """The worked example as the chat shows a run: tasks, thoughts, cells and outputs."""
    shown = []
    for message in messages:
        text = message["content"]
        observed = OBSERVATION.search(text)
        if message["role"] == "assistant":
            shown += [
                {"kind": "think", "text": " ".join(t.split())}
                for t in THINK.findall(text)
            ]
            shown += [
                {"kind": "cell", "code": textwrap.dedent(code).strip(), "output": None}
                for code in CODE.findall(text)
            ]
        elif observed and shown and shown[-1]["kind"] == "cell":
            shown[-1]["output"] = textwrap.dedent(observed[1]).strip()
        else:
            shown.append({"kind": "task", "text": text.strip()})
    return shown


def item(value, level, name, verb="set"):
    """A field's value in namespace *name*, and where it comes from."""
    source = f"{verb} here" if level == name else f"inherited from {level}"
    return {"value": value, "source": source, "here": level == name}


def nearest(levels, key, name, show, unset):
    """A field the nearest level that sets it decides, or *unset* when none does."""
    found = [(level, ns[key]) for level, ns in levels if ns.get(key) is not None]
    if not found:
        return [unset]
    level, value = found[-1]
    return [item(show(value), level, name)]


def reach(spawn):
    return ", ".join(spawn) or "nowhere: a leaf"


def var_summary(value):
    rows = table(value)
    return count(len(rows["rows"]), "row") if rows else flow(value)


def resolve(name, namespaces, run_repl):
    """Each field of a namespace with the level it came from, as deep_reasoner resolves it."""
    levels = [(level, namespaces[level]) for level in chain(name)]
    tools, variables, decompositions = {}, {}, {}
    for level, ns in levels:
        tools |= {tool: level for tool in ns.get("tools", []) if tool not in tools}
        variables |= {key: (value, level) for key, value in ns.get("vars", {}).items()}
        decompositions |= {d["name"]: level for d in ns.get("decompositions", [])}
    run_repl_item = {"value": flow(run_repl), "source": "from the run settings"}
    chat_item = {"value": "chat", "source": "the run's default"}
    anywhere_item = {"value": "any namespace", "source": "not set"}
    variable_items = [
        item(f"{key} ({var_summary(value)})", level, name)
        for key, (value, level) in variables.items()
    ]
    suffix_items = [
        item(ns["system_suffix"].strip(), level, name)
        for level, ns in levels
        if ns.get("system_suffix")
    ]
    return [
        {"label": "REPL", "items": nearest(levels, "repl", name, flow, run_repl_item)},
        {
            "label": "Backbone",
            "items": nearest(levels, "reasoner", name, flow, chat_item),
        },
        {
            "label": "May spawn into",
            "items": nearest(levels, "spawn", name, reach, anywhere_item),
        },
        {
            "label": "Tools",
            "items": [item(t, lv, name, "granted") for t, lv in tools.items()],
        },
        {"label": "Variables", "items": variable_items},
        {"label": "System suffix", "items": suffix_items},
        {
            "label": "Decompositions",
            "items": [
                item(d, lv, name, "attached") for d, lv in decompositions.items()
            ],
        },
    ]


def decomposition(record, attached):
    name = record["name"]
    use_when, hint = USE_WHEN.get(name, (None, None))
    return {
        "name": name,
        "slug": slug(name),
        "version": VERSIONS.get(name, 1),
        "use_when": use_when,
        "hint": hint,
        "attached": attached,
        "steps": steps(record["messages"]),
        "yaml": dump({"name": name, "messages": record["messages"]}),
    }


def collect():
    """The Library's namespaces, tool blocks, menu and unattached decompositions."""
    namespaces, blocks, menu, unattached = {}, {}, [], []
    for relative, root_as in SOURCES.items():
        path = ENGINE / relative
        data = read(path)
        menu += data.get("decompositions", [])
        levels = {
            name: level or {} for name, level in own_namespaces(path, data).items()
        }
        if root_as is None:
            unattached += [
                d for lv in levels.values() for d in lv.get("decompositions", [])
            ]
            continue
        for name, level in levels.items():
            merge(namespaces.setdefault(root_as if name == ROOT else name, {}), level)
        for name, block in (data.get("tools") or {}).items():
            blocks.setdefault(name, block | {"defined_in": path})
    return namespaces, blocks, menu, unattached


def granted(tool, namespaces):
    return [name for name, ns in namespaces.items() if tool in ns.get("tools", [])]


def tool_rows(blocks, namespaces):
    rows = []
    for name in [*BUILTINS, *(b for b in blocks if b not in BUILTINS)]:
        block = dict(blocks.get(name, {}))
        defined_in = block.pop("defined_in", None)
        factory = block.get("factory", name)
        if "factory_from" in block:
            file = (defined_in.parent / block["factory_from"]).resolve()
            description = block.get("description") or described(file, None)
            file = file.relative_to(ENGINE.resolve())
        else:
            file, constant = BUILTINS[factory]
            description = block.get("description") or described(ENGINE / file, constant)
        source = defined_in and str(defined_in.relative_to(ENGINE))
        row = {"name": name, "version": defined_in and VERSIONS.get(name, 1)}
        row |= {"factory": factory, "file": str(file), "defined_in": source}
        row |= {"granted_in": granted(name, namespaces), "description": description}
        rows.append(row | {"config": dump({name: block}) if block else None})
    return rows


def table_summary(rows):
    return (
        f"{count(len(rows['rows']), 'row')} · {count(len(rows['columns']), 'column')}"
    )


def store(name, block, namespaces):
    """What a tool holds before any run: the documents it loads, or where it saves."""
    entry = {"name": name, "where": ", ".join(granted(name, namespaces))}
    records = [
        document
        for path in block.get("documents", [])
        for document in read(ENGINE / "docs" / path)["documents"]
    ]
    if records:
        return entry | {"summary": count(len(records), "document")} | table(records)
    note = f"Empty until a run adds to it; saved in {block['persist']}."
    return entry | {"summary": "empty", "note": note}


def data_sections(namespaces, blocks):
    variables = [
        {"name": key, "where": name, "summary": table_summary(rows)} | rows
        for name, ns in namespaces.items()
        for key, value in ns.get("vars", {}).items()
        if (rows := table(value))
    ]
    stores = [
        store(name, block, namespaces)
        for name, block in blocks.items()
        if {"documents", "persist"} & block.keys()
    ]
    return [
        {"title": "Preloaded variables", "items": variables},
        {"title": "Tool stores", "items": stores},
    ]


def holders(record, namespaces):
    return [n for n, ns in namespaces.items() if record in ns.get("decompositions", [])]


def decomposition_index(namespaces, menu, unattached):
    attached = [d for ns in namespaces.values() for d in ns.get("decompositions", [])]
    return {
        slug(record["name"]): decomposition(record, holders(record, namespaces))
        for record in attached + menu + unattached
    }


def groups(namespaces, menu, unattached):
    """The Decompositions tab's groups: the menu, root's, each namespace's own and what
    it inherits below root (root's group says every namespace inherits it), the rest."""
    found = [
        {
            "title": "Every namespace's menu",
            "rows": [{"slug": slug(d["name"])} for d in menu],
        }
    ]
    for name in namespaces:
        shown_levels = chain(name) if name == ROOT else chain(name)[1:]
        levels = {
            d["name"]: lv
            for lv in shown_levels
            for d in namespaces[lv].get("decompositions", [])
        }
        rows = [
            {"slug": slug(d)} | ({} if lv == name else {"from": lv})
            for d, lv in levels.items()
        ]
        title = f"{ROOT} · every namespace inherits these" if name == ROOT else name
        found.append({"title": title, "rows": rows})
    rest = {
        "title": "Not attached",
        "rows": [{"slug": slug(d["name"])} for d in unattached],
    }
    return [group for group in [*found, rest] if group["rows"]]


def shown(value):
    if isinstance(value, dict):
        return flow(value)
    return "not set" if value is None else str(value)


def main():
    namespaces, blocks, menu, unattached = collect()
    settings = run_settings(ENGINE / next(iter(SOURCES)))
    run_repl = settings["repl"][0]
    library = {
        "revision": REVISION,
        "default_namespace": settings["entry_namespace"][0],
        "run_settings": [
            {"label": key, "items": [{"value": shown(value), "source": source}]}
            for key, (value, source) in settings.items()
        ],
        "namespaces": [
            {"name": name, "depth": len(chain(name)) - 1}
            | {"fields": resolve(name, namespaces, run_repl)}
            for name in namespaces
        ],
        "decompositions": decomposition_index(namespaces, menu, unattached),
        "groups": groups(namespaces, menu, unattached),
        "tools": tool_rows(blocks, namespaces),
        "data": data_sections(namespaces, blocks),
    }
    OUT.write_text(json.dumps(library, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
