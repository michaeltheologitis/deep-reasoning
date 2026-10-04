"""E12, the skeleton flow: the installed Linux app, launched as a user would launch it,
on a fake model (D5 §7.5).

cross-repo.yml's desktop-e2e job builds the packages from the pins (desktop/build.py
linux), installs the .deb and runs this module under xvfb-run. Its tests share one
first launch and run in order: the launch, a conversation, D3's frame through the
bridge, the quit, and an offline relaunch of setup. No test calls a real model.
"""

import json
import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml
from playwright.sync_api import (
    Browser,
    Error,
    Page,
    expect,
    sync_playwright,
)
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from dr_app import texts
from tests.acp.scenarios import repl, scripted
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
PLAN = {QUESTION: [ENVIRONMENT_CELL, repl(f"FinalAnswer({ANSWER!r})")]}
KEY = secret("sk-e12-")
expect.set_options(timeout=60_000)


@pytest.fixture(scope="module")
def fake() -> Iterator[FakeOpenAI]:
    with FakeOpenAI(scripted(PLAN)) as model:
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
                "entry_namespace": "root",
                "namespaces": {"root": {}, NAMESPACE: {}},
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


def dismiss_onboarding(page: Page) -> None:
    """Canvas's first-run telemetry question and onboarding, which would otherwise make
    an OpenHands profile the default."""
    consent = page.get_by_test_id("telemetry-consent-form")
    consent.get_by_role("checkbox").uncheck()
    page.get_by_test_id("confirm-telemetry-preferences").click()
    page.get_by_test_id("onboarding-skip").click()


def worker_environ(app: LaunchedApp) -> str:
    """The run's worker's environment, by the pid its run log records."""
    [events] = list((app.data / "runs").glob("*/events.jsonl"))
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
