from deep_reasoning.library import (
    Library,
)


def test_a_new_library_starts_from_the_starter(tmp_path):
    lib = Library.open(tmp_path / "library.sqlite")
    assert lib.rev() == 1
    assert lib.profile().data["model"] == "gpt-6-luna"
    assert lib.profile().data["client"]["api_key_env"] == "OPENAI_API_KEY"
    assert lib.namespace("root").data == {
        "name": "root",
        "repl": {"type": "local"},
        "tools": ["llm"],
    }
    assert lib.history("profile", "profile")[0].action == "create"


def test_a_bare_library_holds_an_empty_profile_and_root(lib):
    assert lib.rev() == 1
    assert lib.profile().yaml == "{}\n"
    assert lib.profile().default_namespace == "root"
    assert [ns.name for ns in lib.namespaces()] == ["root"]
    assert lib.decompositions() == [] and lib.tools() == []


def test_opening_an_existing_library_changes_nothing(lib):
    again = Library.open(lib.path)
    assert again.rev() == 1 and again.profile().yaml == "{}\n"
