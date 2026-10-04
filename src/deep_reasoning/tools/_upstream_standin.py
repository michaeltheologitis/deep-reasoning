"""STAND-IN, not for merge, not counted: the deep_reasoner API that spec DR3 proposes,
patched onto deep_reasoner at d7334ae so that D4 can be measured against it.

Dean's side would be: make_tools' per-block body as a public build_tool (make_tools calls
it), and its ValueErrors as typed subclasses of ValueError (so every caller that catches
ValueError today is unaffected)."""

from typing import Any

from deep_reasoner.primitives import Func
from deep_reasoner.tools.base import TOOL_BUILDERS, load_tool_factory
from deep_reasoner.v2.cli import build_llm_tool


class ToolBuildError(ValueError):
    """make_tools refused one tool block before or after calling its factory."""


class ToolFactoryNotFound(ToolBuildError):
    """No factory by that name: the file is missing, does not define it, or it is no
    function; or no built-in factory has that name."""


class UnknownToolFactory(ToolFactoryNotFound):
    def __init__(self, factory: str, alias: str) -> None:
        super().__init__(
            f"Unknown tool factory {factory!r} for {alias!r}. "
            f"Known: {sorted(TOOL_BUILDERS)}. "
            f"A factory of your own is reached with factory_from: <a .py file, "
            f"relative to this config>."
        )


class ToolImportFailed(ToolBuildError):
    """Importing the factory_from file raised; __cause__ is what it raised."""


class ToolNotFunc(ToolBuildError):
    """The factory returned something other than a Func."""


def build_tool(
    alias: str, tool_cfg: dict[str, Any], client: Any, config_path: str | None
) -> Func:
    """One block of cfg.tools, built as make_tools builds it (the default `llm` aside).
    A factory's own exception is raised as it is."""
    factory = tool_cfg.get("factory", alias)
    factory_from = tool_cfg.get("factory_from")
    params = {k: v for k, v in tool_cfg.items() if k not in ("factory", "factory_from")}
    if factory_from is not None:
        try:
            build = load_tool_factory(alias, factory, factory_from, config_path)
        except ValueError as exc:
            kind = (
                ToolImportFailed if exc.__cause__ is not None else ToolFactoryNotFound
            )
            raise kind(str(exc)) from exc.__cause__
        built = build(client, params)
        if not isinstance(built, Func):
            raise ToolNotFunc(
                f"tool {alias!r}: {factory} in {factory_from} returned "
                f"{type(built).__name__}, not a Func. A tool factory returns "
                f"Func(value, description=…) — the registry reads its `.value` "
                f"(what the REPL binds) and `.description` (what the agent is told)."
            )
        return built
    if factory == "llm":
        return build_llm_tool(client, None, params)
    if factory not in TOOL_BUILDERS:
        raise UnknownToolFactory(factory, alias)
    return TOOL_BUILDERS[factory](client, {**params, "config_path": config_path})
