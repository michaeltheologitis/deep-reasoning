"""TASK-44: every sentence a user reads names the product Deep Reasoning. Code, ids, paths,
versions and Dean's package keep their names, and ALLOWED says where each may stand.

The built panel is not read: ci.yml pins it to a fresh build of the sources read here."""

import ast
import json
import re
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_TEXTS = (
    "packages/dr-app/src/dr_app/texts.py",
    "src/deep_reasoning/acp/texts.py",
    "src/deep_reasoning/library/texts.py",
    "src/deep_reasoning/tools/texts.py",
)
TYPESCRIPT_TEXTS = ("canvas-app/src/ui/texts.ts", "canvas-app/src/page/texts.ts")
MANIFEST = "src/deep_reasoning/canvas_app/canvas-extension.json"
AGENT = "src/deep_reasoning/acp/agent.py"
BOOTSTRAP = "desktop/bootstrap.sh"
README = "README.md"
NAMES = re.compile(r"deep_reasoner|deep-reasoning")
ALLOWED = (
    re.compile(r"from deep_reasoner import"),  # code: the new-tool template
    re.compile(
        r"deep_reasoner \{"
    ),  # the installed package, a version or commit follows
    re.compile(r"deep_reasoner_beta"),  # Dean's repository
    re.compile(r"/api/agent-profiles/deep_reasoner\b"),  # the profile's id, in a path
    re.compile(r"~/\.deep-reasoning"),  # the app's folder
    re.compile(r"github\.com/[\w.-]+/deep-reasoning"),  # this repository
    re.compile(r"deep-reasoning-<version>"),  # the packages' file names
)
# In the README only: sentences about Dean's package or this repository, as whole phrases.
README_ALLOWED = (
    re.compile(r"^# deep-reasoning "),  # the repository's own title
    re.compile(r"This repository runs Dean's deep_reasoner"),
    re.compile(r"deep_reasoner behind the Agent Client Protocol"),
    re.compile(r"The app installs deep_reasoner on your computer"),
    re.compile(r"Deep Reasoning and deep_reasoner"),  # what the runtime installs
    re.compile(r"is deep_reasoner's own command line"),
    re.compile(r"nothing of deep_reasoner is in the download"),
    re.compile(r"deep-reasoning and its releases are public"),
)
CODE_SPAN = re.compile(r"`[^`\n]+`")
FENCED_BLOCK = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
TS_LITERAL = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'|`(?:[^`\\]|\\.)*`')
ECHO = re.compile(r'^\s*echo "(.*)"$', re.MULTILINE)


def is_docstring(parents: dict[ast.AST, ast.AST], node: ast.Constant) -> bool:
    statement = parents.get(node)
    owner = parents.get(statement) if isinstance(statement, ast.Expr) else None
    body = getattr(owner, "body", None)
    return bool(body) and body[0] is statement


def python_literals(path: Path) -> Iterator[str]:
    """Each string literal but docstrings; an f-string with {…} for each field."""
    tree = ast.parse(path.read_text())
    parents = {
        child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            yield "".join(
                part.value if isinstance(part, ast.Constant) else "{…}"
                for part in node.values
            )
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and not isinstance(parents.get(node), ast.JoinedStr)
            and not is_docstring(parents, node)
        ):
            yield node.value


def constant_fields(node: ast.Dict) -> dict[str, ast.expr]:
    return {
        key.value: value
        for key, value in zip(node.keys, node.values)
        if isinstance(key, ast.Constant)
    }


def agent_title(path: Path) -> str:
    """dr-acp's agentInfo title, as initialize answers it."""
    for node in ast.walk(ast.parse(path.read_text())):
        info = (
            constant_fields(node).get("agentInfo")
            if isinstance(node, ast.Dict)
            else None
        )
        if isinstance(info, ast.Dict):
            return ast.literal_eval(constant_fields(info)["title"])
    raise AssertionError(f"{path} answers no agentInfo")


def manifest_texts(path: Path) -> Iterator[str]:
    manifest = json.loads(path.read_text())
    yield manifest["display_name"]
    yield manifest["description"]
    for panel in manifest["contributes"]["conversation_panels"]:
        yield panel["title"]
        yield from (tab["title"] for tab in panel["tabs"])


def readme_prose(path: Path) -> str:
    """The README without its fenced blocks and code spans, its lines joined."""
    text = CODE_SPAN.sub("", FENCED_BLOCK.sub("", path.read_text()))
    return " ".join(text.split())


def prose() -> Iterator[tuple[str, str]]:
    """(where, text) for every sentence a user can read."""
    for name in PYTHON_TEXTS:
        yield from ((name, text) for text in python_literals(ROOT / name))
    for name in TYPESCRIPT_TEXTS:
        literals = TS_LITERAL.findall((ROOT / name).read_text())
        yield from ((name, text) for text in literals)
    yield from ((MANIFEST, text) for text in manifest_texts(ROOT / MANIFEST))
    yield AGENT, agent_title(ROOT / AGENT)
    yield from ((BOOTSTRAP, t) for t in ECHO.findall((ROOT / BOOTSTRAP).read_text()))


def unallowed(text: str, allowed: tuple[re.Pattern[str], ...]) -> list[str]:
    """Each use of a name that no allowed pattern covers, with the words around it."""
    for pattern in allowed:
        text = pattern.sub("", text)
    return [text[max(0, m.start() - 40) : m.end() + 40] for m in NAMES.finditer(text)]


def test_prose_says_deep_reasoning():
    found = [
        f"{where}: {use!r}"
        for where, text in prose()
        for use in unallowed(text, ALLOWED)
    ]
    readme = readme_prose(ROOT / README)
    found += [
        f"{README}: {use!r}" for use in unallowed(readme, ALLOWED + README_ALLOWED)
    ]
    assert found == []
