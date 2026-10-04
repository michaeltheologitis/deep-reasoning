import copy

import pytest

from deep_reasoning.library import LibraryImportError
from tests.library.conftest import ROUTER, example, text, write_config


def test_import_creates_every_entity_in_one_revision(lib, router):
    report = lib.import_config(router)
    assert report.source == router and report.rev == 2
    assert [(c.kind, c.name, c.version, c.created) for c in report.changed] == [
        ("decomposition", "route a course question", 1, True),
        ("decomposition", "decline", 1, True),
        ("decomposition", "catalog lookup", 1, True),
        ("namespace", "root", 2, False),
        ("namespace", "router", 1, True),
        ("namespace", "courses", 1, True),
        ("profile", "profile", 2, False),
    ]
    assert report.unchanged == []
    assert lib.rev() == 2
    assert lib.profile().default_namespace == "router"
    assert lib.namespace("router").decompositions == [
        "route a course question",
        "decline",
    ]
    assert lib.namespace("router").data == {"name": "router", "spawn": ["courses"]}
    assert lib.profile().data["client"] == ROUTER["client"]
    assert lib.history("namespace", "router")[0].action == "import"


def test_reimporting_the_same_config_changes_nothing(lib, router):
    lib.import_config(router)
    report = lib.import_config(router.parent)
    assert report.rev is None and report.changed == []
    assert len(report.unchanged) == 7
    assert lib.rev() == 2


def test_import_never_deletes(lib, router, tmp_path):
    lib.put_namespace("name: mine")
    lib.put_decomposition(text(example("my own")), namespaces=["mine"])
    lib.import_config(router)
    other = write_config(
        tmp_path / "other",
        {"system_prompt": "s", "namespaces": {"elsewhere": {"tools": ["llm"]}}},
    )
    lib.import_config(other)
    assert [ns.name for ns in lib.namespaces()] == [
        "root",
        "mine",
        "router",
        "courses",
        "elsewhere",
    ]
    assert lib.namespace("mine").decompositions == ["my own"]
    assert lib.namespace("router").decompositions == [
        "route a course question",
        "decline",
    ]


def test_import_replaces_what_the_config_names(lib, router, tmp_path):
    lib.import_config(router)
    lib.put_decomposition(text(example("decline")), use_when="off-topic questions")
    changed = copy.deepcopy(ROUTER)
    changed["max_iter"] = 9
    changed["namespaces"]["router"]["decompositions"] = [example("decline", "Weather?")]
    report = lib.import_config(write_config(tmp_path / "changed", changed))
    assert {(c.kind, c.name) for c in report.changed} == {
        ("decomposition", "decline"),
        ("namespace", "router"),
        ("profile", "profile"),
    }
    assert lib.profile().data["max_iter"] == 9
    assert lib.namespace("router").decompositions == ["decline"]
    assert lib.decomposition("decline").data["messages"][0]["content"] == "Weather?"
    assert lib.decomposition("decline").use_when == "off-topic questions"
    assert lib.decomposition("route a course question").namespaces == []


def test_compose_is_flattened(lib, tmp_path):
    main = write_config(
        tmp_path / "composed",
        {"_compose": ["client.yaml"], "model": "m", "system_prompt": "s"},
        **{"client.yaml": {"client": {"base_url": "http://x/v1"}, "max_iter": 3}},
    )
    lib.import_config(main)
    assert lib.profile().data == {
        "model": "m",
        "max_iter": 3,
        "system_prompt": "s",
        "client": {"base_url": "http://x/v1"},
    }


def test_a_namespaces_dir_is_layered_under_the_inline_namespaces(lib, tmp_path):
    main = write_config(
        tmp_path / "layered",
        {
            "system_prompt": "s",
            "namespaces_dir": "ns",
            "namespaces": {"b": {"tools": ["llm"]}},
        },
        **{
            "ns__a.yaml": {"vars": {"x": 1}},
            "ns__b.yaml": {"vars": {"replaced": True}},
            "ns__a__deep.yaml": {"decompositions": [example("deep")]},
        },
    )
    lib.import_config(main)
    assert [ns.name for ns in lib.namespaces()] == ["root", "a.deep", "a", "b"]
    assert lib.namespace("b").data == {"name": "b", "tools": ["llm"]}
    assert lib.namespace("a.deep").decompositions == ["deep"]


def test_one_name_with_two_bodies_is_refused_naming_both_places(lib, tmp_path):
    config = {
        "system_prompt": "s",
        "decompositions": [example("lookup")],
        "namespaces": {"a": {"decompositions": [example("lookup", "Different?")]}},
    }
    main = write_config(tmp_path / "twice", config)
    with pytest.raises(LibraryImportError) as raised:
        lib.import_config(main)
    assert str(raised.value) == (
        f"{main} defines two different decompositions named 'lookup' (in the top level and "
        "in namespace 'a'). The library keeps one decomposition per name: rename one and "
        "import again."
    )
    assert lib.rev() == 1


def test_one_name_with_one_body_in_two_places_is_one_decomposition(lib, tmp_path):
    shared = example("lookup")
    config = {
        "system_prompt": "s",
        "decompositions": [shared],
        "namespaces": {
            "a": {"decompositions": [shared]},
            "b": {"decompositions": [shared]},
        },
    }
    lib.import_config(write_config(tmp_path / "shared", config))
    record = lib.decomposition("lookup")
    assert (record.namespaces, record.top_level) == (["a", "b"], True)


def test_factory_from_is_read_into_the_library(lib, tmp_path):
    source = "from deep_reasoner.primitives import Func\r\n\r\ndef make(client, cfg):\r\n    ...\r\n"
    main = write_config(
        tmp_path / "tooled",
        {
            "system_prompt": "s",
            "tools": {
                "waitlist": {
                    "factory": "make",
                    "factory_from": "./lib/tools.py",
                    "capacity": 2,
                }
            },
            "namespaces": {"root": {"tools": ["waitlist"]}},
        },
    )
    (main.parent / "lib").mkdir()
    (main.parent / "lib" / "tools.py").write_bytes(source.encode())
    lib.import_config(main)
    tool = lib.tool("waitlist")
    assert tool.source == source
    assert tool.data == {
        "factory": "make",
        "factory_from": "tools/waitlist.py",
        "capacity": 2,
    }
    assert tool.granted_in == ["root"]


def test_a_missing_factory_file_is_refused(lib, tmp_path):
    main = write_config(
        tmp_path / "missing",
        {
            "system_prompt": "s",
            "tools": {"w": {"factory": "make", "factory_from": "gone.py"}},
        },
    )
    with pytest.raises(LibraryImportError) as raised:
        lib.import_config(main)
    assert str(raised.value) == (
        f"Tool 'w': factory_from 'gone.py' resolved to {main.parent / 'gone.py'}, which "
        "does not exist."
    )


def test_a_config_deep_reasoner_cannot_load_is_refused_with_its_message(lib, tmp_path):
    main = write_config(tmp_path / "bad", {"system_prompt": "s", "max_iter": "many"})
    with pytest.raises(LibraryImportError) as raised:
        lib.import_config(main)
    assert str(raised.value).startswith(
        f"{main} is not a dr config deep_reasoner can load: ValidationError: "
    )
    assert "max_iter" in str(raised.value)
