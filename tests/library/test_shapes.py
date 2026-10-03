import json
import re
from pathlib import Path

import pytest
import yaml

from deep_reasoning.library import shapes
from deep_reasoning.library.records import LibraryValidationError

EXAMPLE = {
    "name": "catalog lookup",
    "messages": [
        {"role": "user", "content": "Which course comes after CS101?"},
        {
            "role": "assistant",
            "content": "<think>Scan.</think>\n<repl>\nFinalAnswer('CS201')\n</repl>\n",
        },
    ],
}


@pytest.mark.parametrize(
    "text",
    [
        yaml.safe_dump(EXAMPLE, default_flow_style=False),
        yaml.safe_dump(EXAMPLE, default_flow_style=True),
        json.dumps(EXAMPLE),
        json.dumps({"messages": EXAMPLE["messages"], "name": EXAMPLE["name"]}),
        "name: 'catalog lookup'\n" + yaml.safe_dump({"messages": EXAMPLE["messages"]}),
    ],
    ids=["block", "flow", "json", "key-order", "quoted"],
)
def test_canonical_yaml_is_the_same_for_every_spelling_of_one_model(text):
    canonical = shapes.validate_decomposition(text).yaml
    assert canonical == shapes.validate_decomposition(json.dumps(EXAMPLE)).yaml
    assert canonical.startswith("name: catalog lookup\nmessages:\n")


def test_canonical_yaml_is_idempotent():
    once = shapes.validate_decomposition(json.dumps(EXAMPLE)).yaml
    assert shapes.validate_decomposition(once).yaml == once
    assert shapes.canonical_yaml(yaml.safe_load(once)) == once


def test_multiline_strings_are_literal_blocks():
    text = shapes.validate_decomposition(json.dumps(EXAMPLE)).yaml
    assert "  content: |\n    <think>Scan.</think>\n    <repl>\n" in text


def test_canonical_yaml_keeps_only_what_the_author_set():
    shaped = shapes.validate_namespace("name: math\ntools: [llm]\n")
    assert shaped.yaml == "name: math\ntools:\n- llm\n"
    assert shaped.data == {"name": "math", "tools": ["llm"]}


def test_metadata_in_the_yaml_is_refused_with_deep_reasoners_message():
    with pytest.raises(LibraryValidationError) as raised:
        shapes.validate_decomposition(
            "name: x\nuse_when: one course\nmessages: [{role: user, content: hi}]"
        )
    assert str(raised.value) == (
        "'x' is not a valid deep_reasoner Decomposition:\n"
        "  use_when: Extra inputs are not permitted\n"
        "Use-when text is stored beside the YAML: pass use_when=... instead."
    )
    assert [e.model_dump() for e in raised.value.errors] == [
        {"loc": "use_when", "msg": "Extra inputs are not permitted"}
    ]


def test_pydantic_locations_are_joined_with_dots():
    with pytest.raises(LibraryValidationError) as raised:
        shapes.validate_decomposition("name: x\nmessages: [{role: bot, content: hi}]")
    assert [e.loc for e in raised.value.errors] == ["messages.0.role"]


@pytest.mark.parametrize(
    ("name", "ok"),
    [
        ("root", True),
        ("math.geometry", True),
        ("course_advisor-2", True),
        ("math..geometry", False),
        ("math geometry", False),
        (".math", False),
        ("matemática", False),
    ],
)
def test_a_namespace_name_is_ascii_words_joined_by_single_dots(name, ok):
    text = yaml.safe_dump({"name": name})
    if ok:
        assert shapes.validate_namespace(text).name == name
        return
    with pytest.raises(LibraryValidationError, match="is not a namespace name"):
        shapes.validate_namespace(text)


def test_a_namespace_carries_no_inline_decompositions():
    with pytest.raises(LibraryValidationError) as raised:
        shapes.validate_namespace(
            yaml.safe_dump({"name": "a", "decompositions": [EXAMPLE]})
        )
    assert [e.loc for e in raised.value.errors] == ["decompositions"]


@pytest.mark.parametrize(
    ("name", "error"),
    [
        (" padded", "must not start or end with a space"),
        ("tab\there", "control characters"),
        ("?!", "has no letters or digits"),
    ],
)
def test_decomposition_names_must_make_a_slash_command(name, error):
    with pytest.raises(LibraryValidationError, match=error):
        shapes.validate_decomposition(json.dumps({**EXAMPLE, "name": name}))


@pytest.mark.parametrize(
    ("block", "source", "result"),
    [
        (
            {"factory": "llm", "model": "small"},
            None,
            {"factory": "llm", "model": "small"},
        ),
        (
            {"factory": "make"},
            "def make(client, cfg): ...\n",
            {"factory": "make", "factory_from": "tools/waitlist.py"},
        ),
        (
            {"factory": "make", "factory_from": "tools/waitlist.py"},
            "def make(client, cfg): ...\n",
            {"factory": "make", "factory_from": "tools/waitlist.py"},
        ),
        (
            {"factory": "make", "factory_from": "./tools.py"},
            "x",
            "must be tools/waitlist.py",
        ),
        ({"factory": "make", "factory_from": "tools/waitlist.py"}, None, "no source"),
    ],
)
def test_tool_factory_from_must_be_its_own_file(block, source, result):
    text = yaml.safe_dump(block)
    if isinstance(result, str):
        with pytest.raises(LibraryValidationError, match=result):
            shapes.validate_tool("waitlist", text, source)
        return
    assert shapes.validate_tool("waitlist", text, source).data == result


@pytest.mark.parametrize("name", ["class", "two words", "1st"])
def test_a_tool_name_is_a_python_identifier(name):
    with pytest.raises(LibraryValidationError, match="must be a Python identifier"):
        shapes.validate_tool(name, "factory: llm\n", None)


@pytest.mark.parametrize("key", sorted(shapes.SPLIT_KEYS))
def test_profile_refuses_namespaces_decompositions_and_tools(key):
    with pytest.raises(LibraryValidationError) as raised:
        shapes.validate_profile(yaml.safe_dump({"model": "m", key: {}}))
    assert [e.loc for e in raised.value.errors] == [key]
    assert "is not part of the profile" in str(raised.value)


def test_a_profile_keeps_extras_and_drops_nothing_it_was_given():
    shaped = shapes.validate_profile(
        "model: m\ndescription: Example run\nmax_iter: 5\n"
    )
    assert shaped.data == {"model": "m", "max_iter": 5, "description": "Example run"}


def test_an_example_without_final_answer_warns():
    answering = shapes.validate_decomposition(json.dumps(EXAMPLE))
    assert answering.warnings == []
    looping = json.dumps(
        {
            "name": "x",
            "messages": [
                {"role": "user", "content": "hi"},
                {
                    "role": "assistant",
                    "content": "FinalAnswer(1) outside\n<repl>\nprint(1)\n</repl>",
                },
            ],
        }
    )
    assert shapes.validate_decomposition(looping).warnings == [
        "This example never reaches FinalAnswer; the agent will imitate that."
    ]


@pytest.mark.parametrize(
    ("text", "error"),
    [("- a\n- b\n", "must be a mapping"), ("name: [\n", "expected")],
)
def test_a_document_that_is_not_a_mapping_is_invalid(text, error):
    with pytest.raises(LibraryValidationError, match=error) as raised:
        shapes.validate_namespace(text)
    assert str(raised.value).startswith(
        "this YAML is not a valid deep_reasoner NamespaceConfig:"
    )


def test_the_build_names_the_pinned_commit():
    pyproject = Path(__file__).parents[2] / "pyproject.toml"
    pin = re.search(r"deep_reasoner_beta@([0-9a-f]{40})", pyproject.read_text())[1]
    assert re.fullmatch(rf"\d+\.\d+\.\d+\+{pin[:7]}", shapes.deep_reasoner_build())


def test_namespace_config_inlines_decompositions_in_attachment_order():
    second = json.dumps({**EXAMPLE, "name": "second"})
    bodies = [
        shapes.validate_decomposition(t).yaml for t in (second, json.dumps(EXAMPLE))
    ]
    config = shapes.namespace_config("name: a\n", bodies)
    assert [d.name for d in config.decompositions] == ["second", "catalog lookup"]
