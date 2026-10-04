import json

import pytest
from playwright.sync_api import expect

from tests.canvas_app.conftest import write_new

pytestmark = pytest.mark.browser

TASK = "Which of CS201, CS310 and CS330 can I take first?"
NAME = "rank by prerequisites"
USE_WHEN = "ordering courses by what they need first"
NO_FINAL_ANSWER = "This example never reaches FinalAnswer; the agent will imitate that."


def test_saving_stores_version_1_in_the_picked_namespace(open_ui, library_server):
    page = open_ui(tab="create", namespace="router", started=True)
    page.get_by_test_id("dr-name").fill(NAME)
    expect(page.get_by_test_id("dr-slash")).to_have_text("/rank-by-prerequisites")
    page.get_by_test_id("dr-use-when").fill(USE_WHEN)
    page.get_by_test_id("dr-hint").fill("the task")
    page.get_by_test_id("dr-namespace-course_advisor").check()
    page.get_by_test_id("dr-card-0-task").fill(TASK)
    page.get_by_test_id("dr-card-1-think").fill(
        "Each course's prerequisites decide it."
    )
    page.get_by_test_id("dr-card-1-code").fill("order = sorted(cs)\nprint(order)")
    page.get_by_test_id("dr-add-turn").click()
    expect(page.get_by_test_id("dr-card-2")).to_contain_text("written by you, not run")
    page.get_by_test_id("dr-card-2-output").fill("['CS201', 'CS310', 'CS330']")
    page.get_by_test_id("dr-card-3-code").fill("FinalAnswer(order)")
    expect(page.get_by_test_id("dr-save")).to_have_text("Save to course_advisor")
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text(
        "✓ Saved 'rank by prerequisites' v1 in course_advisor."
    )
    saved = library_server.library().decomposition(NAME)
    assert (saved.version, saved.namespaces) == (1, ["course_advisor"])
    assert (saved.use_when, saved.hint) == (USE_WHEN, "the task")
    assert saved.data["messages"] == [
        {"role": "user", "content": TASK},
        {
            "role": "assistant",
            "content": "<think>Each course's prerequisites decide it.</think>\n"
            "<repl>\norder = sorted(cs)\nprint(order)\n</repl>\n",
        },
        {
            "role": "user",
            "content": "<observation>\n['CS201', 'CS310', 'CS330']\n</observation>",
        },
        {"role": "assistant", "content": "<repl>\nFinalAnswer(order)\n</repl>\n"},
    ]
    expect(page.get_by_test_id("dr-name")).to_have_value("")


def test_the_turn_after_a_step_reads_observation_think_code(open_ui):
    page = open_ui(tab="create")
    page.get_by_test_id("dr-add-turn").click()
    expect(page.locator("[data-testid^='dr-card-'] label")).to_have_text(
        ["task", "think", "code", "observation", "think", "code"]
    )
    expect(page.get_by_test_id("dr-card-2-output")).to_have_accessible_name(
        "observation"
    )
    page.get_by_test_id("dr-view-yaml").click()
    page.get_by_test_id("dr-edit-yaml").click()
    page.get_by_test_id("dr-yaml").fill(
        "name: brief\nmessages:\n  - role: system\n    content: Be brief.\n"
    )
    page.get_by_test_id("dr-edit-cards").click()
    expect(page.get_by_test_id("dr-card-0")).to_contain_text(
        "Shown as written: this message is not a task, a think-and-code step or an "
        "observation."
    )


def test_the_picker_lists_the_librarys_namespaces_and_preselects_the_conversations(
    open_ui,
):
    page = open_ui(tab="create", namespace="course_advisor")
    picker = page.locator("[data-testid^='dr-namespace-']")
    expect(picker).to_have_count(4)
    assert [p.get_attribute("data-testid") for p in picker.all()] == [
        "dr-namespace-root",
        "dr-namespace-router",
        "dr-namespace-router.archive",
        "dr-namespace-course_advisor",
    ]
    expect(page.get_by_test_id("dr-namespace-course_advisor")).to_be_checked()
    expect(page.get_by_test_id("dr-save")).to_have_text("Save to course_advisor")


@pytest.mark.parametrize("namespace", [None, "not_in_the_library"])
def test_without_a_conversation_namespace_the_default_namespace_is_preselected(
    open_ui, namespace
):
    page = open_ui(tab="create", **({"namespace": namespace} if namespace else {}))
    expect(page.get_by_test_id("dr-namespace-router")).to_be_checked()


SAVED_STARTED = (
    "✓ Saved 'rank by prerequisites' v1 in router. New conversations in router use it; "
    "this conversation does not, because its run was built at its first message."
)
SAVED = (
    "✓ Saved 'rank by prerequisites' v1 in router. New conversations in router use it "
    "and offer it as /rank-by-prerequisites; a conversation that has already started "
    "keeps the run it began with."
)


@pytest.mark.parametrize(("started", "line"), [(True, SAVED_STARTED), (False, SAVED)])
def test_the_saved_line_says_the_started_conversation_does_not_change(
    open_ui, started, line
):
    page = open_ui(tab="create", namespace="router", started=started)
    write_new(page, NAME, TASK)
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-result")).to_have_text(line)
    expect(page.get_by_test_id("dr-show-in-decompositions")).to_be_visible()


def test_saving_without_a_name_in_card_mode_asks_for_one_and_writes_nothing(
    open_ui, library_server
):
    library = library_server.library()
    rev = library.rev()
    page = open_ui(tab="create")
    write_new(page, "", TASK)
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-name-errors")).to_have_text(
        "Give the decomposition a name."
    )
    assert library.rev() == rev


def test_validation_errors_show_on_the_card_they_name(open_ui, library_server):
    page = open_ui(tab="create")
    page.get_by_test_id("dr-name").fill(" spaced")
    expect(page.get_by_test_id("dr-name-errors")).to_contain_text(
        "A decomposition's name must not start or end with a space"
    )
    page.get_by_test_id("dr-view-yaml").click()
    page.get_by_test_id("dr-edit-yaml").click()
    page.get_by_test_id("dr-yaml").fill(
        "name: bad role\nmessages:\n- role: user\n  content: Which first?\n"
        "- role: tool\n  content: hi\n"
    )
    page.get_by_test_id("dr-edit-cards").click()
    expect(page.get_by_test_id("dr-card-1-raw")).to_have_value("hi")
    expect(page.get_by_test_id("dr-card-1-errors")).to_contain_text(
        "Input should be 'system', 'user' or 'assistant'"
    )
    expect(page.get_by_test_id("dr-card-0-errors")).to_have_count(0)
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-errors")).to_contain_text(
        "'bad role' is not a valid deep_reasoner Decomposition"
    )
    assert [d.name for d in library_server.library().decompositions()] == [
        "catalog lookup",
        "summarize then rank",
        "triage nightly",
    ]


def test_an_error_that_names_no_card_shows_above_the_cards(open_ui, library_server):
    page = open_ui(tab="create", namespace="router.archive")
    write_new(page, NAME, TASK)
    library_server.library().delete("namespace", "router.archive")
    page.get_by_test_id("dr-save").click()
    errors = page.get_by_test_id("dr-errors")
    expect(errors).to_contain_text(
        "There is no namespace 'router.archive' in the library."
    )
    first_card = page.get_by_test_id("dr-card-0")
    assert errors.bounding_box()["y"] < first_card.bounding_box()["y"]


def test_an_example_without_final_answer_asks_before_saving(open_ui, library_server):
    page = open_ui(tab="create")
    write_new(page, "no answer", TASK, code="print(1)")
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-warnings")).to_contain_text(NO_FINAL_ANSWER)
    page.get_by_test_id("dr-cancel-save").click()
    expect(page.get_by_test_id("dr-warnings")).to_have_count(0)
    library = library_server.library()
    assert "no answer" not in {d.name for d in library.decompositions()}
    page.get_by_test_id("dr-save").click()
    page.get_by_test_id("dr-save-anyway").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text("v1 in router")
    assert library.decomposition("no answer").version == 1


def test_an_existing_name_offers_to_save_the_next_version_keeping_its_namespaces(
    open_ui, library_server
):
    page = open_ui(tab="create", namespace="course_advisor")
    write_new(page, "catalog lookup", TASK)
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-conflict")).to_contain_text(
        "'catalog lookup' already exists (v1, in root)."
    )
    page.get_by_test_id("dr-rename").click()
    expect(page.get_by_test_id("dr-name")).to_be_focused()
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-save-as-next")).to_have_text("Save mine as v2")
    page.get_by_test_id("dr-save-as-next").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text("v2 in course_advisor")
    saved = library_server.library().decomposition("catalog lookup")
    assert (saved.version, saved.namespaces) == (2, ["root", "course_advisor"])
    assert saved.data["messages"][0]["content"] == TASK


def test_rename_in_yaml_mode_focuses_the_yaml_which_holds_the_name(open_ui):
    page = open_ui(tab="create")
    page.get_by_test_id("dr-view-yaml").click()
    page.get_by_test_id("dr-edit-yaml").click()
    existing = {
        "name": "catalog lookup",
        "messages": [
            {"role": "user", "content": TASK},
            {"role": "assistant", "content": "<repl>\nFinalAnswer(1)\n</repl>\n"},
        ],
    }
    page.get_by_test_id("dr-yaml").fill(json.dumps(existing))
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-conflict")).to_contain_text(
        "'catalog lookup' already exists (v1, in root)."
    )
    page.get_by_test_id("dr-rename").click()
    expect(page.get_by_test_id("dr-conflict")).to_have_count(0)
    expect(page.get_by_test_id("dr-yaml")).to_be_focused()


def test_view_yaml_shows_the_canonical_yaml_and_edited_yaml_returns_to_cards(
    open_ui, library_server
):
    page = open_ui(tab="create")
    write_new(page, NAME, TASK)
    page.get_by_test_id("dr-view-yaml").click()
    sent = {
        "name": NAME,
        "messages": [
            {"role": "user", "content": TASK},
            {"role": "assistant", "content": "<repl>\nFinalAnswer(1)\n</repl>\n"},
        ],
    }
    canonical = (
        library_server.library().validate("decomposition", json.dumps(sent)).yaml
    )
    expect(page.get_by_test_id("dr-yaml")).to_have_value(canonical)
    expect(page.get_by_test_id("dr-yaml")).not_to_be_editable()
    page.get_by_test_id("dr-edit-yaml").click()
    page.get_by_test_id("dr-yaml").fill(canonical.replace(TASK, "Which comes first?"))
    page.get_by_test_id("dr-edit-cards").click()
    expect(page.get_by_test_id("dr-card-0-task")).to_have_value("Which comes first?")
    expect(page.get_by_test_id("dr-name")).to_have_value(NAME)
    page.get_by_test_id("dr-view-yaml").click()
    page.get_by_test_id("dr-edit-yaml").click()
    page.get_by_test_id("dr-yaml").fill("name: [unclosed")
    page.get_by_test_id("dr-edit-cards").click()
    expect(page.get_by_test_id("dr-yaml-error")).to_contain_text(
        "This is not valid YAML:"
    )
    page.get_by_test_id("dr-yaml").fill("just a sentence")
    page.get_by_test_id("dr-edit-cards").click()
    expect(page.get_by_test_id("dr-yaml-error")).to_have_text(
        "To edit it as cards, the YAML must be a mapping with a name and a list of "
        "messages, each with a role and a content."
    )


def test_use_when_in_the_yaml_is_refused_in_deep_reasoners_words(
    open_ui, library_server
):
    page = open_ui(tab="create")
    page.get_by_test_id("dr-view-yaml").click()
    page.get_by_test_id("dr-edit-yaml").click()
    page.get_by_test_id("dr-yaml").fill(
        "name: with use when\nuse_when: always\nmessages:\n- role: user\n  content: hi\n"
    )
    page.get_by_test_id("dr-save").click()
    errors = page.get_by_test_id("dr-errors")
    expect(errors).to_contain_text("use_when: Extra inputs are not permitted")
    expect(errors).to_contain_text(
        "Use-when text is stored beside the YAML: pass use_when=... instead."
    )
    assert "with use when" not in {
        d.name for d in library_server.library().decompositions()
    }


def test_a_draft_survives_reloading_the_frame(open_ui):
    page = open_ui(tab="create")
    write_new(page, NAME, TASK)
    page.get_by_test_id("dr-use-when").fill(USE_WHEN)
    page.reload()
    expect(page.get_by_test_id("dr-name")).to_have_value(NAME)
    expect(page.get_by_test_id("dr-use-when")).to_have_value(USE_WHEN)
    expect(page.get_by_test_id("dr-card-0-task")).to_have_value(TASK)
    page.get_by_test_id("dr-discard-draft").click()
    expect(page.get_by_test_id("dr-name")).to_have_value("")
    page.reload()
    expect(page.get_by_test_id("dr-card-0-task")).to_have_value("")


def test_a_draft_keeps_the_namespace_picked_over_the_preselected_one(open_ui):
    page = open_ui(tab="create", namespace="router")
    page.get_by_test_id("dr-namespace-course_advisor").check()
    page.get_by_test_id("dr-name").fill(NAME)
    page.reload()
    expect(page.get_by_test_id("dr-name")).to_have_value(NAME)
    expect(page.get_by_test_id("dr-namespace-course_advisor")).to_be_checked()
    expect(page.get_by_test_id("dr-save")).to_have_text("Save to course_advisor")
    page.get_by_test_id("dr-discard-draft").click()
    expect(page.get_by_test_id("dr-namespace-router")).to_be_checked()


def test_use_when_and_hint_survive_a_save_that_did_not_touch_them(
    open_ui, library_server
):
    page = open_ui(tab="browse", focus="catalog-lookup")
    page.get_by_test_id("dr-card-0-task").fill("What does CS310 need?")
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text("v2")
    saved = library_server.library().decomposition("catalog lookup")
    assert (saved.use_when, saved.hint) == ("one course at a time", "a course code")


def test_an_imported_decomposition_saved_unchanged_makes_no_new_version(
    open_ui, library_server
):
    library = library_server.library()
    rev = library.rev()
    page = open_ui(tab="browse", focus="catalog-lookup")
    expect(page.get_by_test_id("dr-card-2-output")).to_have_value("['CS101']")
    page.get_by_test_id("dr-save").click()
    expect(page.get_by_test_id("dr-result")).to_contain_text(
        "✓ Saved 'catalog lookup' v1."
    )
    assert (library.rev(), library.decomposition("catalog lookup").version) == (rev, 1)
