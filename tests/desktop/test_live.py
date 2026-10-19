"""The UX round's live tier (TASK-65 §7.4): the installed app, a first launch with a fresh
HOME, one question to the starter Library's real model (gpt-6-luna, through the key
proxy) with a keyless LLM profile active, as an install that has one is.

cross-repo.yml runs it after E12 when its dispatch input live is true. OPENAI_API_KEY is
in that step's environment only; the test saves it as a Canvas secret, as a user does,
and the app is launched without it."""

import os
import re
import time
from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Error, expect, sync_playwright

from tests.desktop.app import (
    APP,
    FIRST_LAUNCH_S,
    LaunchedApp,
    conversation_events,
    fresh_home,
    launch,
)
from tests.desktop.e12.subagents import expand_all_subagents
from tests.desktop.test_e12 import eventually, start_conversation, window

KEY = "OPENAI_API_KEY"
QUESTION = "Use one sub-agent to add 2 and 2, then answer with its result."
TITLE_LENGTH = 50  # the agent-server's truncation of a first message into a title
ANSWERED_S = 300.0
COST = re.compile(r"\$\d+\.\d+")

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.live,
    pytest.mark.skipif(not APP.exists(), reason=f"the app is not installed at {APP}"),
    pytest.mark.skipif(not os.environ.get(KEY), reason=f"{KEY} is not set"),
]


@pytest.fixture(scope="module")
def app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LaunchedApp]:
    """A first launch whose environment holds no model key."""
    with fresh_home() as home:
        log = tmp_path_factory.mktemp("live") / "app.log"
        with pytest.MonkeyPatch.context() as without_key:
            without_key.delenv(KEY)
            launched = launch(home, log)
        try:
            launched.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
            yield launched
        finally:
            launched.stop()
            print(f"the app's log: {log}")


@pytest.fixture(scope="module")
def browser(app: LaunchedApp) -> Iterator[Browser]:
    """Playwright attached to the app's own Chromium over its DevTools port."""
    with sync_playwright() as playwright:
        deadline = time.monotonic() + FIRST_LAUNCH_S
        while True:
            try:
                cdp = playwright.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{app.debug_port}"
                )
                break
            except Error:
                assert app.process.poll() is None, "the app exited before its window"
                assert time.monotonic() < deadline, "no DevTools port"
                time.sleep(1.0)
        yield cdp


def test_a_question_to_the_real_model_is_answered_titled_and_costed_with_no_error(
    app, browser
):
    app.request("PUT", "/api/settings/secrets", {"name": KEY, "value": os.environ[KEY]})
    app.request("POST", "/api/profiles/gpt-5-5", {"llm": {"model": "gpt-5.5"}})
    app.request("POST", "/api/profiles/gpt-5-5/activate")
    page = window(browser)
    conversation = start_conversation(page, QUESTION)
    expect(page.get_by_test_id("agent-message").filter(has_text="4")).to_be_visible(
        timeout=ANSWERED_S * 1000
    )
    eventually(
        lambda: (
            app.request("GET", f"/api/conversations/{conversation}")["title"]
            == QUESTION[:TITLE_LENGTH]
        )
    )
    events = conversation_events(app, conversation)
    assert [e for e in events if e["kind"] == "ConversationErrorEvent"] == []
    rows = page.get_by_test_id("subagent-row")
    eventually(lambda: expand_all_subagents(page) or rows.count() > 0)
    expect(rows.first.get_by_test_id("subagent-cost").first).to_have_text(COST)
