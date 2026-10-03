import pytest
from playwright.sync_api import expect

from deep_reasoning.library import store
from tests.library.conftest import example, text

pytestmark = pytest.mark.browser


def test_decompositions_are_grouped_by_namespace_with_version_slash_command_and_use_when(
    open_ui,
):
    page = open_ui(tab="browse")
    groups = page.locator("[data-testid^='dr-group-']")
    expect(groups).to_have_count(5)
    assert [g.get_attribute("data-testid") for g in groups.all()] == [
        "dr-group-top-level",
        "dr-group-root",
        "dr-group-router",
        "dr-group-router.archive",
        "dr-group-course_advisor",
    ]
    rows = page.get_by_test_id("dr-group-router").locator("[data-testid^='dr-row-']")
    expect(rows).to_have_count(2)
    expect(rows.nth(0)).to_have_attribute("data-testid", "dr-row-router-catalog-lookup")
    row = page.get_by_test_id("dr-row-router-summarize-then-rank")
    for part in (
        "summarize then rank",
        "v1",
        "/summarize-then-rank",
        "comparing many courses",
    ):
        expect(row).to_contain_text(part)
    expect(page.get_by_test_id("dr-group-top-level")).to_contain_text(
        "Every namespace's menu"
    )


def test_an_inherited_decomposition_says_where_it_comes_from(open_ui):
    page = open_ui(tab="browse")
    inherited = page.get_by_test_id("dr-row-course_advisor-catalog-lookup")
    expect(inherited).to_contain_text("inherited from root")
    expect(page.get_by_test_id("dr-row-root-catalog-lookup")).not_to_contain_text(
        "inherited"
    )


def test_top_level_and_unattached_decompositions_have_groups_of_their_own(
    open_ui, library_server
):
    page = open_ui(tab="browse")
    expect(page.get_by_test_id("dr-row-top-level-triage-nightly")).to_contain_text(
        "starts the nightly triage"
    )
    expect(page.get_by_test_id("dr-group-unattached")).to_have_count(0)
    library_server.library().put_decomposition(
        text(example("old draft")), namespaces=[]
    )
    expect(page.get_by_test_id("dr-group-unattached")).to_contain_text("Not attached")
    expect(page.get_by_test_id("dr-row-unattached-old-draft")).to_contain_text("v1")


def test_saving_an_opened_decomposition_makes_its_next_version(open_ui, library_server):
    page = open_ui(tab="browse")
    page.get_by_test_id("dr-row-router-summarize-then-rank").click()
    expect(page.get_by_test_id("dr-name")).to_have_value("summarize then rank")
    expect(page.get_by_test_id("dr-name")).not_to_be_editable()
    page.get_by_test_id("dr-card-0-task").fill("Rank them by workload, then summarize.")
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-result")).to_have_text(
        "✓ Saved 'summarize then rank' v2. New conversations use it; conversations "
        "already started keep the version they began with."
    )
    saved = library_server.library().decomposition("summarize then rank")
    assert saved.version == 2
    assert (
        saved.data["messages"][0]["content"] == "Rank them by workload, then summarize."
    )
    assert saved.data["messages"][1]["content"] == (
        "<think>\nSummaries first, then one ranking.\n</think>\n"
        "<repl>\nFinalAnswer(sorted(courses))\n</repl>\n"
    )


def test_attached_to_is_the_exact_set_after_a_save(open_ui, library_server):
    page = open_ui(tab="browse")
    page.get_by_test_id("dr-row-root-catalog-lookup").click()
    expect(page.get_by_test_id("dr-attached-root")).to_be_checked()
    expect(page.get_by_test_id("dr-attached-router")).to_be_disabled()
    expect(page.get_by_test_id("dr-attached-list")).to_contain_text(
        "also used in router (inherited)"
    )
    page.get_by_test_id("dr-attached-root").uncheck()
    page.get_by_test_id("dr-attached-course_advisor").check()
    page.get_by_test_id("dr-save").click()
    # Attachments are the namespaces' lists: the decomposition itself stays at v1.
    expect(page.get_by_test_id("dr-result")).to_contain_text(
        "Saved 'catalog lookup' v1"
    )
    library = library_server.library()
    assert library.decomposition("catalog lookup").namespaces == ["course_advisor"]
    assert library.namespace("root").decompositions == []


def test_a_stale_save_offers_reload_or_save_over(open_ui, library_server):
    library = library_server.library()
    page = open_ui(tab="browse", focus="summarize-then-rank")
    expect(page.get_by_test_id("dr-use-when")).to_have_value("comparing many courses")
    head = library.decomposition("summarize then rank")
    library.put_decomposition(head.yaml, use_when="saved elsewhere", hint=head.hint)
    page.get_by_test_id("dr-hint").fill("mine")
    page.get_by_test_id("dr-save").click()
    stale = (
        "Decomposition 'summarize then rank' is at version 2, not 1: it changed after you "
        "opened it. Reload it, or save over it with base_version=2."
    )
    expect(page.get_by_test_id("dr-conflict")).to_contain_text(stale)
    page.get_by_test_id("dr-reload-entry").click()
    expect(page.get_by_test_id("dr-use-when")).to_have_value("saved elsewhere")
    expect(page.get_by_test_id("dr-hint")).to_have_value("the courses")

    library.put_decomposition(head.yaml, use_when="elsewhere again", hint=head.hint)
    page.get_by_test_id("dr-hint").fill("mine")
    page.get_by_test_id("dr-save").click()
    page.get_by_test_id("dr-save-over").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text("v4")
    saved = library.decomposition("summarize then rank")
    assert (saved.version, saved.use_when, saved.hint) == (4, "saved elsewhere", "mine")


def test_deleting_a_decomposition_detaches_it_everywhere(open_ui, library_server):
    page = open_ui(tab="browse", focus="catalog-lookup")
    page.get_by_test_id("dr-delete").click()
    expect(page.get_by_test_id("dr-confirm")).to_contain_text(
        "Delete 'catalog lookup'? It is removed from every namespace; its versions stay "
        "in the Library's history."
    )
    page.get_by_test_id("dr-confirm-yes").click()
    expect(page.get_by_test_id("dr-group-root")).to_be_visible()
    expect(page.locator("[data-testid$='-catalog-lookup']")).to_have_count(0)
    library = library_server.library()
    assert [d.name for d in library.decompositions()] == [
        "summarize then rank",
        "triage nightly",
    ]
    assert library.namespace("root").decompositions == []


def test_a_change_made_elsewhere_appears_without_a_reload(open_ui, library_server):
    page = open_ui(tab="browse")
    expect(page.get_by_test_id("dr-group-course_advisor")).to_be_visible()
    library_server.library().put_decomposition(
        text(example("rank by prerequisites")),
        namespaces=["course_advisor"],
        use_when="ordering courses by what they need first",
    )
    expect(
        page.get_by_test_id("dr-row-course_advisor-rank-by-prerequisites")
    ).to_contain_text("ordering courses by what they need first")


def test_the_tab_falls_back_to_attachments_when_inheritance_cannot_be_resolved(
    open_ui, library_server
):
    # A head that no longer validates under the installed deep_reasoner, as after an
    # upgrade: written to the store directly, since the Library refuses to write one.
    with store.write(library_server.library().path, "test", "stale head") as w:
        w.add(
            "namespace",
            "router.archive",
            yaml="name: router.archive\nretired_key: 1\n",
            attached=[],
        )
    page = open_ui(tab="browse")
    expect(page.get_by_test_id("dr-effective-failed")).to_contain_text(
        "Inherited decompositions cannot be shown: Namespace 'router.archive' version 2 "
        "no longer validates"
    )
    expect(page.get_by_test_id("dr-row-root-catalog-lookup")).to_be_visible()
    expect(page.get_by_test_id("dr-row-router-summarize-then-rank")).to_be_visible()
    expect(page.get_by_test_id("dr-row-course_advisor-catalog-lookup")).to_have_count(0)
    expect(page.get_by_test_id("dr-problems")).to_contain_text(
        "1 problem in the Library"
    )
    expect(page.get_by_test_id("dr-backend-lost")).to_have_count(0)


def test_focus_opens_that_decomposition(open_ui):
    page = open_ui(tab="browse", focus="summarize-then-rank")
    expect(page.get_by_test_id("dr-name")).to_have_value("summarize then rank")
    expect(page.get_by_test_id("dr-slash")).to_have_text("/summarize-then-rank")
    expect(page.get_by_test_id("dr-card-1-think")).to_have_value(
        "Summaries first, then one ranking."
    )
