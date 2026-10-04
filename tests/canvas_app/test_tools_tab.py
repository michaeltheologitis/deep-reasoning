import pytest
from playwright.sync_api import expect

from tests.canvas_app.test_notice import SAFETY_5

pytestmark = pytest.mark.browser


@pytest.mark.parametrize(
    ("cap", "sentence"), [("5", SAFETY_5), ("12", "stops at $12 per")]
)
def test_the_tools_tab_always_shows_the_safety_notice_with_the_cap(
    open_ui, cap, sentence
):
    page = open_ui(tab="tools", cap=cap)
    expect(page.get_by_test_id("dr-notice")).to_contain_text(sentence)
    expect(page.get_by_test_id("dr-notice-ack")).to_have_count(0)


def test_the_tools_tab_lists_tools_with_their_grants(open_ui, library_server):
    page = open_ui(tab="tools")
    row = page.get_by_test_id("dr-tool-word_count")
    expect(row).to_contain_text("word_count")
    expect(row).to_contain_text("v1")
    expect(row).to_contain_text("factory make · tools/word_count.py")
    expect(row).to_contain_text("granted in course_advisor")
    library = library_server.library()
    library.delete("tool", "word_count")
    expect(page.get_by_test_id("dr-no-tools")).to_have_text("No tools in the Library.")
