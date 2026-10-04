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
    Manifest,
)

MAIN = "main.yaml"
MANIFEST = "library.yaml"


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
