"""Every sentence a user of the Library can read, verbatim from §4.10.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

from collections.abc import Sequence

METADATA_USE_WHEN = (
    "Use-when text is stored beside the YAML: pass use_when=... instead."
)
METADATA_HINT = "A hint is stored beside the YAML: pass hint=... instead."
INLINE_DECOMPOSITIONS = (
    "A namespace's decompositions are attached by name, not written in its YAML: pass "
    "decompositions=[...] instead."
)
NOT_A_MAPPING = "The YAML must be a mapping of keys to values."
NO_FINAL_ANSWER = "This example never reaches FinalAnswer; the agent will imitate that."


def invalid(name: str | None, model: str, errors: Sequence[tuple[str, str]]) -> str:
    """The mock-up's failure cell: a heading, then one line per (loc, msg)."""
    subject = f"'{name}'" if name else "this YAML"
    lines = [f"{subject} is not a valid deep_reasoner {model}:"]
    lines += [f"  {loc}: {msg}" if loc else f"  {msg}" for loc, msg in errors]
    return "\n".join(lines)


def profile_part(key: str) -> str:
    return (
        f"'{key}' is not part of the profile: namespaces, decompositions and tools are "
        "stored as entries of their own."
    )


def namespace_name(name: str) -> str:
    return (
        f"'{name}' is not a namespace name: use letters, digits, '_' and '-', with '.' "
        "between levels (for example math.geometry)."
    )


def decomposition_name(name: str) -> str:
    return (
        "A decomposition's name must not start or end with a space or hold control "
        f"characters; got {name!r}."
    )


def slug_empty(name: str) -> str:
    return f"'{name}' has no letters or digits, so it cannot be a slash command."


def tool_name(name: str) -> str:
    return (
        f"'{name}' is not a tool name: a tool is bound in the REPL under its name, so it "
        "must be a Python identifier."
    )


def tool_file(name: str, value: str) -> str:
    return (
        f"Tool '{name}': factory_from must be tools/{name}.py, where the Library writes "
        f"its source; got '{value}'."
    )


def tool_no_source(name: str) -> str:
    return f"Tool '{name}' names factory_from but no source was sent with it."
