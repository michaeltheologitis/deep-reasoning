"""E12: the installed Linux app, launched as a user would launch it, on a fake model
(D5 §7.5, TASK-65 §7.4).

cross-repo.yml's desktop-e2e job builds the packages from the pins (desktop/build.py
linux), installs the .deb and runs this module under xvfb-run. Its tests run in order
and share one first launch, all but the last two: the launch onto the home screen, with
no onboarding, and the automation backend answering; the page refusing a host name that
is not this machine; no telemetry consent; no screen offering another agent or an agent
profile; a question asked before the model key is saved, answered with where it goes;
the first answered conversation, from deep_reasoner although another profile is active,
its key kept out, and the window title naming the product after its title and alone at
home; a keyless LLM profile titling no chat with an error; nothing recording consent;
D3's frame through the bridge; then the final part: C1's nested sub-agents, their costs
shown by default and a Stop of one, C2's namespace picker, slash menu and header panel
with Create decomposition, the Spend cap set in D4's Tools tab capping the next
conversation, an MCP server granted there, and the panel past its first session; then
the quit and an offline relaunch of setup. Last, a second first launch, from a HOME
whose uv index answers expire a second after their fetch, and its offline relaunch. No
test calls a real model.
"""

import json
import os
import re
import signal
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from playwright.sync_api import (
    Browser,
    Error,
    FrameLocator,
    Locator,
    Page,
    expect,
    sync_playwright,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from deep_reasoning.acp import texts as acp_texts
from deep_reasoning.acp.catalog import slug
from deep_reasoning.acp.runlog import Home, McpStatus, PromptStart, RunLog, RunStart
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from desktop import build
from dr_app import texts
from tests.acp.scenarios import repl, scripted, task_and_turn
from tests.crossrepo.agent_server import conversation_events
from tests.desktop.app import (
    APP,
    CANVAS_URL,
    FIRST_LAUNCH_S,
    NETWORK_CUT,
    QUIT_S,
    SESSION,
    STARTING_OFFLINE,
    STARTUP_FAILED,
    LaunchedApp,
    answer,
    eventually,
    example,
    expire_uv_index_answers_quickly,
    fresh_home,
    get_with_host,
    launch,
    library_frame,
    pick_namespace,
    point_the_library_at,
    processes_mentioning,
    run_ids,
    secret,
    setup_lines,
    spend_caps,
    start_conversation,
    user_environment,
    uvx_start_records,
    worker_environ,
)
from tests.desktop.e12.subagents import (
    expand_all_subagents,
    read_rendered_subagent_tree,
    recorded_subagent_tree,
    subagent_cost,
)

pytestmark = [
    pytest.mark.desktop,
    pytest.mark.skipif(not APP.exists(), reason=f"the app is not installed at {APP}"),
]

INGRESS = "http://127.0.0.1:18000"
BACKEND = "/api/canvas-extensions/installed/dr-library/backend"
QUESTION = "What does E12 answer?"
ANSWER = secret("e12-answer-")
E12_MODEL = "e12-model"
NAMESPACE = "e12"
OFFLINE_S = 5.0
# TASK-50: the pages a locked build hides, and the ones it keeps, in the navigation's order.
HIDDEN_SETTINGS = (
    "settings/agents",
    "settings/agent",
    "settings/llm",
    "settings/meta-llm",
    "settings/condenser",
)
SHOWN_SETTINGS = [
    "/settings/agent-context",
    "/settings/verification",
    "/settings/app",
    "/settings/secrets",
]
# An automation of the pinned @openhands/extensions catalog whose setup needs no integration.
AUTOMATION_TEMPLATE = "custom-automation"
# Q1: asked before the model key is saved; dr-acp answers it before any run.
NO_KEY_QUESTION = "What does E12 ask before its key?"
# TASK-46: an LLM profile as Canvas's Settings → LLM saves it, with no key.
KEYLESS_LLM_PROFILE = "gpt-5-5"
TITLE_QUESTION = "What titles the e12 chat?"  # at most 50 characters: the whole title
TITLE_ANSWER = secret("e12-title-")
# Q3: the Tools tab's Spend cap, set, then the next conversation's cap.
CAP = "7.50"
CAP_QUESTION = "What does E12 spend under its cap?"
CAP_ANSWER = secret("e12-cap-")
# TASK-66: the installed app's defaults and uvx, and how long its services take to answer
# after the first launch and after an offline relaunch, by the lines their logs end on.
INSTALLED_DEFAULTS = APP.parent / "resources" / "app" / "config" / "defaults.json"
APP_UVX = APP.parent / "resources" / "bin" / "uvx"
AUTOMATION_S = 120.0
RELAUNCH_S = 180.0
AUTOMATION_STARTED = "Application startup complete"  # uvicorn's, in its JSON log line
ENVIRONMENT_CELL = repl(
    "import os",
    "print(dict(os.environ))",
    "print(open('/proc/self/environ', 'rb').read())",
)
# C1: a fan-out whose first child spawns one of its own.
TREE_QUESTION = "How do the e12 courses compare?"
TREE_ANSWER = secret("e12-tree-")
# C1's Stop: the first child answers; the second waits on a grandchild whose model
# call is held until E12 has pressed Stop on it, so both are running then.
STOP_QUESTION = "Read the e12 courses."
SLOW, DEEPER, QUICK = "Read slowly.", "Read deeper.", "Read quickly."
STOP_ANSWER = secret("e12-stop-")
HELD_S = 180.0
# C2: a decomposition the Library holds in NAMESPACE, and one Create decomposition saves.
IMPORTED = "e12 triage"
CREATED = "rank e12 courses"
CREATED_TASK = "Which e12 course comes first?"
PANEL_QUESTION = "Open the e12 panel."
PANEL_ANSWER = secret("e12-panel-")
NEXT_TASK = "Rank the e12 courses."
NEXT_ANSWER = secret("e12-next-")
# D4: an MCP server of Canvas's settings, granted to NAMESPACE in the Tools tab.
ECHO_SERVER = Path(__file__).resolve().parents[1] / "mcp" / "servers" / "echo_server.py"
MCP_QUESTION = "Echo through the e12 server."
MCP_REPLY = secret("e12-mcp-")
SESSION_S = 5 * 60  # the bridge's App backend session (C2 renews it before it ends)
CONSENT_SHOWS_S = 5  # a lazy-loaded consent dialog would be up by then
CONSENT_STORAGE_KEY = (
    "openhands-telemetry-consent"  # Canvas's src/services/telemetry.ts
)
INSTALLING = texts.installing("", "").partition(" with ")[0]
PLAN = {
    QUESTION: [ENVIRONMENT_CELL, repl(f"FinalAnswer({ANSWER!r})")],
    TREE_QUESTION: [
        repl(
            "r = run_all({c: anext(subagent().send(f'Survey {c}.')) for c in 'AB'})",
            "print(r)",
        ),
        repl(f"FinalAnswer({TREE_ANSWER!r})"),
    ],
    "Survey A.": [
        repl("inner = subagent('Read A1.')", "print(inner)"),
        repl("FinalAnswer('A: ' + inner)"),
    ],
    "Survey B.": [repl("FinalAnswer('B surveyed')")],
    "Read A1.": [repl("FinalAnswer('A1 is light')")],
    STOP_QUESTION: [
        repl(f"quick = subagent({QUICK!r})", f"slow = subagent({SLOW!r})"),
        repl(f"FinalAnswer({STOP_ANSWER!r})"),
    ],
    SLOW: [
        repl(f"deeper = subagent({DEEPER!r})", "print(deeper)"),
        repl("FinalAnswer(deeper)"),
    ],
    DEEPER: [repl("print('deeper')"), repl("FinalAnswer('deep')")],
    QUICK: [repl("FinalAnswer('quick')")],
    PANEL_QUESTION: [repl(f"FinalAnswer({PANEL_ANSWER!r})")],
    NEXT_TASK: [repl(f"FinalAnswer({NEXT_ANSWER!r})")],
    MCP_QUESTION: [repl(f"FinalAnswer(echo.echo({MCP_REPLY!r}))")],
    TITLE_QUESTION: [repl(f"FinalAnswer({TITLE_ANSWER!r})")],
    CAP_QUESTION: [repl(f"FinalAnswer({CAP_ANSWER!r})")],
}
# $0.002 a call at E12_MODEL's price, so each sub-agent's cost has a few digits.
USAGE = {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
KEY = secret("sk-e12-")
STOPPED = threading.Event()  # E12 has pressed Stop and dr-acp has accepted it
expect.set_options(timeout=60_000)


def spend_cap_saved(cap: str) -> str:
    """The Spend cap field's line after a save (TASK-65 §6.3)."""
    return f"✓ Saved: new conversations stop at ${cap}."


def holding_the_grandchild(respond: Callable[[list], str]) -> Callable[[list], str]:
    """DEEPER's first model call waits until STOPPED, or HELD_S."""

    def held(messages: list) -> str:
        task, turn = task_and_turn(messages)
        if DEEPER in task and turn == 0:
            STOPPED.wait(HELD_S)
        return respond(messages)

    return held


@pytest.fixture(scope="module")
def fake() -> Iterator[FakeOpenAI]:
    responder = holding_the_grandchild(scripted(PLAN))
    with FakeOpenAI(responder, usage=lambda messages, reply: USAGE) as model:
        yield model


@contextmanager
def first_launch(logs: Path, *, expiring: bool = False) -> Iterator[LaunchedApp]:
    """A first launch, with a fresh HOME: a cold uv cache, nothing installed; stopped on
    the way out. When expiring, uv's index answers under that HOME stay fresh for a
    second only."""
    with fresh_home() as home:
        if expiring:
            expire_uv_index_answers_quickly(home)
        log = logs / "app.log"
        launched = launch(home, log)
        try:
            yield launched
        finally:
            launched.stop()
            print(f"the app's log: {log}")


@pytest.fixture(scope="module")
def app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LaunchedApp]:
    """The first launch, which every step but the last two shares."""
    with first_launch(tmp_path_factory.mktemp("e12")) as launched:
        yield launched


@pytest.fixture(scope="module")
def expiring(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LaunchedApp]:
    """Another first launch, from a HOME whose uv index answers stay fresh for a second,
    as if every later launch came past their ten minutes; quit once setup is done and
    both services have recorded their online start."""
    logs = tmp_path_factory.mktemp("e12-expiring")
    with first_launch(logs, expiring=True) as launched:
        launched.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
        eventually(lambda: len(uvx_start_records(launched)) >= 2, AUTOMATION_S)
        launched.stop()
        eventually(lambda: processes_mentioning(str(launched.home)) == [], QUIT_S)
        yield launched


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


def window(browser: Browser) -> Page:
    """The main window, once it shows Canvas. It waits through Playwright, whose sync API
    takes in the app's events (a new window, a navigation) only while it is called."""
    context = browser.contexts[0]
    deadline = time.monotonic() + FIRST_LAUNCH_S
    while time.monotonic() < deadline:
        for page in context.pages:
            if page.url.startswith(CANVAS_URL):
                return page
        try:
            context.wait_for_event("page", timeout=1000)
        except PlaywrightTimeout:
            pass
    raise AssertionError("the window never loaded Canvas")


def test_the_first_launch_installs_everything_and_opens_on_the_home_screen(
    app, browser
):
    app.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
    page = window(browser)
    expect(page.get_by_test_id("chat-input")).to_be_visible()
    expect(page.get_by_test_id("first-run-onboarding-screen")).to_have_count(0)
    expect(page.get_by_test_id("onboarding-modal")).to_have_count(0)
    before, after = setup_lines(app, "before-start"), setup_lines(app, "after-ready")
    assert texts.home_local(str(app.data)) in before
    assert any(line.startswith("installed in ") for line in before)
    assert texts.PROFILE_CREATED in after
    assert texts.app_ready("0.1.0", "installed") in after
    unwanted = ("runs as you", "OPENAI_API_KEY")
    assert [line for line in before + after if any(u in line for u in unwanted)] == []
    assert app.request("GET", BACKEND)["state"] == "ready"
    info = app.request("GET", "/server_info")
    assert info["app_backend_ingress_url"] == INGRESS
    assert app.request("GET", "/api/agent-profiles")["active_agent_profile_id"] == (
        locked_profile_id(app)
    )


def locked_profile_id(app: LaunchedApp) -> str:
    profiles = app.request("GET", "/api/agent-profiles")["profiles"]
    [ours] = [p for p in profiles if p["name"] == build.LOCKED_PROFILE]
    return ours["id"]


def installed_defaults() -> dict:
    return json.loads(INSTALLED_DEFAULTS.read_text())


def test_the_automation_backend_answers_after_the_first_launch(app):
    """It would not install at a cutoff before versions.automation's release, and no
    other step asks it (TASK-66 §5.4)."""
    port = installed_defaults()["ports"]["automation"]
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + AUTOMATION_S
    while True:
        try:
            status, body = get_with_host(url, f"127.0.0.1:{port}")
        except OSError as error:  # not listening yet
            status, body = None, str(error)
        if status == 200 or time.monotonic() > deadline:
            break
        time.sleep(2.0)
    assert status == 200, f"{url}: {status} {body}"


@pytest.mark.parametrize("port", [8000, 3001], ids=["ingress", "frontend"])
def test_the_page_refuses_a_host_name_that_is_not_this_machine(app, port):
    """A DNS-rebound page's requests name its own host; the page carries the session key
    (TASK-64)."""
    url = f"http://127.0.0.1:{port}/"
    status, body = get_with_host(url, f"rebound.example:{port}")
    assert status == 403
    assert app.session_key not in body
    status, body = get_with_host(url, f"localhost:{port}")
    assert status == 200
    assert app.session_key in body


def test_the_first_launch_asks_for_no_telemetry_consent(app, browser):
    """Our build cannot report (decision K), so Canvas has nothing to ask (dr-3, #28).
    The consent dialog is lazy-loaded; where a build shows it, it is up within a few
    seconds of the home screen."""
    page = window(browser)
    expect(page.get_by_test_id("chat-input")).to_be_visible()
    page.wait_for_timeout(CONSENT_SHOWS_S * 1000)
    expect(page.get_by_test_id("telemetry-consent-form")).to_have_count(0)


def settings_navigation(page: Page) -> list[str]:
    """The pages the settings navigation links to, in its order."""
    return page.locator('[data-testid^="sidebar-settings-/settings/"]').evaluate_all(
        "links => links.map(link => link.dataset.testid.slice('sidebar-settings-'.length))"
    )


def test_no_screen_offers_another_agent_or_edits_an_agent_profile(app, browser):
    """TASK-50 and Q2: the "+" menu, Settings, the command menu, the checklist and an
    automation's setup, as a locked build renders them."""
    page = window(browser)
    page.goto(CANVAS_URL)
    page.get_by_test_id("chat-plus-button").click()
    expect(page.get_by_test_id("tools-context-menu")).to_be_visible()
    expect(page.get_by_test_id("switch-agent-profile-button")).to_have_count(0)
    page.keyboard.press("Escape")
    page.goto(CANVAS_URL + "settings")
    page.wait_for_url(CANVAS_URL + "settings/app")
    expect(page.get_by_test_id("app-settings-screen")).to_be_visible()
    assert settings_navigation(page) == SHOWN_SETTINGS
    expect(page.locator('a[href="/settings/llm"]')).to_have_count(0)
    for hidden in HIDDEN_SETTINGS:
        page.goto(CANVAS_URL + hidden)
        page.wait_for_url(CANVAS_URL + "settings/app")
    page.goto(CANVAS_URL)
    page.get_by_test_id("command-menu-trigger").click()
    expect(page.get_by_test_id("command-menu")).to_be_visible()
    expect(page.locator("#command-menu-option-secrets-settings")).to_be_visible()
    for item in ("agent-settings", "llm-settings", "condenser-settings"):
        expect(page.locator(f"#command-menu-option-{item}")).to_have_count(0)
    page.keyboard.press("Escape")
    checklist = "sidebar-onboarding-checklist-item-"
    expect(page.get_by_test_id(f"{checklist}start-conversation")).to_be_attached()
    for item in ("configure-llm", "customize-agent"):
        expect(page.get_by_test_id(f"{checklist}{item}")).to_have_count(0)
    page.goto(CANVAS_URL + f"automations/new/{AUTOMATION_TEMPLATE}")
    expect(page.get_by_test_id("setup-continue-button")).to_be_visible()
    expect(page.get_by_test_id("automation-agent-profile")).to_have_count(0)


def test_a_question_with_no_model_key_saved_says_where_the_key_goes(app, browser, fake):
    """Q1: the reminder is dr-acp's answer to a question, before any run."""
    page = window(browser)
    start_conversation(page, NO_KEY_QUESTION)
    reminder = acp_texts.missing_model_key(["OPENAI_API_KEY"])
    expect(answer(page, reminder)).to_be_visible()
    assert run_ids(app) == set()
    assert fake.calls == []


def test_every_conversation_starts_from_deep_reasoner_whatever_profile_is_active(
    app, browser, fake, tmp_path
):
    """TASK-50's launch: another profile is made active, here and for the rest of E12,
    and the conversation still runs deep_reasoner."""
    point_the_library_at(
        app,
        fake.base_url,
        tmp_path,
        key=KEY,
        model=E12_MODEL,
        namespace=NAMESPACE,
        decomposition=example(IMPORTED, "Triage e12."),
    )
    other = {"agent_kind": "acp", "acp_server": "custom", "acp_command": "false"}
    app.request("POST", "/api/agent-profiles/e12-other", other)
    [other_id] = [
        p["id"]
        for p in app.request("GET", "/api/agent-profiles")["profiles"]
        if p["name"] == "e12-other"
    ]
    app.request("POST", f"/api/agent-profiles/{other_id}/activate")
    page = window(browser)
    conversation = start_conversation(page, QUESTION)
    expect(answer(page, ANSWER)).to_be_visible()
    launched = app.request("GET", f"/api/conversations/{conversation}")
    assert launched["launched_agent_profile"]["agent_profile_id"] == (
        locked_profile_id(app)
    )


def test_a_conversation_in_the_window_runs_dr_acp_and_its_key_stays_out(
    app, browser, fake
):
    page = window(browser)
    expect(page.get_by_test_id("agent-message").filter(has_text=ANSWER)).to_be_visible()
    assert [call.model for call in fake.calls] == [E12_MODEL, E12_MODEL]
    assert {call.authorization for call in fake.calls} == {f"Bearer {KEY}"}
    environ = worker_environ(app)
    worker = dict(line.split("=", 1) for line in environ.split("\0") if "=" in line)
    assert worker["OPENAI_API_KEY"] not in ("", KEY)
    stored = [
        path.read_bytes().decode(errors="replace")
        for root in (app.data / "runs", app.data / "canvas" / "agent-canvas")
        for path in root.rglob("*")
        if path.is_file() and path.name not in ("api-key.txt", "secret-key.txt")
    ]
    cells = [text for text in stored if worker["OPENAI_API_KEY"] in text]
    assert cells, "the cell printed the worker's environment into the run log"
    for value in (KEY, app.session_key, app.secret_key):
        assert value not in environ
        assert not [text for text in stored if value in text]


def test_the_window_title_names_deep_reasoning_at_home_and_after_a_conversations_title(
    browser,
):
    """Step 5's conversation is still open, after step 6, which only reads it."""
    product = build.load_pins(build.PINS).app.product_name
    page = window(browser)
    expect(page).to_have_title(
        re.compile(rf"{re.escape(QUESTION)} \| {re.escape(product)}$")
    )
    page.goto(CANVAS_URL)
    expect(page).to_have_title(product)


def test_a_new_chats_first_message_shows_no_title_error_with_a_keyless_llm_profile(
    app, browser
):
    """TASK-46: Canvas sends the active LLM profile as the title profile; one with no
    key is never called, and the chat is titled by its first message."""
    llm = f"/api/profiles/{KEYLESS_LLM_PROFILE}"
    app.request("POST", llm, {"llm": {"model": "gpt-5.5"}})
    app.request("POST", f"{llm}/activate")
    page = window(browser)
    conversation = start_conversation(page, TITLE_QUESTION)
    expect(answer(page, TITLE_ANSWER)).to_be_visible()
    eventually(
        lambda: (
            app.request("GET", f"/api/conversations/{conversation}")["title"]
            == TITLE_QUESTION
        )
    )
    events = conversation_events(app, conversation)
    assert [e for e in events if e["kind"] == "ConversationErrorEvent"] == []


def test_nothing_records_telemetry_consent_and_settings_offer_no_analytics_switch(
    app, browser
):
    page = window(browser)
    misc = app.request("GET", "/api/settings")["misc_settings"]
    assert misc.get("app_preferences", {}).get("user_consents_to_analytics") is None
    assert misc.get("telemetry", {}).get("consent") is None
    stored = page.evaluate(f"() => localStorage.getItem({CONSENT_STORAGE_KEY!r})")
    assert stored is None
    page.goto(CANVAS_URL + "settings/app")
    # A settings switch's test id is on its hidden checkbox.
    expect(page.get_by_test_id("enable-sound-notifications-switch")).to_be_attached()
    expect(page.get_by_test_id("enable-analytics-switch")).to_have_count(0)


def test_d3s_frame_works_through_the_bridge_in_electrons_chromium(app, browser):
    page = window(browser)
    frame = library_frame(page, app.session_key)
    expect(frame.get_by_test_id(f"dr-node-{NAMESPACE}")).to_be_visible()
    expect(frame.get_by_test_id("dr-notice")).to_have_count(0)
    cookies = browser.new_browser_cdp_session().send("Storage.getCookies")["cookies"]
    [session] = [c for c in cookies if c["path"] == "/app-backends/dr-library"]
    assert session["partitionKey"]["topLevelSite"] == "http://localhost"
    assert (session["secure"], session["sameSite"]) == (True, "None")
    deleted = page.evaluate(
        """async ([url, key]) => (await fetch(url, {method: "DELETE",
            credentials: "include", headers: {"X-Session-API-Key": key}})).status""",
        [SESSION, app.session_key],
    )
    assert deleted == 204
    inside = page.frame(url=lambda url: url.startswith(f"{INGRESS}/app-backends/"))
    assert inside.evaluate("async () => (await fetch('../health')).status") == 401


def slash_commands(page: Page) -> list[str]:
    """The slash menu's commands for a bare "/", as C2's own spec reads them."""
    page.get_by_test_id("chat-input").click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.press("Backspace")
    page.keyboard.type("/")
    menu = page.get_by_test_id("slash-command-menu")
    expect(menu).to_be_visible()
    commands = menu.get_by_test_id("slash-command-item").evaluate_all(
        "items => items.map(item => item.getAttribute('data-command'))"
    )
    page.keyboard.press("Escape")
    return commands


def new_run(app: LaunchedApp, before: set[str]) -> str:
    [run_id] = run_ids(app) - before
    return run_id


def run_start(app: LaunchedApp, run_id: str) -> RunStart:
    return next(
        e for e in RunLog.read(Home(app.data), run_id) if isinstance(e, RunStart)
    )


def run_asked(app: LaunchedApp, task: str) -> str:
    """The run whose first prompt's task was task."""
    [run_id] = [
        r
        for r in run_ids(app)
        if any(
            isinstance(e, PromptStart) and e.task == task
            for e in RunLog.read(Home(app.data), r)
        )
    ]
    return run_id


def row_titled(page: Page, title: str) -> Locator:
    """The sub-agent row whose own title is title (a row also holds its children's),
    once it is shown: a child's row is in its parent's, shown expanded."""
    titles = page.get_by_test_id("subagent-title").filter(has_text=title)

    def shown() -> bool:
        expand_all_subagents(page)
        return titles.count() > 0

    eventually(shown)
    session = page.get_by_test_id("subagent-row").evaluate_all(
        """(rows, title) => rows.find(row =>
            row.querySelector('[data-testid="subagent-title"]').textContent === title
        ).getAttribute("data-acp-session-id")""",
        title,
    )
    return page.locator(
        f'[data-testid="subagent-row"][data-acp-session-id="{session}"]'
    )


def expanded_rows(page: Page) -> int:
    """How many sub-agent rows show, every block and row expanded."""
    expand_all_subagents(page)
    return page.get_by_test_id("subagent-row").count()


def test_sub_agents_nest_under_the_cells_that_spawned_them_as_the_run_log_records(
    app, browser
):
    page = window(browser)
    before = run_ids(app)
    start_conversation(page, TREE_QUESTION)
    expect(answer(page, TREE_ANSWER)).to_be_visible()
    recorded, _ = recorded_subagent_tree(app.data, new_run(app, before))
    nested = [link for link in recorded if link["parentSessionId"] is not None]
    assert (len(recorded), len(nested)) == (3, 1)

    def nested_as_recorded() -> bool:
        expand_all_subagents(page)
        return read_rendered_subagent_tree(page) == recorded

    eventually(nested_as_recorded)
    rows = page.get_by_test_id("subagent-row")
    expect(rows).to_have_count(3)
    for row in rows.all():
        expect(row).to_have_attribute("data-subagent-status", "done")
        expect(row.get_by_test_id("subagent-status").first).to_have_text("done")


def test_each_sub_agent_shows_its_latest_cost_by_default_and_none_once_turned_off(
    app, browser
):
    """TASK-51: the setting untouched, costs show; turned off, none does."""
    page = window(browser)
    conversation = page.url
    _, costs = recorded_subagent_tree(app.data, run_asked(app, TREE_QUESTION))
    assert expanded_rows(page) == 3
    for session, cost in costs.items():
        row = page.locator(
            f'[data-testid="subagent-row"][data-acp-session-id="{session}"]'
        )
        expect(row.get_by_test_id("subagent-cost").first).to_have_text(
            subagent_cost(cost)
        )
    page.goto(CANVAS_URL + "settings/app")
    switch = page.get_by_test_id("show-subagent-costs-switch")
    expect(switch).to_be_checked()
    page.locator("label", has=switch).click()
    expect(switch).not_to_be_checked()
    page.goto(conversation)
    expect(page.get_by_test_id("subagent-block-toggle")).to_be_visible()
    eventually(lambda: expanded_rows(page) == 3)
    expect(page.get_by_test_id("subagent-cost")).to_have_count(0)


def test_stop_on_one_sub_agent_stops_it_and_its_branch(app, browser):
    page = window(browser)
    before = run_ids(app)
    conversation = start_conversation(page, STOP_QUESTION)
    eventually(lambda: bool(run_ids(app) - before))
    events = app.data / "runs" / new_run(app, before) / "events.jsonl"
    slow, deeper, quick = (row_titled(page, title) for title in (SLOW, DEEPER, QUICK))
    expand_all_subagents(page)
    expect(quick).to_have_attribute("data-subagent-status", "done")
    expect(deeper).to_have_attribute("data-subagent-status", "running")
    stop = slow.get_by_test_id("subagent-stop").first
    expect(stop).to_have_attribute("data-subagent-stop", "ready")
    session = slow.get_attribute("data-acp-session-id")
    cancel = f"/api/conversations/{conversation}/acp/sessions/{session}/cancel"
    with page.expect_response(lambda r: r.url.endswith(cancel)) as sent:
        stop.click()
    assert sent.value.ok, sent.value.status
    eventually(lambda: '"stop.accepted"' in events.read_text())
    STOPPED.set()
    expect(answer(page, STOP_ANSWER)).to_be_visible()
    expand_all_subagents(page)
    expect(slow).to_have_attribute("data-subagent-status", "stopped")
    expect(deeper).to_have_attribute("data-subagent-status", "stopped")
    expect(quick).to_have_attribute("data-subagent-status", "done")
    expect(page.get_by_test_id("subagent-stop")).to_have_count(0)


def test_the_home_screen_offers_the_namespaces_and_each_ones_decompositions(
    app, browser
):
    page = window(browser)
    page.goto(CANVAS_URL)
    expect(page.get_by_test_id("agent-options")).to_be_visible()
    expect(page.get_by_test_id("agent-option-namespace")).to_have_attribute(
        "data-value", "root"
    )
    imported = f"/{slug(IMPORTED)}"
    assert imported not in slash_commands(page)
    pick_namespace(page, NAMESPACE)
    eventually(lambda: imported in slash_commands(page))


def panel_tab(page: Page, tab: str) -> FrameLocator:
    """D3's frame in C2's header panel, on tab. Clicking the selected tab would close
    the panel."""
    content = page.get_by_test_id("conversation-app-panel-content")
    if content.get_attribute("data-tab-id") != tab:
        page.get_by_test_id(f"conversation-app-panel-tab-{tab}").click()
    expect(content).to_have_attribute("data-tab-id", tab)
    frame = page.frame_locator('[data-testid="conversation-app-panel-content"] iframe')
    expect(frame.locator("main")).to_be_visible()
    return frame


def open_panel(page: Page) -> None:
    """Show Decompositions: C2's header button for D3's panel, unless it is open."""
    toggle = page.get_by_test_id(
        "conversation-app-panel-toggle-dr-library-decompositions"
    )
    if toggle.get_attribute("aria-pressed") != "true":
        toggle.click()
    expect(toggle).to_have_attribute("aria-pressed", "true")
    expect(page.get_by_test_id("conversation-app-panel")).to_be_visible()


def test_create_decomposition_in_the_header_panel_saves_into_the_conversations_namespace(
    app, browser
):
    page = window(browser)
    start_conversation(page, PANEL_QUESTION, NAMESPACE)
    expect(answer(page, PANEL_ANSWER)).to_be_visible()
    open_panel(page)
    namespaces = panel_tab(page, "namespaces")
    expect(namespaces.get_by_test_id(f"dr-node-{NAMESPACE}")).to_be_visible()
    create = panel_tab(page, "create")
    create.get_by_test_id("dr-name").fill(CREATED)
    create.get_by_test_id("dr-use-when").fill("ranking e12's courses")
    create.get_by_test_id("dr-card-0-task").fill(CREATED_TASK)
    create.get_by_test_id("dr-card-1-code").fill("FinalAnswer('first')")
    expect(create.get_by_test_id(f"dr-namespace-{NAMESPACE}")).to_be_checked()
    create.get_by_test_id("dr-save").click()
    expect(create.get_by_test_id("dr-result")).to_contain_text(
        f"✓ Saved '{CREATED}' v1 in {NAMESPACE}."
    )


def test_the_next_conversation_in_the_namespace_offers_the_decomposition_and_uses_it(
    app, browser, fake
):
    page = window(browser)
    page.goto(CANVAS_URL)
    pick_namespace(page, NAMESPACE)
    command = f"/{slug(CREATED)}"
    eventually(lambda: command in slash_commands(page))
    before, asked = run_ids(app), len(fake.calls)
    start_conversation(page, NEXT_TASK, NAMESPACE)
    expect(answer(page, NEXT_ANSWER)).to_be_visible()
    start = run_start(app, new_run(app, before))
    assert start.namespace == NAMESPACE
    assert start.source["versions"]["decompositions"][CREATED] == 1
    first = fake.calls[asked]
    assert any(CREATED_TASK in str(m.get("content")) for m in first.messages)


def test_the_spend_cap_set_in_the_tools_tab_caps_the_next_conversation(app, browser):
    """Q3: the field writes the profile's --spend-cap-usd, keeping --home, and the key
    proxy of the next conversation holds it to that cap."""
    page = window(browser)
    open_panel(page)
    tools = panel_tab(page, "tools")
    expect(tools.get_by_test_id("dr-spend-cap-input")).to_have_value("5")
    expect(tools.get_by_test_id("dr-notice")).to_have_count(0)
    expect(tools.get_by_test_id("dr-tools-risk")).to_have_count(0)
    tools.get_by_test_id("dr-spend-cap-input").fill(CAP)
    tools.get_by_test_id("dr-spend-cap-save").click()
    expect(tools.get_by_test_id("dr-spend-cap-status")).to_have_text(
        spend_cap_saved(CAP)
    )
    profile = f"/api/agent-profiles/{build.LOCKED_PROFILE}"
    args = app.request("GET", profile)["profile"]["acp_args"]
    assert args[:2] == ["--home", str(app.data)]
    assert args[-2:] == ["--spend-cap-usd", CAP]
    before = spend_caps(app)
    start_conversation(page, CAP_QUESTION)
    expect(answer(page, CAP_ANSWER)).to_be_visible()
    eventually(lambda: spend_caps(app).keys() - before.keys())
    caps = spend_caps(app)
    assert [caps[s] for s in caps.keys() - before.keys()] == [float(CAP)]


def test_an_mcp_server_granted_in_the_tools_tab_is_called_by_the_next_conversation(
    app, browser
):
    page = window(browser)
    server = {"command": str(app.runtime_bin / "python"), "args": [str(ECHO_SERVER)]}
    app.request("POST", "/api/settings/mcp/echo", server)
    open_panel(page)
    panel_tab(page, "browse")  # the Tools tab reads Canvas's MCP settings as it opens
    tools = panel_tab(page, "tools")
    tools.get_by_test_id(f"dr-mcp-grant-echo-{NAMESPACE}").check()
    expect(tools.get_by_test_id("dr-mcp-seen-echo")).to_be_visible()
    before = run_ids(app)
    start_conversation(page, MCP_QUESTION, NAMESPACE)
    expect(answer(page, MCP_REPLY)).to_be_visible()
    run_id = new_run(app, before)
    [status] = [
        e for e in RunLog.read(Home(app.data), run_id) if isinstance(e, McpStatus)
    ]
    assert [(s.tool, s.state) for s in status.servers] == [("echo", "bound")]


def test_the_header_panel_keeps_working_past_its_first_backend_session(app, browser):
    page = window(browser)
    open_panel(page)
    opened = time.monotonic()
    namespaces = panel_tab(page, "namespaces")
    expect(namespaces.get_by_test_id(f"dr-node-{NAMESPACE}")).to_be_visible()
    page.wait_for_timeout((SESSION_S + 20 - (time.monotonic() - opened)) * 1000)
    expect(namespaces.get_by_test_id("dr-backend-lost")).to_have_count(0)
    browse = panel_tab(page, "browse")
    expect(browse.get_by_test_id(f"dr-row-{NAMESPACE}-{slug(CREATED)}")).to_be_visible()


def test_closing_the_window_quits_the_app_and_leaves_nothing_running(app, browser):
    started = time.monotonic()
    window(browser).close()
    app.process.wait(timeout=QUIT_S)
    while processes_mentioning(str(app.home)) and time.monotonic() - started < QUIT_S:
        time.sleep(0.2)
    assert processes_mentioning(str(app.home)) == []


def test_setup_relaunches_offline_from_its_cache_and_installs_nothing(app):
    command = installed_defaults()["setup"]["command"]
    env = user_environment(app.home) | {
        "OH_CANVAS_SETUP_PHASE": "before-start",
        "PATH": f"{APP.parent / 'resources' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    }
    started = time.monotonic()
    done = subprocess.run(
        [*NETWORK_CUT, *command],
        env=env,
        cwd=app.data / "canvas" / "agent-canvas",
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    took = time.monotonic() - started
    assert done.returncode == 0, done.stdout + done.stderr
    assert took < OFFLINE_S, f"{took:.1f} s"
    assert not [
        line for line in done.stdout.splitlines() if line.startswith(INSTALLING)
    ]


def uvx_in_the_cut(app: LaunchedApp, *args: str) -> subprocess.CompletedProcess:
    """The app's own uvx inside the cut network, from the HOME's uv cache."""
    return subprocess.run(
        [*NETWORK_CUT, str(APP_UVX), *args],
        env=user_environment(app.home),
        cwd=app.home,
        capture_output=True,
        text=True,
        timeout=RELAUNCH_S,
        check=False,
    )


def wait_for_a_line(app: LaunchedApp, test: Callable[[str], bool], what: str) -> None:
    deadline = time.monotonic() + RELAUNCH_S
    while not any(test(line) for line in app.lines()):
        if app.process.poll() is not None or time.monotonic() > deadline:
            app.fail(f"no {what} in {RELAUNCH_S} s")
        time.sleep(1.0)


def test_with_index_answers_that_expire_uv_goes_to_the_network_and_offline_uv_still_runs(
    expiring,
):
    """The negative control for the next step: where uv's index answers expire a second
    after each fetch, uvx of the automation backend the first launch there installed
    needs the network, and --offline still runs it from the cache."""
    defaults = installed_defaults()
    automation = (
        *("--exclude-newer", defaults["uv"]["excludeNewer"]),
        "--from",
        f"{defaults['packages']['automation']}=={defaults['versions']['automation']}",
        *("python", "-c", "pass"),
    )
    online_first = uvx_in_the_cut(expiring, *automation)
    assert online_first.returncode != 0, "uv ran on expired answers without PyPI"
    offline = uvx_in_the_cut(expiring, "--offline", *automation)
    assert offline.returncode == 0, offline.stderr


def test_the_app_relaunches_offline_once_uvs_index_answers_have_expired(
    expiring, tmp_path
):
    """From the HOME whose index answers expire, as after uv's ten minutes (TASK-66
    §5.4): the relaunch inside the cut starts both services offline and installs
    nothing."""
    started = time.monotonic()
    relaunched = launch(expiring.home, tmp_path / "relaunch.log", network=False)
    try:
        relaunched.wait_for_line("[agent-server] Ready at", RELAUNCH_S)
        ready = time.monotonic() - started
        wait_for_a_line(
            relaunched,
            lambda line: "[automation]" in line and AUTOMATION_STARTED in line,
            "automation start",
        )
        lines = relaunched.lines()
        for service in ("agent-server", "automation"):
            assert [line for line in lines if f"[{service}] {STARTING_OFFLINE}" in line]
        assert not [line for line in lines if INSTALLING in line]
        assert not [line for line in lines if STARTUP_FAILED in line]
        relaunched.process.send_signal(signal.SIGTERM)
        relaunched.process.wait(timeout=QUIT_S)
        deadline = time.monotonic() + QUIT_S
        while processes_mentioning(str(expiring.home)) and time.monotonic() < deadline:
            time.sleep(0.2)
        assert processes_mentioning(str(expiring.home)) == []
        print(f"offline relaunch: the agent-server ready in {ready:.1f} s")
    finally:
        relaunched.stop()
