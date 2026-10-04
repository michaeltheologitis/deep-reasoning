"""deep_reasoner's own models for each kind, canonical YAML, and the Library's name rules."""

import functools
import json
import keyword
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import metadata
from typing import Any

import yaml
from deep_reasoner.namespaces import NamespaceConfig
from deep_reasoner.prompt_config import Decomposition
from deep_reasoner.v2.cli import V2Config
from deep_reasoner.v2.messages import NoCodeBlock, code
from pydantic import BaseModel, ValidationError

from deep_reasoning.acp.catalog import slug
from deep_reasoning.library import texts
from deep_reasoning.library.records import FieldError, LibraryValidationError

__all__ = ["slug"]

# Matched with fullmatch.
NAMESPACE_NAME: re.Pattern[str] = re.compile(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*")
SPLIT_KEYS: frozenset[str] = frozenset(
    {"namespaces", "namespaces_dir", "decompositions", "tools", "config_path"}
)
TOOL_DIR = "tools"
YAML_WIDTH = 100
FINAL_ANSWER = "FinalAnswer("


class _Dumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _represent_str)


def canonical_yaml(data: Mapping[str, Any]) -> str:
    return yaml.dump(
        dict(data),
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=YAML_WIDTH,
    )


@functools.cache
def deep_reasoner_build() -> str:
    """'0.2.1+d7334ae' when deep-reasoner was installed from git (direct_url.json's
    commit_id, first 7), else its version alone."""
    dist = metadata.distribution("deep-reasoner")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    commit = direct.get("vcs_info", {}).get("commit_id")
    return f"{dist.version}+{commit[:7]}" if commit else dist.version


@dataclass(frozen=True)
class Shaped:
    yaml: str  # canonical
    data: dict[str, Any]  # the canonical YAML, parsed
    name: str  # the entity's key ("profile" for the profile)
    warnings: list[str]


def load_mapping(text: str, model: str) -> dict[str, Any]:
    """The YAML (or JSON) text as a mapping, or INVALID with one whole-document error."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise _invalid(None, model, [FieldError(loc="", msg=str(exc))]) from exc
    if not isinstance(data, dict):
        raise _invalid(None, model, [FieldError(loc="", msg=texts.NOT_A_MAPPING)])
    return data


def _name_of(data: Mapping[str, Any]) -> str | None:
    name = data.get("name")
    return name if isinstance(name, str) else None


def _invalid(
    name: str | None,
    model: str,
    errors: Sequence[FieldError],
    extra: Sequence[str] = (),
) -> LibraryValidationError:
    message = texts.invalid(name, model, [(e.loc, e.msg) for e in errors])
    return LibraryValidationError("\n".join([message, *extra]), errors)


def _shaped(
    model: type[BaseModel],
    data: dict[str, Any],
    rules: list[FieldError],
    *,
    name: str | None,
    label: str,
    extra: Sequence[str] = (),
) -> tuple[BaseModel, str]:
    """Validate data with model, add the Library's own rule errors, and return the model
    and its canonical YAML; any error raises INVALID."""
    try:
        validated, errors = model.model_validate(data), []
    except ValidationError as exc:
        validated = None
        errors = [
            FieldError(loc=".".join(str(part) for part in e["loc"]), msg=e["msg"])
            for e in exc.errors()
        ]
    if errors or rules:
        raise _invalid(name, label, [*errors, *rules], extra)
    return validated, canonical_yaml(
        validated.model_dump(mode="json", exclude_unset=True)
    )


def _reaches_final_answer(decomposition: Decomposition) -> bool:
    for message in decomposition.messages:
        if message.role != "assistant":
            continue
        try:
            if FINAL_ANSWER in code(message.content).source:
                return True
        except NoCodeBlock:
            continue
    return False


def validate_namespace(text: str) -> Shaped:
    data = load_mapping(text, "NamespaceConfig")
    name = _name_of(data)
    rules = []
    if name is not None and not NAMESPACE_NAME.fullmatch(name):
        rules.append(FieldError(loc="name", msg=texts.namespace_name(name)))
    if "decompositions" in data:
        rules.append(FieldError(loc="decompositions", msg=texts.INLINE_DECOMPOSITIONS))
    _, canonical = _shaped(
        NamespaceConfig, data, rules, name=name, label="NamespaceConfig"
    )
    return Shaped(canonical, yaml.safe_load(canonical), name, [])


def validate_decomposition(text: str) -> Shaped:
    data = load_mapping(text, "Decomposition")
    name = _name_of(data)
    rules = []
    if name is not None and (
        name != name.strip() or any(unicodedata.category(c) == "Cc" for c in name)
    ):
        rules.append(FieldError(loc="name", msg=texts.decomposition_name(name)))
    elif name is not None and not slug(name):
        rules.append(FieldError(loc="name", msg=texts.slug_empty(name)))
    extra = [
        line
        for key, line in (
            ("use_when", texts.METADATA_USE_WHEN),
            ("hint", texts.METADATA_HINT),
        )
        if key in data
    ]
    validated, canonical = _shaped(
        Decomposition, data, rules, name=name, label="Decomposition", extra=extra
    )
    warnings = [] if _reaches_final_answer(validated) else [texts.NO_FINAL_ANSWER]
    return Shaped(canonical, yaml.safe_load(canonical), name, warnings)


def tool_file(name: str) -> str:
    """Where a tool's source is written beside main.yaml, as factory_from names it."""
    return f"{TOOL_DIR}/{name}.py"


def validate_tool(name: str, text: str, source: str | None) -> Shaped:
    """With a source, factory_from is set to tools/<name>.py in the canonical block."""
    data = load_mapping(text, "tool")
    rules = []
    if not name.isidentifier() or keyword.iskeyword(name):
        rules.append(FieldError(loc="name", msg=texts.tool_name(name)))
    if any(not isinstance(key, str) for key in data):
        rules.append(FieldError(loc="", msg=texts.NOT_A_MAPPING))
    declared = data.get("factory_from")
    if source is None and declared is not None:
        rules.append(FieldError(loc="factory_from", msg=texts.tool_no_source(name)))
    elif source is not None and declared not in (None, tool_file(name)):
        rules.append(
            FieldError(loc="factory_from", msg=texts.tool_file(name, declared))
        )
    if rules:
        raise _invalid(name, "tool", rules)
    if source is not None:
        data["factory_from"] = tool_file(name)
    canonical = canonical_yaml(data)
    return Shaped(canonical, yaml.safe_load(canonical), name, [])


def validate_profile(text: str) -> Shaped:
    data = load_mapping(text, "V2Config")
    rules = [
        FieldError(loc=key, msg=texts.profile_part(key))
        for key in data
        if key in SPLIT_KEYS
    ]
    kept = {key: value for key, value in data.items() if key not in SPLIT_KEYS}
    _, canonical = _shaped(V2Config, kept, rules, name=None, label="V2Config")
    return Shaped(canonical, yaml.safe_load(canonical), "profile", [])


def namespace_config(
    namespace_yaml: str,
    decomposition_yamls: Sequence[str],
) -> NamespaceConfig:
    """A namespace head's canonical YAML with its attached decompositions' canonical YAML
    inlined as `decompositions`, in the given (attachment) order, validated."""
    data = yaml.safe_load(namespace_yaml)
    bodies = [yaml.safe_load(text) for text in decomposition_yamls]
    if bodies:
        data["decompositions"] = bodies
    return NamespaceConfig.model_validate(data)
