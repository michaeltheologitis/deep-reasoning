import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.browser

SAFETY_5 = (
    "deep_reasoner runs as you. It can read and change any file you can, and code it "
    "writes can find your model keys on this computer if it tries. Spend through the key "
    "proxy stops at $5 per conversation."
)
SAFETY_NO_CAP = (
    "deep_reasoner runs as you. It can read and change any file you can, and code it "
    "writes can find your model keys on this computer if it tries. The key proxy is off "
    "for this agent (--no-key-proxy), so nothing caps what a conversation spends."
)


def test_the_safety_notice_shows_until_understood(open_ui):
    page = open_ui(notice=True, tab="create")
    expect(page.get_by_test_id("dr-notice")).to_have_text(SAFETY_5 + "I understand")
    expect(page.get_by_test_id("dr-save")).to_have_count(0)
    page.get_by_test_id("dr-notice-ack").click()
    expect(page.get_by_test_id("dr-notice")).to_have_count(0)
    expect(page.get_by_test_id("dr-save")).to_be_visible()
    page.reload()
    expect(page.get_by_test_id("dr-save")).to_be_visible()
    expect(page.get_by_test_id("dr-notice")).to_have_count(0)


def test_the_notice_is_d5s_sentence_with_the_cap(open_ui):
    texts = pytest.importorskip("dr_app.texts", reason="D5's dr_app is not installed")
    page = open_ui(notice=True, cap="7")
    expect(page.get_by_test_id("dr-notice")).to_contain_text(texts.SAFETY.format(cap=7))


def test_without_the_key_proxy_the_notice_says_nothing_caps_spending(open_ui):
    page = open_ui(notice=True, cap="off")
    expect(page.get_by_test_id("dr-notice")).to_have_text(
        SAFETY_NO_CAP + "I understand"
    )
