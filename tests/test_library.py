import socket
from contextlib import closing
from pathlib import Path

import pytest
from deep_reasoner.config import resolve_api_key
from deep_reasoner.namespaces import ROOT, build_registry
from deep_reasoner.tools import load_tool_factory
from deep_reasoner.v2 import DeepReasoner
from deep_reasoner.v2.cli import V2Config, build_reasoner, close_run

from deep_reasoning.library import (
    LibraryError,
    default_namespace,
    engine_config,
    import_config,
    open_library,
)

FAKE_KEY = "sk-test-not-a-real-key"
ADVISORS_NAMESPACES = {"root", "router", "course_advisor", "health_advisor"}
ROUTER_DECOMPOSITIONS = [
    "route a course question",
    "route a wellbeing question",
    "decline anything else",
]


@pytest.fixture
def no_network(monkeypatch):
    def refuse(sock, address):
        raise AssertionError(f"tried to connect to {address}")

    monkeypatch.setattr(socket.socket, "connect", refuse)


def run_config(library, tmp_path, namespace=ROOT):
    return V2Config.model_validate(
        engine_config(library, namespace, tmp_path / "tools")
    )


def import_into(library, config):
    with closing(open_library(library)) as connection:
        return import_config(connection, config)


def dump(library):
    with closing(open_library(library)) as connection:
        return list(connection.iterdump())


def test_a_fresh_library_has_root_and_runs_on_gpt_6_luna_with_the_openai_key(
    library, tmp_path, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.delenv("NOVITA_API_KEY", raising=False)
    config = run_config(library, tmp_path)
    assert list(config.namespaces) == [ROOT]
    assert default_namespace(library) == ROOT
    assert config.model == "gpt-6-luna"
    assert config.client.api_key_env == "OPENAI_API_KEY"
    assert resolve_api_key(config.client) == FAKE_KEY
    assert FAKE_KEY.encode() not in library.read_bytes()


def test_import_brings_the_configs_namespaces_decompositions_and_prompt(
    imported, tmp_path
):
    config = run_config(imported, tmp_path)
    router = config.namespaces["router"]
    assert set(config.namespaces) == ADVISORS_NAMESPACES
    assert [each.name for each in router.decompositions] == ROUTER_DECOMPOSITIONS
    assert router.spawn == ["course_advisor", "health_advisor"]
    assert config.namespaces["course_advisor"].vars["catalog"]["CS201"]["prereqs"] == [
        "CS101"
    ]
    assert config.system_prompt.startswith("You solve each request")
    assert default_namespace(imported) == "router"


def test_import_keeps_the_librarys_model_and_key(imported, tmp_path):
    config = run_config(imported, tmp_path)
    assert config.model == "gpt-6-luna"
    assert config.client.api_key_env == "OPENAI_API_KEY"
    assert config.llm_kwargs == {}


def test_import_replaces_same_named_items_and_keeps_the_rest(imported, tmp_path):
    newer = tmp_path / "newer.yaml"
    newer.write_text(
        "max_iter: 3\n"
        "namespaces:\n"
        "  router:\n"
        "    spawn: [course_advisor]\n"
        "    decompositions:\n"
        "      - name: decline anything else\n"
        '        messages: [{role: user, content: "Only courses, please."}]\n'
    )
    import_into(imported, newer)
    config = run_config(imported, tmp_path)
    router = config.namespaces["router"]
    assert router.spawn == ["course_advisor"]
    assert [each.name for each in router.decompositions] == ROUTER_DECOMPOSITIONS
    assert router.decompositions[-1].messages[0].content == "Only courses, please."
    assert config.max_iter == 3
    assert config.namespaces[ROOT].tools == ["llm"]
    assert set(config.namespaces) == ADVISORS_NAMESPACES


def test_a_failed_import_leaves_the_library_unchanged(imported, tmp_path):
    broken = tmp_path / "broken.yaml"
    broken.write_text(
        "max_iter: 1\nnamespaces:\n  router: {tools: [ghost]}\n  extra: {}\n"
    )
    before = dump(imported)
    with pytest.raises(ValueError, match="grants unknown tool 'ghost'"):
        import_into(imported, broken)
    assert dump(imported) == before


@pytest.mark.parametrize(
    ("block", "files", "problem"),
    [
        (
            "{factory: build, factory_from: ./broken.py}",
            {"broken.py": "def build(:\n"},
            "broken.py is not valid Python",
        ),
        (
            "{factory: telepathy}",
            {},
            'names factory "telepathy", which is not built in',
        ),
    ],
)
def test_import_refuses_a_tool_the_engine_could_not_build(
    library, tmp_path, block, files, problem
):
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    config = tmp_path / "tool.yaml"
    config.write_text(f"tools:\n  mine: {block}\n")
    with pytest.raises(LibraryError, match=problem):
        import_into(library, config)


def test_a_custom_tools_source_round_trips_and_the_engine_loads_its_factory(
    library, waitlist, tmp_path
):
    import_into(library, waitlist)
    block = engine_config(library, ROOT, tmp_path / "tools")["tools"]["waitlist"]
    written = block["factory_from"]
    assert Path(written).read_text() == (waitlist.parent / "tools.py").read_text()
    build = load_tool_factory("waitlist", block["factory"], written, None)
    queue = build(None, {"capacity": 1}).value
    assert queue.join("ada", "CS201") == "enrolled"
    assert queue.join("grace", "CS201") == "waitlisted at 1"


def test_the_engine_config_builds_a_registry_and_a_reasoner_without_a_model_call(
    library, advisors, waitlist, tmp_path, monkeypatch, no_network
):
    import_into(library, waitlist)
    import_into(library, advisors)
    config = run_config(library, tmp_path, "course_advisor")
    registry = build_registry(
        inline=list(config.namespaces.values()), default_repl=config.repl
    )
    lookup = registry.resolve("course_advisor").decompositions
    assert [each.name for each in lookup] == ["catalog lookup"]
    assert registry.resolve("course_advisor").tools == ["llm"]
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    monkeypatch.chdir(tmp_path)
    reasoner, _alias = build_reasoner(config, run_dir=tmp_path / "run")
    assert isinstance(reasoner, DeepReasoner)
    assert config.entry_namespace == "course_advisor"
    close_run(reasoner)
