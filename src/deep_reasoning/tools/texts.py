"""Every sentence Check and the tool routes can send, verbatim from D4 §9.1.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

from collections.abc import Iterable

BUILT = "builds"


def reserved_name(name: str) -> str:
    return (
        f"'{name}' is one of deep_reasoner's own names in the REPL (subagent, run_all, "
        "FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another "
        "name."
    )


def syntax(name: str, line: int | None, message: str) -> str:
    return f"tool '{name}': tools/{name}.py line {line}: {message}"


def unknown_factory(factory: str, alias: str, known: Iterable[str]) -> str:
    """make_tools' own sentence (deep_reasoner v2/cli.py), copied."""
    return (
        f"Unknown tool factory {factory!r} for {alias!r}. "
        f"Known: {sorted(known)}. "
        f"A factory of your own is reached with factory_from: <a .py file, "
        f"relative to this config>."
    )


def not_func(alias: str, factory: str, factory_from: str, type_name: str) -> str:
    """make_tools' own sentence (deep_reasoner v2/cli.py), copied."""
    return (
        f"tool {alias!r}: {factory} in {factory_from} returned "
        f"{type_name}, not a Func. A tool factory returns "
        f"Func(value, description=…) — the registry reads its `.value` "
        f"(what the REPL binds) and `.description` (what the agent is told)."
    )


def factory_raised(name: str, factory: str, type_name: str, message: str) -> str:
    return f"tool '{name}': {factory} raised {type_name}: {message}"


def build_timeout(name: str, seconds: float) -> str:
    return (
        f"tool '{name}': building it took longer than {seconds:g} s, so Check stopped it. "
        "A tool is built at the start of every conversation; a factory must return "
        "quickly."
    )


def ready_timeout(seconds: float) -> str:
    return (
        f"Check could not start deep_reasoner within {seconds:g} s, so it did not build "
        "the tool. Try again."
    )


def child_ended(name: str, how: str, phase: str) -> str:
    """how: 'exit code 3', 'signal 11'; phase: 'starting', 'building the tool'."""
    return f"tool '{name}': the Check process ended ({how}) while {phase}."


def example_timeout(seconds: float) -> str:
    return f"TimeoutError: the expression did not finish within {seconds:g} s"


def builtin(factory: str) -> str:
    return (
        f"'{factory}' is one of deep_reasoner's own factories. It is built when a "
        "conversation starts, with your model and files, so Check does not build it here."
    )


def check_failed(name: str) -> str:
    return f"'{name}' did not pass Check, so it was not saved."
