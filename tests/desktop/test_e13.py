"""E13: the browser command, run as the README gives it from a fresh HOME, on a tarball
build.py web made, and driven in Playwright's own browsers on a fake model (TASK-48 §7.4).

Run it after uv run desktop/build.py web, as uv run pytest -m web
tests/desktop/test_e13.py; without the tarball it skips. Its tests share one first start
and run in order: the setup it ran; the stack's processes, environment and sockets; the
page refusing a host name that is not this machine; a conversation; the Library panel
through the bridge in Chromium, Firefox and WebKit; a second start refused; Ctrl+C; then
a restart with the network cut. Last, from a second first start whose uv index answers
expire a second after each fetch, the same restart, which starts both services from uv's
cache at the tarball's PyPI cutoff (TASK-66). The terminal it starts from holds junk
that a user's might: the command must keep all of it from the stack. No test calls a
real model.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Playwright, expect, sync_playwright

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from desktop import build
from dr_app import texts
from dr_web import cache
from tests.acp.scenarios import repl, scripted
from tests.desktop.app import (
    AGENT_SERVER,
    AGENT_SERVER_PORT,
    ANSI,
    CANVAS_URL,
    FIRST_LAUNCH_S,
    LIBRARY_APP_VERSION,
    NETWORK_CUT,
    STARTING_OFFLINE,
    LaunchedApp,
    answer,
    cmdline,
    descendants,
    environ,
    eventually,
    example,
    executable,
    expire_uv_index_answers_quickly,
    fresh_home,
    get_with_host,
    interrupt,
    launch_web,
    library_frame,
    listening_sockets,
    mark_onboarded,
    point_the_library_at,
    processes_mentioning,
    run_ids,
    secret,
    setup_lines,
    snapshot,
    start_conversation,
    user_environment,
    uvx_start_records,
    web_command,
    web_text,
    worker_environ,
)

PINS = build.load_pins(build.PINS)
TARBALL = build.REPO / "dist" / build.web_tarball_name(PINS.app.version)

pytestmark = [
    pytest.mark.web,
    pytest.mark.skipif(not TARBALL.exists(), reason=f"no {TARBALL}: build.py web"),
]

HEAD = build.git("rev-parse", "HEAD", cwd=build.REPO).strip()
# What a user's terminal may hold, which the stack must never see.
JUNK = {
    "PYTHONPATH": "/nonexistent/e13",
    "VIRTUAL_ENV": "/nonexistent/e13-venv",
    "OH_AGENT_SERVER_GIT_REF": "main",
    "VITE_POSTHOG_API_KEY": "phc_e13",
}
# A Node first on PATH that fails loudly: nothing of the stack may run a system Node.
SYSTEM_NODE_MARKER = "e13: a system node ran"
RUNNING = "Deep Reasoning is running at "
PAGE_PORT = 8000  # the ingress, without --port
STACK_PORTS = (PAGE_PORT, 3001, 18000, 18001)
REFUSED_S = 10.0
STOPPED_S = 10.0
SERVED_S = 30.0
QUESTION = "What does E13 answer?"
ANSWER = secret("e13-answer-")
E13_MODEL = "e13-model"
NAMESPACE = "e13"
IMPORTED = "e13 triage"
KEY = secret("sk-e13-")
CONSENT_SHOWS_S = 5
AUTOMATION_UP_S = 180.0
expect.set_options(timeout=60_000)
ENVIRONMENT_CELL = repl(
    "import os",
    "print(dict(os.environ))",
    "print(open('/proc/self/environ', 'rb').read())",
)
PLAN = {QUESTION: [ENVIRONMENT_CELL, repl(f"FinalAnswer({ANSWER!r})")]}
# Started inside the cut network: the command, the page polled until it answers, then
# Ctrl+C. Prints "served <seconds>" when it did; exits with the command's code.
OFFLINE_START = f"""
import os, signal, subprocess, sys, time, urllib.request
log, *command = sys.argv[1:]
opener = urllib.request.build_opener(urllib.request.ProxyHandler({{}}))
with open(log, "ab") as out:
    started = time.monotonic()
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out,
                               stderr=subprocess.STDOUT, start_new_session=True)
    while process.poll() is None and time.monotonic() - started < {SERVED_S * 2}:
        try:
            with opener.open("http://127.0.0.1:8000/", timeout=2) as page:
                if page.status == 200:
                    print(f"served {{time.monotonic() - started:.1f}}", flush=True)
                    break
        except OSError:
            time.sleep(0.5)
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGINT)
    sys.exit(process.wait(timeout=60))
"""


@dataclass
class FirstStart:
    web: LaunchedApp
    command: list[str]
    env: dict[str, str]
    took_s: float


def system_node(folder: Path) -> Path:
    folder.mkdir()
    for name in ("node", "npm", "npx"):
        (folder / name).write_text(
            f"#!/bin/sh\necho '{SYSTEM_NODE_MARKER}' >&2\nexit 97\n"
        )
        (folder / name).chmod(0o755)
    return folder


@pytest.fixture(scope="module")
def fake() -> Iterator[FakeOpenAI]:
    with FakeOpenAI(scripted(PLAN)) as model:
        yield model


@contextmanager
def started_fresh(logs: Path, *, expiring: bool = False) -> Iterator[FirstStart]:
    """The command's first start from a fresh HOME, running, from a terminal holding JUNK
    and a system Node that fails; stopped on the way out. When expiring, uv's index
    answers under that HOME stay fresh for a second only."""
    with fresh_home() as home:
        if expiring:
            expire_uv_index_answers_quickly(home)
        env = user_environment(home) | JUNK
        env["PATH"] = f"{system_node(logs / 'system-node')}{os.pathsep}{env['PATH']}"
        started = time.monotonic()
        command = web_command(HEAD, TARBALL, "--no-open")
        web = launch_web(home, logs / "web.log", command, env=env)
        try:
            web.wait_for_line(RUNNING, FIRST_LAUNCH_S)
            yield FirstStart(web, command, env, time.monotonic() - started)
        finally:
            if web.process.poll() is None:
                interrupt(web)
                web.stop()
            print(f"the command's log: {web.log}")


@pytest.fixture(scope="module")
def first(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FirstStart]:
    """The first start, from a fresh HOME: a cold uv cache, nothing installed."""
    with started_fresh(tmp_path_factory.mktemp("e13")) as started:
        yield started


@pytest.fixture(scope="module")
def expiring(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FirstStart]:
    """Another first start, from a HOME whose uv index answers stay fresh for a second,
    as if every later start came past their ten minutes; stopped once both services have
    recorded their online start."""
    logs = tmp_path_factory.mktemp("e13-expiring")
    with started_fresh(logs, expiring=True) as started:
        eventually(lambda: len(uvx_start_records(started.web)) >= 2, AUTOMATION_UP_S)
        interrupt(started.web)
        assert started.web.process.wait(timeout=STOPPED_S) == 0
        yield started


@pytest.fixture(scope="module")
def playwright() -> Iterator[Playwright]:
    with sync_playwright() as running:
        yield running


@pytest.fixture(scope="module")
def chromium(playwright: Playwright) -> Iterator[Browser]:
    browser = playwright.chromium.launch()
    try:
        yield browser
    finally:
        browser.close()


def stack(web: LaunchedApp) -> list[int]:
    """The services: everything the launcher started, below the command and its Node."""
    [launcher] = [
        pid
        for pid in descendants(web.process.pid)
        if "deep-reasoning.mjs" in cmdline(pid)
    ]
    return descendants(launcher)


def test_the_first_start_sets_up_as_the_app_does(first):
    web = first.web
    before, after = setup_lines(web, "before-start"), setup_lines(web, "after-ready")
    assert texts.home_local(str(web.data)) in before
    assert any(line.startswith("installed in ") for line in before)
    assert texts.PROFILE_CREATED in after
    assert texts.app_ready(LIBRARY_APP_VERSION, "installed") in after
    info = web.request("GET", "/server_info")
    assert info["app_backend_ingress_url"] == AGENT_SERVER
    [left_out] = [
        line for line in web.lines() if line.startswith("Left out of the environment")
    ]
    assert set(JUNK) <= set(left_out.split(": ", 1)[1].split(", "))
    print(f"the cold first start took {first.took_s:.0f} s")
    print(f"the tarball is {TARBALL.stat().st_size / 1e6:.1f} MB")


def test_the_stack_runs_the_pinned_agent_server_on_the_wheels_node_with_nothing_of_the_terminal(
    first,
):
    web = first.web
    services = stack(web)
    lines = {pid: cmdline(pid) for pid in services}
    agent_server = [pid for pid, line in lines.items() if "agent-server" in line]
    automation = [
        pid for pid, line in lines.items() if "openhands.automation.app" in line
    ]
    assert agent_server and automation, lines
    assert any(PINS.sdk_fork.commit in lines[pid] for pid in agent_server)
    assert not [line for line in lines.values() if "@main" in line]
    wheel_node = cache.WebLayout(web.data / cache.WEB_DIRNAME).node.resolve()
    runs = {pid: executable(pid) for pid in descendants(web.process.pid)}
    nodes = {pid: path for pid, path in runs.items() if path and path.name == "node"}
    assert len(nodes) >= 3, nodes  # the launcher, the static server and the ingress
    assert set(nodes.values()) == {wheel_node}
    for pid in services:
        environment = environ(pid)
        held = {"PYTHONPATH", "VIRTUAL_ENV", "VITE_POSTHOG_API_KEY"} & set(environment)
        assert not held, (lines[pid], held)
        assert not [k for k, v in environment.items() if "phc_e13" in v], lines[pid]
    for pid in agent_server + automation:
        assert environ(pid).get("DO_NOT_TRACK") == "1", lines[pid]
    assert not [line for line in web.lines() if SYSTEM_NODE_MARKER in line]


def test_every_socket_the_stack_listens_on_is_loopback(first):
    """Once every service listens: the automation backend may still be installing when
    the page first answers."""
    command = first.web.process.pid
    expected = {f"127.0.0.1:{port}" for port in STACK_PORTS}
    eventually(
        lambda: expected <= set(listening_sockets([command, *descendants(command)])),
        AUTOMATION_UP_S,
    )
    listening = listening_sockets([command, *descendants(command)])
    assert [a for a in listening if not a.startswith("127.0.0.1:")] == []


def test_the_page_refuses_a_host_name_that_is_not_this_machine(first):
    """A DNS-rebound page's requests name its own host; the page carries the session key
    (TASK-64)."""
    url = f"http://127.0.0.1:{PAGE_PORT}/"
    status, body = get_with_host(url, f"rebound.example:{PAGE_PORT}")
    assert status == 403
    assert first.web.session_key not in body
    status, body = get_with_host(url, f"localhost:{PAGE_PORT}")
    assert status == 200
    assert first.web.session_key in body


def test_a_conversation_answers_and_the_key_stays_out(first, fake, chromium, tmp_path):
    web = first.web
    point_the_library_at(
        web,
        fake.base_url,
        tmp_path,
        key=KEY,
        model=E13_MODEL,
        namespace=NAMESPACE,
        decomposition=example(IMPORTED, "Triage e13."),
    )
    context = chromium.new_context()
    mark_onboarded(context)
    page = context.new_page()
    start_conversation(page, QUESTION)
    expect(answer(page, ANSWER)).to_be_visible(timeout=120_000)
    page.wait_for_timeout(CONSENT_SHOWS_S * 1000)
    expect(page.get_by_test_id("telemetry-consent-form")).to_have_count(0)
    assert {call.authorization for call in fake.calls} == {f"Bearer {KEY}"}
    [run_id] = run_ids(web)
    environment = worker_environ(web, run_id)
    worker = dict(line.split("=", 1) for line in environment.split("\0") if "=" in line)
    assert worker["OPENAI_API_KEY"] not in ("", KEY)
    stored = [
        path.read_bytes().decode(errors="replace")
        for root in (web.data / "runs", web.data / "canvas" / "agent-canvas")
        for path in root.rglob("*")
        if path.is_file() and path.name not in ("api-key.txt", "secret-key.txt")
    ]
    assert [text for text in stored if worker["OPENAI_API_KEY"] in text], (
        "the cell printed the worker's environment into the run log"
    )
    for value in (KEY, web.session_key, web.secret_key):
        assert value not in environment
        assert not [text for text in stored if value in text]
    context.close()


WEBKIT_REFUSED = pytest.mark.xfail(
    strict=True,
    reason=(
        "WebKit does not send the bridge's session cookie with the panel's frame, which "
        "the bridge refuses (401): the README names Safari as no Library panel (Q4 (a))"
    ),
)


@pytest.mark.parametrize(
    "engine", ["chromium", "firefox", pytest.param("webkit", marks=WEBKIT_REFUSED)]
)
def test_the_library_panel_works_through_the_bridge(first, playwright, engine):
    web = first.web
    browser = getattr(playwright, engine).launch()
    try:
        context = browser.new_context()
        mark_onboarded(context)
        page = context.new_page()
        page.goto(CANVAS_URL)
        expect(page.get_by_test_id("chat-input")).to_be_visible(timeout=60_000)
        frame = library_frame(page, web.session_key)
        expect(frame.get_by_test_id(f"dr-node-{NAMESPACE}")).to_be_visible(
            timeout=60_000
        )
        if engine == "chromium":
            cdp = context.new_cdp_session(page)
            cookies = cdp.send("Network.getAllCookies")["cookies"]
            [session] = [c for c in cookies if c["path"] == "/app-backends/dr-library"]
            assert session["partitionKey"]["topLevelSite"] == "http://localhost"
    finally:
        browser.close()


def test_a_second_start_is_refused_and_changes_nothing(first, tmp_path):
    web = first.web
    before = snapshot(web.data)
    log = tmp_path / "second.log"
    second = launch_web(web.home, log, first.command, env=first.env)
    code = second.process.wait(timeout=REFUSED_S)
    said = second.lines()
    assert (code, said[-1]) == (20, web_text("already_running", AGENT_SERVER_PORT))
    assert not [line for line in said if "[setup" in line or "[agent-server]" in line]
    assert snapshot(web.data) == before


def bindable(port: int) -> bool:
    """As a server binds it: a closed connection's TIME_WAIT does not hold the port."""
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True


def test_ctrl_c_stops_everything_within_10_s(first):
    web = first.web
    interrupt(web)
    assert web.process.wait(timeout=STOPPED_S) == 0
    deadline = time.monotonic() + STOPPED_S
    while processes_mentioning(str(web.home)) and time.monotonic() < deadline:
        time.sleep(0.2)
    assert processes_mentioning(str(web.home)) == []
    assert [port for port in STACK_PORTS if not bindable(port)] == []


def start_offline(
    start: FirstStart, log: Path
) -> tuple[subprocess.CompletedProcess, str]:
    done = subprocess.run(
        [
            *NETWORK_CUT,
            sys.executable,
            "-I",
            "-c",
            OFFLINE_START,
            str(log),
            *start.command,
        ],
        env=start.env,
        cwd=start.web.home,
        capture_output=True,
        text=True,
        timeout=SERVED_S * 4,
        check=False,
    )
    said = log.read_text(errors="replace") if log.exists() else ""
    return done, ANSI.sub("", said)


def served_within(done: subprocess.CompletedProcess) -> float | None:
    found = re.search(r"^served ([0-9.]+)$", done.stdout, re.MULTILINE)
    return float(found[1]) if found else None


def test_a_restart_offline_installs_nothing_and_serves_the_page_within_30_s(
    first, tmp_path
):
    done, log = start_offline(first, tmp_path / "offline.log")
    took = served_within(done)
    assert took is not None and took < SERVED_S, (done.stdout, done.stderr, log[-4000:])
    for installing in (
        "installing deep-reasoning",
        "Installing Node",
        "Fetching Deep Reasoning",
    ):
        assert installing not in log
    assert done.returncode == 0, log[-4000:]


def uvx_offline(start: FirstStart, *args: str) -> subprocess.CompletedProcess:
    """uvx inside the cut network, from the start's HOME and its uv cache."""
    return subprocess.run(
        [*NETWORK_CUT, "uvx", *args],
        env=start.env,
        cwd=start.web.home,
        capture_output=True,
        text=True,
        timeout=SERVED_S * 4,
        check=False,
    )


def test_with_index_answers_that_expire_uv_goes_to_the_network_and_offline_uv_still_runs(
    expiring,
):
    """The negative control for claim 9: where uv's index answers expire a second after
    each fetch, uvx of the automation backend the first start there installed needs the
    network, even at the PyPI cutoff, and --offline still runs it from the cache."""
    [tree] = (expiring.web.data / cache.WEB_DIRNAME).glob("tree-*")
    defaults = json.loads((tree / "package" / "config" / "defaults.json").read_text())
    package, version = (
        defaults["packages"]["automation"],
        defaults["versions"]["automation"],
    )
    # The launcher's own uvx of it, the cutoff first (dev-with-automation.mjs,
    # buildAutomationCommand).
    probe = (
        *("--exclude-newer", defaults["uv"]["excludeNewer"]),
        *("--from", f"{package}=={version}", "uvicorn", "--version"),
    )
    online_first = uvx_offline(expiring, *probe)
    assert online_first.returncode != 0, online_first.stdout
    offline = uvx_offline(expiring, "--offline", *probe)
    assert offline.returncode == 0, offline.stderr


def test_an_offline_restart_once_uvs_index_answers_have_expired(expiring, tmp_path):
    """Claim 8's restart, from the HOME whose index answers expire: the launcher starts
    both services from uv's cache, offline, which it does only with the PyPI cutoff the
    build wrote into the tarball's defaults."""
    done, log = start_offline(expiring, tmp_path / "expired.log")
    took = served_within(done)
    assert took is not None and took < SERVED_S, (done.stdout, done.stderr, log[-4000:])
    for service in ("agent-server", "automation"):
        assert f"[{service}] {STARTING_OFFLINE}" in log, log[-4000:]
    assert done.returncode == 0, log[-4000:]
