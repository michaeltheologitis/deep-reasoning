"""E12: the installed Linux app, launched as a user would launch it, on a fake model
(D5 §7.5).

cross-repo.yml's desktop-e2e job builds the packages from the pins (desktop/build.py
linux), installs the .deb and runs this module under xvfb-run. Its tests share one
first launch and run in order: the launch, a conversation, D3's frame through the
bridge; then the final part: C1's nested sub-agents and a Stop of one, C2's namespace
picker, slash menu and header panel with Create decomposition, an MCP server granted in
D4's Tools tab, and the panel past its first session; then the quit and an offline
relaunch of setup. No test calls a real model.
"""

import json
import os
import re
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import yaml
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

from deep_reasoning.acp.catalog import slug
from deep_reasoning.acp.runlog import Home, McpStatus, PromptStart, RunLog, RunStart
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from dr_app import texts
from tests.acp.scenarios import repl, scripted, task_and_turn
from tests.desktop.app import (
    APP,
    CANVAS_URL,
    FIRST_LAUNCH_S,
    QUIT_S,
    LaunchedApp,
    fresh_home,
    launch,
    processes_mentioning,
    secret,
    user_environment,
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
SESSION = f"{INGRESS}/app-backends/dr-library/session"
BACKEND = "/api/canvas-extensions/installed/dr-library/backend"
QUESTION = "What does E12 answer?"
ANSWER = secret("e12-answer-")
E12_MODEL = "e12-model"
NAMESPACE = "e12"
OFFLINE_S = 5.0
ENVIRONMENT_CELL = repl(
    "import os",
    "print(dict(os.environ))",
    "print(open('/proc/self/environ', 'rb').read())",
)
# C1: a fan-out whose first child spawns one of its own.
TREE_QUESTION = "How do the e12 courses compare?"
TREE_ANSWER = secret("e12-tree-")
# C1's Stop: one child waits on a grandchild whose model call is held until E12 presses
# Stop on the child, so both are running then; the other child is done by then.
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
        repl(
            f"r = run_all({{t: anext(subagent().send(t)) for t in {[SLOW, QUICK]!r}}})",
            "print(r)",
        ),
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
}
# $0.002 a call at E12_MODEL's price, so each sub-agent's cost has a few digits.
USAGE = {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500}
KEY = secret("sk-e12-")
STOPPED = threading.Event()  # E12 has pressed Stop and dr-acp has accepted it
expect.set_options(timeout=60_000)


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


@pytest.fixture(scope="module")
def app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LaunchedApp]:
    """The first launch, with a fresh HOME: a cold uv cache, nothing installed."""
    with fresh_home() as home:
        log = tmp_path_factory.mktemp("e12") / "app.log"
        launched = launch(home, log)
        try:
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


def setup_lines(app: LaunchedApp, phase: str) -> list[str]:
    """What the setup command printed in a phase, without the launcher's prefixes."""
    marker = f"[setup {phase}] "
    return [line.split(marker, 1)[1] for line in app.lines() if marker in line]


def test_the_first_launch_installs_everything_and_opens_the_window(app, browser):
    app.wait_for_line("[setup after-ready] Done in", FIRST_LAUNCH_S)
    page = window(browser)
    expect(page.get_by_test_id("first-run-onboarding-screen")).to_be_visible()
    before, after = setup_lines(app, "before-start"), setup_lines(app, "after-ready")
    assert texts.home_local(str(app.data)) in before
    assert texts.safety("5") in before
    assert any(line.startswith("installed in ") for line in before)
    assert texts.PROFILE_CREATED in after
    assert texts.app_ready("0.1.0", "installed") in after
    assert app.request("GET", BACKEND)["state"] == "ready"
    info = app.request("GET", "/server_info")
    assert info["app_backend_ingress_url"] == INGRESS
    profiles = app.request("GET", "/api/agent-profiles")
    [ours] = [p for p in profiles["profiles"] if p["name"] == "deep_reasoner"]
    assert profiles["active_agent_profile_id"] == ours["id"]


def point_the_library_at(app: LaunchedApp, fake: FakeOpenAI, directory: Path) -> None:
    """The model key as a Canvas secret, and a Library whose run settings call the fake,
    with its model priced for the spend cap."""
    app.request(
        "PUT", "/api/settings/secrets", {"name": "OPENAI_API_KEY", "value": KEY}
    )
    config = directory / "main.yaml"
    client = {"base_url": fake.base_url, "api_key_env": "OPENAI_API_KEY"}
    config.write_text(
        yaml.safe_dump(
            {
                "model": E12_MODEL,
                "client": client | {"max_retries": 0},
                "system_prompt": "You are a scripted test agent.",
                "max_iter": 6,
                "max_depth": 3,
                "entry_namespace": "root",
                "namespaces": {
                    "root": {},
                    NAMESPACE: {"decompositions": [example(IMPORTED, "Triage e12.")]},
                },
            },
            sort_keys=False,
        )
    )
    price = {"input_per_mtok": 1.0, "output_per_mtok": 2.0, "context_window": 200000}
    (app.data / "prices.yaml").write_text(yaml.safe_dump({E12_MODEL: price}))
    subprocess.run(
        [app.runtime_bin / "dr-library", "import", config, "--home", app.data],
        env=user_environment(app.home),
        check=True,
        capture_output=True,
    )


def example(name: str, task: str) -> dict:
    """A decomposition: the task, then a turn that answers it."""
    return {
        "name": name,
        "messages": [
            {"role": "user", "content": task},
            {"role": "assistant", "content": repl("FinalAnswer('done')")},
        ],
    }


def dismiss_onboarding(page: Page) -> None:
    """Canvas's first-run telemetry question and onboarding, which would otherwise make
    an OpenHands profile the default."""
    consent = page.get_by_test_id("telemetry-consent-form")
    consent.get_by_role("checkbox").uncheck()
    page.get_by_test_id("confirm-telemetry-preferences").click()
    page.get_by_test_id("onboarding-skip").click()


def run_ids(app: LaunchedApp) -> set[str]:
    return {path.parent.name for path in (app.data / "runs").glob("*/events.jsonl")}


def worker_environ(app: LaunchedApp) -> str:
    """The run's worker's environment, by the pid its run log records."""
    [run_id] = run_ids(app)
    events = app.data / "runs" / run_id / "events.jsonl"
    for line in events.read_text().splitlines():
        event = json.loads(line)
        if event["kind"] == "worker.ready":
            return Path(f"/proc/{event['pid']}/environ").read_bytes().decode()
    raise AssertionError("no worker.ready in the run log")


def test_a_conversation_in_the_window_runs_dr_acp_and_its_key_stays_out(
    app, browser, fake, tmp_path
):
    point_the_library_at(app, fake, tmp_path)
    page = window(browser)
    dismiss_onboarding(page)
    page.get_by_test_id("chat-input").fill(QUESTION)
    page.get_by_test_id("submit-button").click()
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


def test_d3s_frame_works_through_the_bridge_in_electrons_chromium(app, browser):
    page = window(browser)
    made = page.evaluate(
        """async ([url, key]) => {
            const r = await fetch(url, {method: "POST", credentials: "include",
                                        headers: {"X-Session-API-Key": key}});
            return {status: r.status, body: await r.json()};
        }""",
        [SESSION, app.session_key],
    )
    assert made["status"] == 200, made
    page.evaluate(
        """(src) => {
            const frame = document.createElement("iframe");
            frame.id = "e12-frame";
            frame.src = src;
            frame.style = "position:fixed;inset:0;width:100%;height:100%;z-index:99999";
            document.body.appendChild(frame);
        }""",
        made["body"]["ingress_url"] + "ui/?tab=namespaces&cap=5",
    )
    frame = page.frame_locator("#e12-frame")
    expect(frame.get_by_test_id("dr-notice")).to_contain_text(texts.safety("5"))
    frame.get_by_test_id("dr-notice-ack").click()
    expect(frame.get_by_test_id(f"dr-node-{NAMESPACE}")).to_be_visible()
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


def eventually(check: Callable[[], bool], timeout_s: float = 60.0) -> None:
    """check() until it holds, or fail at timeout_s."""
    deadline = time.monotonic() + timeout_s
    while not check():
        assert time.monotonic() < deadline, f"not within {timeout_s} s"
        time.sleep(0.5)


def answer(page: Page, text: str) -> Locator:
    return page.get_by_test_id("agent-message").filter(has_text=text)


def pick_namespace(page: Page, namespace: str) -> None:
    """C2's option picker on the home screen: dr-acp's namespace option, picked and
    accepted by the agent's preview (the pill is disabled while one is pending)."""
    pill = page.get_by_test_id("agent-option-namespace")
    expect(pill).to_be_enabled()
    pill.click()
    page.get_by_test_id(f"agent-option-namespace-value-{namespace}").click()
    eventually(
        lambda: pill.is_enabled() and pill.get_attribute("data-value") == namespace
    )


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


def start_conversation(page: Page, text: str, namespace: str | None = None) -> str:
    """From the home screen, in namespace when one is named; the conversation's id."""
    page.goto(CANVAS_URL)
    if namespace is not None:
        pick_namespace(page, namespace)
    page.get_by_test_id("chat-input").fill(text)
    page.get_by_test_id("submit-button").click()
    page.wait_for_url(re.compile(r".*/conversations/[^/?]+$"))
    return page.url.rsplit("/", 1)[-1]


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
        expect(row.get_by_test_id("subagent-status")).to_be_visible()


def test_each_sub_agent_shows_its_latest_cost_once_the_setting_is_on(app, browser):
    page = window(browser)
    conversation = page.url
    _, costs = recorded_subagent_tree(app.data, run_asked(app, TREE_QUESTION))
    expand_all_subagents(page)
    expect(page.get_by_test_id("subagent-row")).to_have_count(3)
    expect(page.get_by_test_id("subagent-cost")).to_have_count(0)
    page.goto(CANVAS_URL + "settings/app")
    switch = page.get_by_test_id("show-subagent-costs-switch")
    page.locator("label", has=switch).click()
    expect(switch).to_be_checked()
    page.goto(conversation)
    expect(page.get_by_test_id("subagent-row")).to_have_count(3)
    expand_all_subagents(page)
    for session, cost in costs.items():
        row = page.locator(
            f'[data-testid="subagent-row"][data-acp-session-id="{session}"]'
        )
        expect(row.get_by_test_id("subagent-cost").first).to_have_text(
            subagent_cost(cost)
        )


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
    """D3's frame in C2's header panel, on tab; the safety notice acknowledged.
    Clicking the selected tab would close the panel."""
    content = page.get_by_test_id("conversation-app-panel-content")
    if content.get_attribute("data-tab-id") != tab:
        page.get_by_test_id(f"conversation-app-panel-tab-{tab}").click()
    expect(content).to_have_attribute("data-tab-id", tab)
    frame = page.frame_locator('[data-testid="conversation-app-panel-content"] iframe')
    shown = frame.get_by_test_id("dr-notice-ack").or_(frame.locator("main"))
    expect(shown.first).to_be_visible()
    if frame.get_by_test_id("dr-notice-ack").is_visible():
        frame.get_by_test_id("dr-notice-ack").click()
    return frame


def open_panel(page: Page) -> None:
    """Show decompositions: C2's header button for D3's panel, unless it is open."""
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
    start_conversation(page, f"{command} {NEXT_TASK}", NAMESPACE)
    expect(answer(page, NEXT_ANSWER)).to_be_visible()
    start = run_start(app, new_run(app, before))
    assert start.namespace == NAMESPACE
    assert start.source["versions"]["decompositions"][CREATED] == 1
    first = fake.calls[asked]
    assert any(CREATED_TASK in str(m.get("content")) for m in first.messages)


def test_an_mcp_server_granted_in_the_tools_tab_is_called_by_the_next_conversation(
    app, browser
):
    page = window(browser)
    server = {"command": str(app.runtime_bin / "python"), "args": [str(ECHO_SERVER)]}
    app.request("POST", "/api/settings/mcp/echo", server)
    open_panel(page)
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
    defaults = APP.parent / "resources" / "app" / "config" / "defaults.json"
    command = json.loads(defaults.read_text())["setup"]["command"]
    env = user_environment(app.home) | {
        "OH_CANVAS_SETUP_PHASE": "before-start",
        "PATH": f"{APP.parent / 'resources' / 'bin'}{os.pathsep}{os.environ['PATH']}",
    }
    offline = ["unshare", "--map-root-user", "-n", "sh", "-c"]
    loopback_up = 'ip link set lo up && exec "$@"'
    started = time.monotonic()
    done = subprocess.run(
        [*offline, loopback_up, "offline", *command],
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
    assert "installing deep-reasoning" not in done.stdout
