import math
import socket
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest
from deep_reasoner.config import load_cli_config, resolve_api_key
from deep_reasoner.namespaces import ROOT, build_registry
from deep_reasoner.tools import load_tool_factory
from deep_reasoner.v2 import DeepReasoner
from deep_reasoner.v2.cli import (
    V2Config,
    build_namespace_registry,
    build_reasoner,
    close_run,
    declared_tool_names,
)

from deep_reasoning.library import (
    UPSERT_NAMESPACE,
    UPSERT_SETTING,
    LibraryError,
    add_decomposition,
    default_namespace,
    dump,
    engine_config,
    import_config,
    open_library,
    panel,
    stored_config,
    writing,
)

FAKE_KEY = "sk-test-not-a-real-key"
ADVISORS_NAMESPACES = {"root", "router", "course_advisor", "health_advisor"}
ROUTER_DECOMPOSITIONS = [
    "route a course question",
    "route a wellbeing question",
    "decline anything else",
]
TYPED = """system_prompt: |
  Solve it.
namespaces:
  root:
    vars: {by_year: {2024: 10}, due: 2026-10-25, cap: .inf}
    decompositions:
      - name: count
        messages:
          - {role: user, content: "How many?"}
          - role: assistant
            content: |
              <repl>
              FinalAnswer(3)
              </repl>
"""
ADDED = "name: added\nmessages: [{role: user, content: hi}]\n"
# What the app puts in for a chat on OpenAI's gpt-6-luna.
CHATS_MODEL = {
    "model": "gpt-6-luna",
    "client": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
}


@pytest.fixture
def no_network(monkeypatch):
    def refuse(sock, address):
        raise AssertionError(f"tried to connect to {address}")

    monkeypatch.setattr(socket.socket, "connect", refuse)


def run_config(library, tmp_path, namespace=ROOT):
    """The config of a run on gpt-6-luna, as the app makes it."""
    return V2Config.model_validate(
        engine_config(library, namespace, tmp_path / "tools") | CHATS_MODEL
    )


def import_into(library, config):
    with closing(open_library(library)) as connection:
        return import_config(connection, config)


def dumped(library):
    with closing(open_library(library)) as connection:
        return list(connection.iterdump())


def test_a_fresh_library_has_root_and_leaves_the_model_and_its_key_to_the_chat(
    library, tmp_path, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    config = engine_config(library, ROOT, tmp_path / "tools")
    assert list(config["namespaces"]) == [ROOT]
    assert default_namespace(library) == ROOT
    assert "model" not in config and "client" not in config
    assert resolve_api_key(run_config(library, tmp_path).client) == FAKE_KEY
    assert FAKE_KEY.encode() not in library.read_bytes()


def test_a_fresh_library_grants_llm_at_root_and_the_engine_accepts_it(
    library, tmp_path
):
    config = run_config(library, tmp_path)
    build_namespace_registry(config).check(declared_tool_names(config))
    assert config.namespaces[ROOT].tools == ["llm"]


def test_a_library_made_with_an_empty_root_is_given_llm_there_once(library, tmp_path):
    with closing(open_library(library)) as connection, writing(connection):
        connection.execute(UPSERT_NAMESPACE, (ROOT, dump({})))
    upgraded = dumped(library)
    assert dumped(library) == upgraded
    assert run_config(library, tmp_path).namespaces[ROOT].tools == ["llm"]


def test_a_read_only_library_with_an_empty_root_still_opens_as_it_is(
    library, monkeypatch
):
    with closing(open_library(library)) as connection, writing(connection):
        connection.execute(UPSERT_NAMESPACE, (ROOT, dump({})))
    connect = sqlite3.connect

    def read_only(path, **options):
        return connect(f"{Path(path).as_uri()}?mode=ro", uri=True, **options)

    monkeypatch.setattr(sqlite3, "connect", read_only)
    with closing(open_library(library)) as connection:
        assert stored_config(connection)["namespaces"][ROOT] == {"decompositions": []}


@pytest.mark.parametrize(
    "root",
    [
        "{tools: []}",
        "{vars: {term: fall}}",
        "{decompositions: [{name: hi, messages: [{role: user, content: hi}]}]}",
    ],
)
def test_a_root_that_was_imported_or_edited_keeps_what_it_has(library, tmp_path, root):
    written = tmp_path / "root.yaml"
    written.write_text(f"namespaces:\n  root: {root}\n")
    import_into(library, written)
    assert run_config(library, tmp_path).namespaces[ROOT].tools == []


def test_a_library_that_still_holds_a_model_and_client_opens_and_they_go_unread(
    library, tmp_path
):
    old = {"model": "gpt-4o", "client": {"base_url": "https://example.com/v1"}}
    with closing(open_library(library)) as connection, writing(connection):
        connection.executemany(
            UPSERT_SETTING, [(key, dump(value)) for key, value in old.items()]
        )
    with closing(open_library(library)) as connection:
        shown = panel(connection)
    config = engine_config(library, ROOT, tmp_path / "tools")
    assert "model" not in config and "client" not in config
    assert [row["label"] for row in shown["run_settings"]][:2] == [
        "max_iter",
        "max_depth",
    ]
    assert not {"model", "client"} & {row["label"] for row in shown["run_settings"]}


def test_a_fresh_library_carries_a_generic_repl_prompt(library, tmp_path):
    prompt = run_config(library, tmp_path).system_prompt
    assert "<repl>" in prompt
    assert "FinalAnswer" in prompt


def test_a_file_that_is_not_a_library_is_refused_and_left_alone(tmp_path):
    other = tmp_path / "chats.sqlite"
    with closing(sqlite3.connect(other)) as connection:
        connection.execute("CREATE TABLE chats (id TEXT)")
    before = other.read_bytes()
    with pytest.raises(LibraryError, match="is not a Library"):
        open_library(other)
    assert other.read_bytes() == before


def test_an_open_reader_does_not_hold_up_a_write(library):
    with closing(open_library(library)) as reader:
        stored_config(reader)
        with closing(open_library(library)) as writer:
            add_decomposition(writer, ROOT, ADDED)
        assert [
            each["name"]
            for each in stored_config(reader)["namespaces"][ROOT]["decompositions"]
        ] == ["added"]


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


def test_import_brings_no_model_or_client(library, tmp_path):
    written = tmp_path / "own_model.yaml"
    written.write_text(
        "model: qwen/qwen3-30b\nclient: {base_url: 'https://api.novita.ai/v3/openai'}\n"
    )
    import_into(library, written)
    config = engine_config(library, ROOT, tmp_path / "tools")
    assert "model" not in config and "client" not in config
    assert run_config(library, tmp_path).llm_kwargs == {}


def test_an_imported_llm_tool_runs_on_the_chats_model(library, tmp_path):
    written = tmp_path / "tiers.yaml"
    written.write_text(
        "models: {coder: {model: qwen/qwen3-coder-30b-a3b-instruct}}\n"
        "tools:\n"
        "  code_reviewer: {factory: llm, model: coder, system_prompt: Review it.}\n"
    )
    import_into(library, written)
    config = run_config(library, tmp_path)
    assert config.tools["code_reviewer"] == {
        "factory": "llm",
        "system_prompt": "Review it.",
    }
    assert "models" not in engine_config(library, ROOT, tmp_path / "tools")


def test_an_import_reads_back_as_the_engine_loads_the_config(library, tmp_path):
    written = tmp_path / "typed.yaml"
    written.write_text(TYPED)
    import_into(library, written)
    expected = load_cli_config(written, schema=V2Config)
    config = run_config(library, tmp_path)
    assert config.system_prompt == expected.system_prompt == "Solve it.\n"
    assert config.namespaces[ROOT].vars == expected.namespaces[ROOT].vars
    assert config.namespaces[ROOT].vars["by_year"][2024] == 10
    assert config.namespaces[ROOT].vars["due"] == date(2026, 10, 25)
    assert config.namespaces[ROOT].vars["cap"] == math.inf
    assert (
        config.namespaces[ROOT].decompositions
        == expected.namespaces[ROOT].decompositions
    )


def test_a_configs_run_level_openings_are_left_out(library, tmp_path):
    written = tmp_path / "openings.yaml"
    written.write_text(
        "decompositions:\n"
        "  - name: full_triage\n"
        "    messages: [{role: user, content: '{{ task }}'}]\n"
    )
    assert import_into(library, written)["decompositions"] == 0
    assert run_config(library, tmp_path).namespaces[ROOT].decompositions == []


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
    before = dumped(imported)
    with pytest.raises(ValueError, match="grants unknown tool 'ghost'"):
        import_into(imported, broken)
    assert dumped(imported) == before


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
        ("{factory: [a, b]}", {}, "factory and factory_from should be text"),
        (
            "{factory: build, factory_from: 5}",
            {},
            "factory and factory_from should be text",
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


def test_a_shared_librarys_tool_cannot_be_written_outside_the_tools_folder(
    library, tmp_path
):
    with closing(open_library(library)) as connection:
        connection.execute(
            "INSERT INTO tools VALUES (?, ?, ?)",
            ("../escaped", "factory: build\n", "def build(client, cfg): ...\n"),
        )
    with pytest.raises(LibraryError, match="needs a Python name"):
        engine_config(library, ROOT, tmp_path / "tools")
    assert not (tmp_path / "escaped.py").exists()


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
