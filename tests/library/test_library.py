import pytest

from deep_reasoning.library import (
    Library,
    LibraryConflict,
    LibraryNotFound,
    LibraryRefused,
    LibraryValidationError,
    shapes,
)
from tests.library.conftest import example, text


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


def test_put_then_get_returns_the_canonical_record(lib):
    lib.put_namespace("{name: router}")
    saved = lib.put_decomposition(
        '{"name": "summarize then rank", "messages": [{"role": "user", "content": "hi"}]}',
        use_when="comparing many courses",
        hint="what to compare",
        namespaces=["router"],
    )
    got = lib.decomposition("summarize-then-rank")
    assert got == lib.decomposition("summarize then rank") == saved
    assert (got.name, got.slug, got.version, got.rev) == (
        "summarize then rank",
        "summarize-then-rank",
        1,
        3,
    )
    assert (
        got.yaml
        == "name: summarize then rank\nmessages:\n- role: user\n  content: hi\n"
    )
    assert got.data["messages"] == [{"role": "user", "content": "hi"}]
    assert (got.use_when, got.hint, got.namespaces, got.top_level) == (
        "comparing many courses",
        "what to compare",
        ["router"],
        False,
    )


def test_every_save_is_a_new_version(lib):
    first = lib.put_decomposition(text(example("lookup")))
    second = lib.put_decomposition(text(example("lookup", "Another question?")))
    third = lib.put_decomposition(
        text(example("lookup", "Another question?")), use_when="x"
    )
    assert [first.version, second.version, third.version] == [1, 2, 3]
    assert [first.rev, second.rev, third.rev] == [2, 3, 4]


def test_an_unchanged_save_returns_the_head_and_makes_no_revision(lib):
    saved = lib.put_decomposition(text(example("lookup")), use_when="x")
    again = lib.put_decomposition(
        text(example("lookup")).replace("name: lookup", "name: 'lookup'"), use_when="x"
    )
    assert again == saved
    assert lib.rev() == 2


def test_use_when_and_hint_are_replaced_by_every_save(lib):
    lib.put_decomposition(text(example("lookup")), use_when="x", hint="y")
    again = lib.put_decomposition(text(example("lookup")), use_when="")
    assert (again.version, again.use_when, again.hint) == (2, None, None)


def test_a_stale_base_version_is_a_conflict_carrying_the_head(lib):
    lib.put_namespace("name: router")
    lib.put_decomposition(text(example("lookup")), namespaces=["router"])
    lib.put_decomposition(text(example("lookup", "Edited?")), base_version=1)
    with pytest.raises(LibraryConflict) as raised:
        lib.put_decomposition(text(example("lookup", "Mine?")), base_version=1)
    assert str(raised.value) == (
        "Decomposition 'lookup' is at version 2, not 1: it changed after you opened it. "
        "Reload it, or save over it with base_version=2."
    )
    assert raised.value.head == lib.decomposition("lookup")
    assert raised.value.head.namespaces == ["router"]
    assert raised.value.payload()["head"]["version"] == 2


def test_base_version_zero_refuses_an_existing_entry(lib):
    lib.put_decomposition(text(example("lookup")), base_version=0)
    with pytest.raises(LibraryConflict, match="already exists, at version 1") as raised:
        lib.put_decomposition(text(example("lookup", "Again?")), base_version=0)
    assert raised.value.head.version == 1
    assert lib.rev() == 2


def test_a_base_version_on_something_that_is_not_there_is_not_found(lib):
    with pytest.raises(LibraryNotFound, match="There is no decomposition 'lookup'"):
        lib.put_decomposition(text(example("lookup")), base_version=3)


def test_attaching_versions_the_namespace_and_appends_in_order(lib):
    lib.put_namespace("name: router")
    for name in ("b first", "a second", "c third"):
        lib.put_decomposition(text(example(name)), namespaces=["router"])
    router = lib.namespace("router")
    assert router.decompositions == ["b first", "a second", "c third"]
    assert router.version == 4
    assert router.yaml == "name: router\n"


def test_namespaces_is_the_exact_set_after_a_save(lib):
    for name in ("a", "b", "c"):
        lib.put_namespace(f"name: {name}")
    lib.put_decomposition(text(example("lookup")), namespaces=["a", "b"])
    lib.put_decomposition(text(example("other")), namespaces=["b"])
    saved = lib.put_decomposition(text(example("lookup")), namespaces=["c", "b"])
    assert saved.namespaces == ["b", "c"]
    assert [lib.namespace(n).decompositions for n in ("a", "b", "c")] == [
        [],
        ["lookup", "other"],
        ["lookup"],
    ]
    kept = lib.put_decomposition(text(example("lookup", "Edited?")))
    assert kept.namespaces == ["b", "c"]


def test_top_level_is_the_profiles_list(lib):
    saved = lib.put_decomposition(text(example("triage")), top_level=True)
    assert saved.top_level and lib.profile().decompositions == ["triage"]
    assert not lib.put_decomposition(text(example("triage")), top_level=False).top_level
    assert lib.profile().decompositions == []


def test_putting_a_namespace_sets_its_list_only_when_given(lib):
    lib.put_decomposition(text(example("x")))
    lib.put_decomposition(text(example("y")))
    lib.put_namespace("name: a", decompositions=["y", "x"])
    assert lib.put_namespace("name: a\ntools: [llm]").decompositions == ["y", "x"]
    with pytest.raises(LibraryValidationError, match="There is no decomposition 'z'"):
        lib.put_namespace("name: a", decompositions=["z"])
    with pytest.raises(
        LibraryValidationError, match="'x' is listed twice in namespace 'a'."
    ):
        lib.put_namespace("name: a", decompositions=["x", "x"])


def test_deleting_a_decomposition_detaches_it_everywhere(lib):
    lib.put_namespace("name: a")
    lib.put_decomposition(text(example("keep")), namespaces=["a"])
    lib.put_decomposition(text(example("drop")), namespaces=["a"], top_level=True)
    tombstone = lib.delete("decomposition", "drop")
    assert (tombstone.deleted, tombstone.version, tombstone.slug) == (True, 2, "drop")
    assert lib.namespace("a").decompositions == ["keep"]
    assert lib.profile().decompositions == []
    assert [d.name for d in lib.decompositions()] == ["keep"]
    assert tombstone.rev == lib.namespace("a").rev == lib.profile().rev


def test_deleting_a_tool_ungrants_it_everywhere(lib):
    lib.put_namespace("name: a\ntools: [llm]")
    lib.put_tool(
        "waitlist",
        "factory: make\n",
        source="def make(c, p): ...\n",
        granted_in=["a", "root"],
    )
    assert lib.namespace("a").data["tools"] == ["llm", "waitlist"]
    assert lib.tool("waitlist").granted_in == ["root", "a"]
    lib.delete("tool", "waitlist")
    assert lib.namespace("a").data["tools"] == ["llm"]
    assert "tools" not in lib.namespace("root").data
    with pytest.raises(LibraryNotFound):
        lib.tool("waitlist")


def test_granted_in_is_the_exact_set_after_a_save(lib):
    lib.put_namespace("name: a")
    lib.put_namespace("name: b")
    lib.put_tool("search", "factory: llm\n", granted_in=["a", "b"])
    saved = lib.put_tool("search", "factory: llm\n", granted_in=["b"])
    assert saved.granted_in == ["b"]
    assert "tools" not in lib.namespace("a").data


@pytest.mark.parametrize("loc", ["namespaces", "granted_in"])
def test_a_namespace_that_is_not_there_cannot_be_attached_to_or_granted_in(lib, loc):
    save = {
        "namespaces": lambda: lib.put_decomposition(
            text(example("lookup")), namespaces=["root", "gone"]
        ),
        "granted_in": lambda: lib.put_tool(
            "search", "factory: llm\n", granted_in=["root", "gone"]
        ),
    }[loc]
    with pytest.raises(LibraryValidationError) as raised:
        save()
    sentence = "There is no namespace 'gone' in the library."
    assert str(raised.value) == sentence
    assert [e.model_dump() for e in raised.value.errors] == [
        {"loc": loc, "msg": sentence}
    ]
    assert lib.rev() == 1


def test_root_the_default_and_a_parent_cannot_be_deleted(lib):
    lib.put_namespace("name: a")
    lib.put_namespace("name: a.b")
    lib.put_namespace("name: c")
    lib.put_profile("entry_namespace: c")
    refusals = {
        "root": "root cannot be deleted: every namespace inherits from it.",
        "c": "'c' is the namespace new conversations start in; choose another one first.",
        "a": "'a' has namespaces under it (a.b); delete them first.",
    }
    for name, sentence in refusals.items():
        with pytest.raises(LibraryRefused) as raised:
            lib.delete("namespace", name)
        assert str(raised.value) == sentence
    lib.delete("namespace", "a.b")
    lib.delete("namespace", "a")
    assert [ns.name for ns in lib.namespaces()] == ["root", "c"]


def test_a_namespace_needs_its_parent(lib):
    with pytest.raises(LibraryValidationError) as raised:
        lib.put_namespace("name: math.geometry")
    assert str(raised.value) == (
        "Namespace 'math.geometry' needs its parent 'math', which is not in the library."
    )
    assert lib.rev() == 1


def test_the_default_namespace_must_be_in_the_library(lib):
    with pytest.raises(
        LibraryValidationError, match="The default namespace 'x' is not"
    ):
        lib.put_profile("entry_namespace: x")


def test_two_names_with_one_slug_are_refused(lib):
    lib.put_decomposition(text(example("Rank courses")))
    with pytest.raises(LibraryValidationError) as raised:
        lib.put_decomposition(text(example("rank  courses!")))
    assert str(raised.value) == (
        "'rank  courses!' would be the slash command /rank-courses, which 'Rank courses' "
        "already is. Give it another name."
    )


def test_deleted_and_recreated_continues_its_version_numbers(lib):
    lib.put_decomposition(text(example("lookup")))
    lib.delete("decomposition", "lookup")
    again = lib.put_decomposition(text(example("lookup")), base_version=0)
    assert again.version == 3


def test_history_lists_tombstones(lib):
    lib.put_decomposition(text(example("lookup")), use_when="first")
    lib.put_decomposition(text(example("lookup", "Second?")), use_when="second")
    lib.delete("decomposition", "lookup")
    history = lib.history("decomposition", "lookup")
    assert [(h.version, h.deleted, h.use_when) for h in history] == [
        (3, True, None),
        (2, False, "second"),
        (1, False, "first"),
    ]
    assert [h.action for h in history] == [
        "delete decomposition",
        "put decomposition",
        "put decomposition",
    ]
    assert history[1].deep_reasoner == shapes.deep_reasoner_build()
    assert lib.history("decomposition", "lookup") == history


def test_state_as_of_an_old_revision(lib):
    lib.put_namespace("name: a")
    lib.put_namespace("name: a\ntools: [llm]")
    assert lib.state(rev=2).namespaces["a"].data == {"name": "a"}
    assert lib.state().namespaces["a"].data == {"name": "a", "tools": ["llm"]}


@pytest.mark.parametrize("rev", [0, 3])
def test_a_revision_the_library_has_not_reached_is_not_found(lib, rev):
    lib.put_namespace("name: a")
    with pytest.raises(LibraryNotFound) as raised:
        lib.state(rev=rev)
    assert (
        str(raised.value)
        == f"There is no revision {rev}: the library is at revision 2."
    )


def test_validate_reports_without_saving(lib):
    result = lib.validate("decomposition", "name: x\nmessages: []")
    assert result.model_dump() == {
        "ok": False,
        "message": "'x' is not a valid deep_reasoner Decomposition:\n"
        "  messages: List should have at least 1 item after validation, not 0",
        "errors": [
            {
                "loc": "messages",
                "msg": "List should have at least 1 item after validation, not 0",
            }
        ],
        "warnings": [],
        "name": "x",
        "slug": "x",
        "yaml": None,
    }
    ok = lib.validate("decomposition", text(example("Rank it")))
    assert (ok.ok, ok.slug, ok.yaml) == (
        True,
        "rank-it",
        lib.validate("decomposition", ok.yaml).yaml,
    )
    assert lib.validate("tool", "factory: llm\n", name="search").ok
    assert lib.rev() == 1
