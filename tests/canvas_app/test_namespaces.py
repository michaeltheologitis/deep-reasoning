import pytest
from playwright.sync_api import Page, expect

from tests.canvas_app.conftest import get_json, stale_head

pytestmark = pytest.mark.browser


def select(page: Page, namespace: str) -> None:
    page.get_by_test_id(f"dr-node-{namespace}").click()
    expect(page.get_by_test_id("dr-namespace-title")).to_have_text(namespace)


def edit_value(page: Page, editor: str, value: str) -> None:
    page.get_by_test_id(f"dr-value-{editor}").fill(value)
    page.get_by_test_id("dr-value-save").click()


def test_the_tree_follows_dotted_names_and_marks_the_default(open_ui):
    page = open_ui(tab="namespaces")
    nodes = page.locator("[data-testid^='dr-node-']")
    expect(nodes).to_have_count(5)
    assert [n.get_attribute("data-testid") for n in nodes.all()] == [
        "dr-node-run-settings",
        "dr-node-root",
        "dr-node-router",
        "dr-node-router.archive",
        "dr-node-course_advisor",
    ]
    nested = page.get_by_test_id("dr-tree-router").get_by_test_id(
        "dr-node-router.archive"
    )
    expect(nested).to_be_visible()
    expect(page.get_by_test_id("dr-tree-router.archive")).not_to_contain_text(
        "course_advisor"
    )
    expect(page.get_by_test_id("dr-node-router")).to_contain_text("★")
    expect(page.get_by_test_id("dr-node-course_advisor")).not_to_contain_text("★")
    expect(page.get_by_test_id("dr-namespace-title")).to_have_text("router")
    expect(page.get_by_test_id("dr-default-badge")).to_have_text(
        "★ New conversations start here"
    )


def test_each_field_shows_its_effective_value_and_source(open_ui):
    page = open_ui(tab="namespaces", focus="course_advisor")
    expect(page.get_by_test_id("dr-namespace-title")).to_have_text("course_advisor")
    sources = {
        "repl": "From the run settings",
        "reasoner": "Not set: deep_reasoner's default",
        "spawn": "Not set: deep_reasoner's default",
    }
    for field, source in sources.items():
        expect(page.get_by_test_id(f"dr-source-{field}")).to_have_text(source)
    expect(page.get_by_test_id("dr-field-repl")).to_contain_text("type: local")
    expect(page.get_by_test_id("dr-field-spawn")).to_contain_text("Any namespace")
    expect(page.get_by_test_id("dr-tool-source-llm")).to_have_text(
        "Inherited from root"
    )
    expect(page.get_by_test_id("dr-tool-source-word_count")).to_have_text(
        "Granted here"
    )
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Northwind")
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Inherited from root")
    expect(page.get_by_test_id("dr-suffix-root")).to_contain_text("Answer briefly.")
    expect(page.get_by_test_id("dr-decomposition-catalog-lookup")).to_contain_text(
        "Inherited from root"
    )
    select(page, "router")
    expect(page.get_by_test_id("dr-field-spawn")).to_contain_text("course_advisor")
    expect(page.get_by_test_id("dr-source-spawn")).to_have_text("Overridden here")
    expect(page.get_by_test_id("dr-decomposition-summarize-then-rank")).to_contain_text(
        "Attached here"
    )
    select(page, "root")
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Set here")


def test_override_sets_a_field_here_and_reset_removes_it(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="course_advisor")
    page.get_by_test_id("dr-override-repl").click()
    expect(page.get_by_test_id("dr-value-repl")).to_have_value("type: local\n")
    edit_value(page, "repl", "type: restricted\n")
    expect(page.get_by_test_id("dr-source-repl")).to_have_text("Overridden here")
    expect(page.get_by_test_id("dr-field-repl")).to_contain_text("type: restricted")
    library = library_server.library()
    assert library.namespace("course_advisor").data["repl"] == {"type": "restricted"}
    page.get_by_test_id("dr-reset-repl").click()
    expect(page.get_by_test_id("dr-source-repl")).to_have_text("From the run settings")
    assert "repl" not in library.namespace("course_advisor").data
    page.get_by_test_id("dr-override-spawn").click()
    page.get_by_test_id("dr-spawn-router").check()
    page.get_by_test_id("dr-value-save").click()
    expect(page.get_by_test_id("dr-source-spawn")).to_have_text("Overridden here")
    assert library.namespace("course_advisor").data["spawn"] == ["router"]


def test_a_variable_is_overridden_and_reset_key_by_key(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="course_advisor")
    page.get_by_test_id("dr-override-var-school").click()
    edit_value(page, "var-school", "Southwind")
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Overridden here")
    page.get_by_test_id("dr-add-variable").click()
    page.get_by_test_id("dr-new-variable").fill("level")
    edit_value(page, "new-variable", "3")
    expect(page.get_by_test_id("dr-var-level")).to_contain_text("Overridden here")
    library = library_server.library()
    assert library.namespace("course_advisor").data["vars"] == {
        "school": "Southwind",
        "level": 3,
    }
    page.get_by_test_id("dr-reset-var-school").click()
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Inherited from root")
    expect(page.get_by_test_id("dr-var-school")).to_contain_text("Northwind")
    assert library.namespace("course_advisor").data["vars"] == {"level": 3}


def test_a_tool_granted_here_adds_to_the_inherited_ones(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="router")
    expect(page.get_by_test_id("dr-grant-llm")).to_be_checked()
    expect(page.get_by_test_id("dr-grant-llm")).to_be_disabled()
    page.get_by_test_id("dr-grant-word_count").check()
    expect(page.get_by_test_id("dr-tool-source-word_count")).to_have_text(
        "Granted here"
    )
    library = library_server.library()
    assert library.namespace("router").data["tools"] == ["word_count"]
    assert [t.name for t in library.effective("router").tools] == ["llm", "word_count"]
    page.get_by_test_id("dr-grant-word_count").uncheck()
    expect(page.get_by_test_id("dr-tool-source-word_count")).to_have_count(0)
    assert "tools" not in library.namespace("router").data


def test_attach_and_detach_change_only_this_namespaces_list(open_ui, library_server):
    library = library_server.library()
    before = library.namespace("course_advisor").yaml
    page = open_ui(tab="namespaces", focus="course_advisor")
    page.get_by_test_id("dr-attach").click()
    page.get_by_test_id("dr-attach-choice").select_option("summarize then rank")
    page.get_by_test_id("dr-attach-confirm").click()
    expect(page.get_by_test_id("dr-decomposition-summarize-then-rank")).to_contain_text(
        "Attached here"
    )
    after = library.namespace("course_advisor")
    assert (after.decompositions, after.yaml) == (["summarize then rank"], before)
    assert library.namespace("router").decompositions == ["summarize then rank"]
    page.get_by_test_id("dr-detach-summarize-then-rank").click()
    expect(page.get_by_test_id("dr-decomposition-summarize-then-rank")).to_have_count(0)
    assert library.namespace("course_advisor").decompositions == []


def test_start_new_conversations_here_moves_the_default(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="course_advisor")
    page.get_by_test_id("dr-make-default").click()
    expect(page.get_by_test_id("dr-default-badge")).to_be_visible()
    expect(page.get_by_test_id("dr-node-course_advisor")).to_contain_text("★")
    expect(page.get_by_test_id("dr-node-router")).not_to_contain_text("★")
    assert (
        get_json(f"{library_server.url}/health")["default_namespace"]
        == "course_advisor"
    )
    profile = library_server.library().profile().data
    assert (profile["entry_namespace"], profile["max_iter"]) == ("course_advisor", 6)


def test_adding_and_deleting_a_namespace(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="router")
    page.get_by_test_id("dr-add-namespace").click()
    expect(page.get_by_test_id("dr-new-namespace")).to_have_value("router.")
    page.get_by_test_id("dr-new-namespace").fill("nowhere.child")
    page.get_by_test_id("dr-create-namespace").click()
    expect(page.get_by_test_id("dr-message")).to_contain_text(
        "Namespace 'nowhere.child' needs its parent 'nowhere', which is not in the library."
    )
    page.get_by_test_id("dr-new-namespace").fill("router.next")
    page.get_by_test_id("dr-create-namespace").click()
    expect(page.get_by_test_id("dr-namespace-title")).to_have_text("router.next")
    expect(
        page.get_by_test_id("dr-tree-router").get_by_test_id("dr-node-router.next")
    ).to_be_visible()
    library = library_server.library()
    assert "router.next" in [n.name for n in library.namespaces()]
    page.get_by_test_id("dr-delete-namespace").click()
    expect(page.get_by_test_id("dr-confirm")).to_contain_text(
        "Delete namespace 'router.next'? Its decompositions stay in the Library."
    )
    page.get_by_test_id("dr-confirm-yes").click()
    expect(page.get_by_test_id("dr-node-router.next")).to_have_count(0)
    assert "router.next" not in [n.name for n in library.namespaces()]
    refusals = {
        "root": "root cannot be deleted: every namespace inherits from it.",
        "router": "'router' is the namespace new conversations start in; choose another "
        "one first.",
    }
    for namespace, refusal in refusals.items():
        select(page, namespace)
        page.get_by_test_id("dr-delete-namespace").click()
        page.get_by_test_id("dr-confirm-yes").click()
        expect(page.get_by_test_id("dr-message")).to_have_text(refusal)
    page.get_by_test_id("dr-node-course_advisor").click()
    page.get_by_test_id("dr-add-namespace").click()
    page.get_by_test_id("dr-new-namespace").fill("course_advisor.deep")
    page.get_by_test_id("dr-create-namespace").click()
    select(page, "course_advisor")
    page.get_by_test_id("dr-delete-namespace").click()
    page.get_by_test_id("dr-confirm-yes").click()
    expect(page.get_by_test_id("dr-message")).to_have_text(
        "'course_advisor' has namespaces under it (course_advisor.deep); delete them first."
    )


@pytest.mark.parametrize("selected", ["root", "run-settings"])
def test_add_namespace_is_not_prefilled_under_root_or_run_settings(open_ui, selected):
    page = open_ui(tab="namespaces", focus=selected)
    page.get_by_test_id("dr-add-namespace").click()
    expect(page.get_by_test_id("dr-new-namespace")).to_have_value("")


def test_run_settings_edit_the_profile(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="run-settings")
    expect(page.get_by_test_id("dr-field-entry_namespace")).to_have_count(0)
    page.get_by_test_id("dr-edit-max_iter").click()
    edit_value(page, "max_iter", "8")
    expect(page.get_by_test_id("dr-field-max_iter")).to_contain_text("8")
    page.get_by_test_id("dr-reset-max_depth").click()
    expect(page.get_by_test_id("dr-field-max_depth")).to_have_count(0)
    profile = library_server.library().profile().data
    assert (profile["max_iter"], profile["entry_namespace"]) == (8, "router")
    assert "max_depth" not in profile
    page.get_by_test_id("dr-add-setting").click()
    page.get_by_test_id("dr-new-setting").fill("tools")
    edit_value(page, "new-setting", "{}")
    expect(page.get_by_test_id("dr-message")).to_contain_text(
        "'tools' is not part of the profile: namespaces, decompositions and tools are "
        "stored as entries of their own."
    )
    page.get_by_test_id("dr-new-setting").fill("system_prompt")
    edit_value(page, "new-setting", "Think, then act.\nOne block per turn.")
    expect(page.get_by_test_id("dr-field-system_prompt")).to_contain_text(
        "Think, then act."
    )
    prompt = library_server.library().profile().data["system_prompt"]
    assert prompt == "Think, then act.\nOne block per turn."


def test_yaml_values_mean_what_dr_reads(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="router")
    page.get_by_test_id("dr-add-variable").click()
    page.get_by_test_id("dr-new-variable").fill("enabled")
    edit_value(page, "new-variable", "on")
    expect(page.get_by_test_id("dr-var-enabled")).to_contain_text("true")
    namespace = library_server.library().namespace("router")
    assert namespace.data["vars"]["enabled"] is True
    assert "enabled: true" in namespace.yaml


def test_keys_the_panel_does_not_show_survive_an_override(open_ui, library_server):
    page = open_ui(tab="namespaces", focus="router")
    page.get_by_test_id("dr-override-reasoner").click()
    edit_value(page, "reasoner", "kind: chat\n")
    expect(page.get_by_test_id("dr-source-reasoner")).to_have_text("Overridden here")
    assert library_server.library().namespace("router").data == {
        "name": "router",
        "vars": {"max_courses": 3},
        "spawn": ["course_advisor"],
        "reasoner": {"kind": "chat"},
    }


def test_a_namespace_whose_inheritance_cannot_be_resolved_says_why(
    open_ui, library_server
):
    stale_head(library_server)
    page = open_ui(tab="namespaces", focus="course_advisor")
    expect(page.get_by_test_id("dr-effective-failed")).to_contain_text(
        "Namespace 'router.archive' version 2 no longer validates"
    )
    expect(page.get_by_test_id("dr-delete-namespace")).to_be_visible()
    expect(page.get_by_test_id("dr-backend-lost")).to_have_count(0)
