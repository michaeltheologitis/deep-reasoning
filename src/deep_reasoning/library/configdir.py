"""A plain dr config directory into parts (import), and a Library state back out (§4.6)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from deep_reasoner.namespaces import ROOT, NamespaceConfig, load_namespaces_from_dir
from pydantic import ValidationError

from deep_reasoning.acp.catalog import load_dr_config
from deep_reasoning.library import shapes, texts
from deep_reasoning.library.records import (
    DecompositionMeta,
    LibraryImportError,
    LibraryState,
    Manifest,
)

MAIN = "main.yaml"
MANIFEST = "library.yaml"
NAMESPACES_DIR = "namespaces"


@dataclass(frozen=True)
class ConfigParts:
    main: Path  # the main YAML read
    profile: dict[str, Any]  # the V2Config remainder, as set
    top_level: list[str]  # top-level decomposition names, in order
    # (the NamespaceConfig dump without decompositions, its attached names), root first
    namespaces: list[tuple[dict[str, Any], list[str]]]
    decompositions: dict[str, dict[str, Any]]  # name -> its dump, as first seen
    tools: dict[str, tuple[dict[str, Any], str | None]]  # name -> (block, source)
    metadata: dict[str, DecompositionMeta]  # from library.yaml beside it, if any


def _dump(model: Any, **kwargs: Any) -> dict[str, Any]:
    return model.model_dump(mode="json", exclude_unset=True, **kwargs)


def _unique(names: list[str]) -> list[str]:
    return list(dict.fromkeys(names))


def _namespaces(cfg: Any) -> dict[str, NamespaceConfig]:
    """Root first, then the namespaces_dir's, then the inline ones, a later one replacing
    an earlier one by name, as build_registry layers them."""
    found: dict[str, NamespaceConfig] = {ROOT: NamespaceConfig(name=ROOT)}
    if cfg.namespaces_dir is not None:
        found |= {ns.name: ns for ns in load_namespaces_from_dir(cfg.namespaces_dir)}
    return found | {ns.name: ns for ns in cfg.namespaces.values()}


def _decompositions(
    main: Path, cfg: Any, namespaces: dict[str, NamespaceConfig]
) -> dict[str, dict[str, Any]]:
    """Every decomposition by name, top level first; one name with two bodies is refused."""
    places = [("the top level", cfg.decompositions)] + [
        (f"namespace '{name}'", ns.decompositions) for name, ns in namespaces.items()
    ]
    bodies: dict[str, dict[str, Any]] = {}
    first_place: dict[str, str] = {}
    for place, decompositions in places:
        for decomposition in decompositions:
            body = _dump(decomposition)
            if bodies.setdefault(decomposition.name, body) != body:
                raise LibraryImportError(
                    texts.import_collision(
                        str(main),
                        decomposition.name,
                        first_place[decomposition.name],
                        place,
                    )
                )
            first_place.setdefault(decomposition.name, place)
    by_slug: dict[str, str] = {}
    for name in bodies:
        other = by_slug.setdefault(shapes.slug(name), name)
        if other != name:
            raise LibraryImportError(texts.slug_taken(name, shapes.slug(name), other))
    return bodies


def _tools(main: Path, cfg: Any) -> dict[str, tuple[dict[str, Any], str | None]]:
    """Each tool block; a factory_from file is read, and named tools/<name>.py."""
    tools: dict[str, tuple[dict[str, Any], str | None]] = {}
    for name, block in cfg.tools.items():
        declared = block.get("factory_from")
        if declared is None:
            tools[name] = (dict(block), None)
            continue
        # Resolved as deep_reasoner's load_tool_factory does: against the main config.
        resolved = (main.resolve().parent / declared).resolve()
        if not resolved.is_file():
            raise LibraryImportError(
                texts.import_tool_file(name, declared, str(resolved))
            )
        source = resolved.read_bytes().decode()
        tools[name] = ({**block, "factory_from": shapes.tool_file(name)}, source)
    return tools


def _metadata(main: Path) -> dict[str, DecompositionMeta]:
    path = main.parent / MANIFEST
    if not path.is_file():
        return {}
    try:
        return Manifest.model_validate(yaml.safe_load(path.read_text())).metadata
    except (yaml.YAMLError, ValidationError):
        return {}


def read_config(path: Path) -> ConfigParts:
    main = path / MAIN if path.is_dir() else path
    try:
        cfg = load_dr_config(main)
        namespaces = _namespaces(cfg)
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        raise LibraryImportError(texts.import_load(str(main), detail)) from exc
    return ConfigParts(
        main=main,
        profile=_dump(cfg, exclude=set(shapes.SPLIT_KEYS)),
        top_level=_unique([d.name for d in cfg.decompositions]),
        namespaces=[
            (
                _dump(ns, exclude={"decompositions"}),
                _unique([d.name for d in ns.decompositions]),
            )
            for ns in namespaces.values()
        ],
        decompositions=_decompositions(main, cfg, namespaces),
        tools=_tools(main, cfg),
        metadata=_metadata(main),
    )


def _write_yaml(path: Path, data: dict[str, Any], header: str = "") -> None:
    path.write_text(header + shapes.canonical_yaml(data), encoding="utf-8")


def write_config(state: LibraryState, dest: Path, *, namespace: str) -> Manifest:
    """namespaces/<name>.yaml, tools/<name>.py, library.yaml, then main.yaml (last, so a
    directory with a main.yaml is complete)."""
    header = (
        f"# Written by the deep-reasoning Library from {state.path} at revision "
        f"{state.rev}. Edit the Library, not this file.\n"
    )
    bodies = {name: d.yaml for name, d in state.decompositions.items()}
    (dest / NAMESPACES_DIR).mkdir()
    for ns in state.namespaces.values():
        config = shapes.namespace_config(
            ns.yaml, [bodies[d] for d in ns.decompositions]
        )
        _write_yaml(dest / NAMESPACES_DIR / f"{ns.name}.yaml", _dump(config))
    sourced = {
        name: t.source for name, t in state.tools.items() if t.source is not None
    }
    if sourced:
        (dest / shapes.TOOL_DIR).mkdir()
    for name, source in sourced.items():
        (dest / shapes.tool_file(name)).write_bytes(source.encode())
    manifest = Manifest(
        library=str(state.path),
        rev=state.rev,
        namespace=namespace,
        deep_reasoner=shapes.deep_reasoner_build(),
        profile=state.profile.version,
        namespaces={name: ns.version for name, ns in state.namespaces.items()},
        decompositions={name: d.version for name, d in state.decompositions.items()},
        tools={name: t.version for name, t in state.tools.items()},
        metadata={
            name: DecompositionMeta(use_when=d.use_when, hint=d.hint)
            for name, d in state.decompositions.items()
            if d.use_when is not None or d.hint is not None
        },
    )
    _write_yaml(dest / MANIFEST, manifest.model_dump(mode="json"), header)
    main = {
        **state.profile.data,
        "entry_namespace": namespace,
        "namespaces_dir": NAMESPACES_DIR,
    }
    if state.profile.decompositions:
        main["decompositions"] = [
            state.decompositions[name].data for name in state.profile.decompositions
        ]
    if state.tools:
        main["tools"] = {name: t.data for name, t in state.tools.items()}
    _write_yaml(dest / MAIN, main, header)
    return manifest
