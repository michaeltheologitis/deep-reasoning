"""What a namespace inherits, and from where (§4.9): values are deep_reasoner's own
resolve; only the sources are the Library's."""

from typing import Any

from deep_reasoner.namespaces import ROOT
from deep_reasoner.v2.cli import V2Config, build_namespace_registry
from pydantic import BaseModel

from deep_reasoning.library.records import LibraryState
from deep_reasoning.library.shapes import namespace_config


class Sourced(BaseModel):
    value: Any
    source: str | None  # a namespace, "profile", or None (unset everywhere)


class SuffixPart(BaseModel):
    source: str
    text: str


class EffectiveTool(BaseModel):
    name: str
    source: str
    defined: bool


class EffectiveDecomposition(BaseModel):
    name: str
    slug: str
    version: int
    use_when: str | None
    source: str


class Effective(BaseModel):
    namespace: str
    chain: list[str]  # root first
    repl: Sourced
    reasoner: Sourced
    spawn: Sourced
    system_suffix: list[SuffixPart]
    tools: list[EffectiveTool]
    vars: dict[str, Sourced]
    decompositions: list[EffectiveDecomposition]


def chain(namespace: str) -> list[str]:
    """root, then each dotted prefix of namespace, as deep_reasoner walks it."""
    parts = namespace.split(".")
    prefixes = [".".join(parts[: i + 1]) for i in range(len(parts))]
    return [ROOT, *(p for p in prefixes if p != ROOT)]


def resolved(state: LibraryState, namespace: str) -> Any:
    """deep_reasoner's ResolvedNamespace for namespace, over the Library's live heads."""
    configs = {
        name: namespace_config(
            ns.yaml, [state.decompositions[d].yaml for d in ns.decompositions]
        )
        for name, ns in state.namespaces.items()
    }
    cfg = V2Config.model_validate({**state.profile.data, "namespaces": configs})
    registry = build_namespace_registry(cfg)
    try:
        return registry.resolve(namespace)
    finally:
        registry.close()


def defined_tools(state: LibraryState) -> set[str]:
    """The tools a grant can name: the Library's, and llm while the profile has a model."""
    return set(state.tools) | ({"llm"} if state.profile.data.get("model") else set())


def _last(levels: list[tuple[str, dict[str, Any]]], key: str) -> str | None:
    setting = [name for name, data in levels if data.get(key) is not None]
    return setting[-1] if setting else None


def effective(state: LibraryState, namespace: str) -> Effective:
    values = resolved(state, namespace)
    levels = [(name, state.namespaces[name].data) for name in chain(namespace)]
    attached = [
        (name, state.namespaces[name].decompositions) for name in chain(namespace)
    ]
    defined = defined_tools(state)
    return Effective(
        namespace=namespace,
        chain=[name for name, _ in levels],
        repl=Sourced(
            value=values.repl.model_dump(mode="json"),
            source=_last(levels, "repl") or "profile",
        ),
        reasoner=Sourced(value=values.reasoner, source=_last(levels, "reasoner")),
        spawn=Sourced(value=values.spawn, source=_last(levels, "spawn")),
        system_suffix=[
            SuffixPart(source=name, text=data["system_suffix"])
            for name, data in levels
            if data.get("system_suffix") is not None
        ],
        tools=[
            EffectiveTool(
                name=tool,
                source=next(n for n, data in levels if tool in data.get("tools", [])),
                defined=tool in defined,
            )
            for tool in values.tools
        ],
        vars={
            key: Sourced(
                value=value,
                source=[n for n, data in levels if key in data.get("vars", {})][-1],
            )
            for key, value in values.vars.items()
        },
        decompositions=[
            EffectiveDecomposition(
                name=d.name,
                slug=state.decompositions[d.name].slug,
                version=state.decompositions[d.name].version,
                use_when=state.decompositions[d.name].use_when,
                source=[n for n, names in attached if d.name in names][-1],
            )
            for d in values.decompositions
        ],
    )
