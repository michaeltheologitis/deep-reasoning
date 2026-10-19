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
from playwright.sync_api import expect

from deep_reasoning.acp.runlog import AgentStart, Home, PromptEnd, RunLog
from tests.crossrepo.agent_server import conversation_events
from tests.desktop.app import (
    APP,
    FIRST_LAUNCH_S,
    LaunchedApp,
    fresh_home,
    launch,
)
from tests.desktop.e12.subagents import expand_all_subagents
from tests.desktop.test_e12 import eventually, run_ids, start_conversation, window

KEY = "OPENAI_API_KEY"
QUESTION = "Use one sub-agent to add 2 and 2, then answer with its result."
# The agent-server's title for it with no title LLM: the SDK's generate_fallback_title
# keeps a first message of up to 50 characters, else its first 47 and "...".
TITLE = f"{QUESTION[:47]}..."
ANSWERED_S = 600.0  # a real model, a sub-agent and its turns
COST = re.compile(r"\$\d+\.\d+")
COSTS_SETTING = "openhands-show-subagent-costs"  # C1's saved "Show sub-agent costs"

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


def logged(app: LaunchedApp, before: set[str]) -> list:
    """Every event of the runs started since before, as dr-acp's run logs hold them."""
    runs = sorted(run_ids(app) - before)
    return [event for run in runs for event in RunLog.read(Home(app.data), run)]


def first_prompt_end(app: LaunchedApp, before: set[str], page) -> PromptEnd:
    """The first prompt's end in a run started since before; failing at ANSWERED_S with
    what the runs logged and what the window shows."""
    deadline = time.monotonic() + ANSWERED_S
    while not (ended := [e for e in logged(app, before) if isinstance(e, PromptEnd)]):
        if time.monotonic() > deadline:
            kinds = [event.kind for event in logged(app, before)]
            shown = page.get_by_test_id("agent-message").all_inner_texts()
            raise AssertionError(
                f"no prompt ended in {ANSWERED_S:g} s; the runs logged {kinds}; the "
                f"window shows {shown}"
            )
        time.sleep(1.0)
    return ended[0]


def test_a_question_to_the_real_model_is_answered_titled_and_costed_with_no_error(
    app, browser
):
    app.request("PUT", "/api/settings/secrets", {"name": KEY, "value": os.environ[KEY]})
    app.request("POST", "/api/profiles/gpt-5-5", {"llm": {"model": "gpt-5.5"}})
    app.request("POST", "/api/profiles/gpt-5-5/activate")
    page = window(browser)
    costs_setting = f"localStorage.getItem({COSTS_SETTING!r})"
    assert page.evaluate(costs_setting) is None, "the app's profile is not a fresh one"
    before = run_ids(app)
    conversation = start_conversation(page, QUESTION)
    ended = first_prompt_end(app, before, page)
    assert (ended.outcome, ended.detail) == ("answered", None), ended
    print(f"answered: {ended.answer!r}")
    expect(page.get_by_test_id("agent-message").last).to_be_visible()
    eventually(
        lambda: (
            app.request("GET", f"/api/conversations/{conversation}")["title"] == TITLE
        )
    )
    events = conversation_events(app, conversation)
    assert [e for e in events if e["kind"] == "ConversationErrorEvent"] == []
    children = [
        e
        for e in logged(app, before)
        if isinstance(e, AgentStart) and e.parent is not None
    ]
    print(f"sub-agents the run recorded: {[child.task for child in children]}")
    rows = page.get_by_test_id("subagent-row")
    eventually(lambda: expand_all_subagents(page) or rows.count() == len(children))
    for row in rows.all():
        expect(row.get_by_test_id("subagent-cost").first).to_have_text(COST)
