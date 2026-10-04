"""The built page bundle, as Canvas loads it: imported from a blob: URL by a page on
another site than the frame's, which implements C2's host API over the real backend."""

import json
from importlib import resources

import pytest
from playwright.sync_api import Page, expect

from tests.canvas_app.conftest import SAFETY_ACK, write_new

pytestmark = pytest.mark.browser

BUNDLE = resources.files("deep_reasoning.canvas_app").joinpath("dist", "index.js")
# C2's host (C2 §7, A.1, A.11) over a fake agent-server: the backend is ready, conversation
# c1 has started in router, c2 has not started in course_advisor, and the profile caps
# spend at $7. The events search answers as the SDK fork's at dr-1 does: its kind is the
# module-qualified class name, and TIMESTAMP_DESC with limit 1 is the newest match
# (S2 §3.2 B2). mountFrame appends the frame at the backend's address, as C2's does at the
# ingress; selectTab disposes the tab's page and mounts the next one, as C2's panel does.
PARENT = """<!doctype html>
<meta charset="utf-8">
<style>
  :root { --oh-surface: rgb(1, 2, 3); --oh-radius: 3px; color-scheme: dark; }
</style>
<div id="panel" style="width: 600px; height: 700px"></div>
<script type="module">
  const BACKEND = %(backend)s;
  const CONTROLS_KIND = "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";
  const ALL = ["root", "router", "course_advisor"];
  const controls = (namespace, values) => ({
    kind: "ACPSessionControlsEvent",
    available_commands: [],
    config_options: [{
      id: "namespace", name: "Namespace", type: "select", current_value: namespace,
      options: values.map((value) => ({ value, name: value })),
    }],
  });
  // Each conversation's controls events, oldest first.
  const EVENTS = {
    c1: [controls("router", ALL), controls("router", ["router"])],
    c2: [controls("course_advisor", ALL)],
  };
  function search(id, query) {
    const found = query.get("kind") === CONTROLS_KIND ? [...(EVENTS[id] ?? [])] : [];
    if (query.get("sort_order") === "TIMESTAMP_DESC") found.reverse();
    return { items: found.slice(0, Number(query.get("limit") ?? 100)), next_page_id: null };
  }
  function answer({ path }) {
    if (path === "/api/canvas-extensions/installed/dr-library/backend") {
      return { name: "dr-library", state: "ready", revision: "r1", prepared_revision: "r1", detail: null };
    }
    if (path === "/api/agent-profiles/deep_reasoner") {
      return { name: "deep_reasoner", profile: { acp_args: ["--spend-cap-usd", "7"] } };
    }
    const url = new URL(path, location.origin);
    return search(url.pathname.split("/")[3], url.searchParams);
  }
  const registered = new Map();
  window.selected = [];
  const host = {
    apiVersion: "1",
    registerPage(id, mount) {
      registered.set(id, mount);
      return () => registered.delete(id);
    },
    agentServer: { request: async (request) => answer(request) },
    appBackend: {
      mountFrame(container, { path, title }) {
        const frame = document.createElement("iframe");
        frame.src = `${BACKEND}/${path.replace(/^\\//, "")}`;
        frame.title = title;
        frame.setAttribute("sandbox", "allow-forms allow-modals allow-popups allow-same-origin allow-scripts");
        frame.referrerPolicy = "no-referrer";
        frame.style.cssText = "width: 100%%; height: 100%%; border: 0";
        container.append(frame);
        return () => frame.remove();
      },
    },
  };
  let dispose = null;
  window.mountTab = async (tab, conversationId) => {
    dispose?.();
    const container = document.getElementById("panel");
    container.replaceChildren();
    const surface = {
      kind: "conversation-panel",
      panelId: "decompositions",
      tabId: tab,
      selectTab: (next) => {
        window.selected.push(next);
        window.mountTab(next, conversationId);
      },
    };
    dispose = await registered.get(tab)({ container, path: tab, navigate() {}, conversationId, surface });
  };
  const text = await (await fetch("index.js")).text();
  const app = await import(URL.createObjectURL(new Blob([text], { type: "text/javascript" })));
  app.activate(host);
  window.registered = [...registered.keys()];
</script>
"""


@pytest.fixture
def canvas(browser, library_server, parent_site):
    """Canvas's page with the App activated; the frames it mounts acknowledge the notice."""
    origin = parent_site(
        {
            "parent.html": PARENT % {"backend": json.dumps(library_server.url)},
            "index.js": BUNDLE.read_text(),
        }
    )
    context = browser.new_context()
    context.add_init_script(SAFETY_ACK)
    page = context.new_page()
    page.goto(f"{origin}/parent.html")
    page.wait_for_function("window.registered !== undefined")
    yield page
    context.close()


def mount(page: Page, tab: str, conversation: str) -> None:
    page.evaluate("([tab, id]) => window.mountTab(tab, id)", [tab, conversation])


def test_the_frame_opens_with_the_conversations_namespace(canvas):
    mount(canvas, "create", "c2")
    frame = canvas.frame_locator("#panel iframe")
    expect(frame.get_by_test_id("dr-namespace-course_advisor")).to_be_checked()
    mount(canvas, "create", "c1")
    expect(frame.get_by_test_id("dr-namespace-router")).to_be_checked()
    src = canvas.locator("#panel iframe").get_attribute("src")
    assert "namespace=router" in src and "started=1" in src and "cap=7" in src


def test_show_in_decompositions_selects_the_tab_and_opens_the_new_entry(
    canvas, library_server
):
    mount(canvas, "create", "c1")
    frame = canvas.frame_locator("#panel iframe")
    write_new(frame, "rank by prerequisites", "Which of CS201 and CS310 comes first?")
    frame.get_by_test_id("dr-save").click()
    expect(frame.get_by_test_id("dr-result")).to_contain_text("v1 in router")
    frame.get_by_test_id("dr-show-in-decompositions").click()
    expect(frame.get_by_test_id("dr-name")).to_have_value("rank by prerequisites")
    assert canvas.evaluate("window.selected") == ["browse"]
    assert "tab=browse" in canvas.locator("#panel iframe").get_attribute("src")
    assert library_server.library().decomposition("rank by prerequisites").version == 1


def test_the_frame_takes_canvas_theme(canvas):
    mount(canvas, "browse", "c1")
    frame = canvas.frame_locator("#panel iframe")
    expect(frame.get_by_test_id("dr-group-router")).to_be_visible()
    read = "getComputedStyle(document.documentElement).getPropertyValue('--oh-surface')"
    theirs = canvas.locator("#panel").evaluate(
        "(panel) => getComputedStyle(panel).getPropertyValue('--oh-surface')"
    )
    ours = frame.locator(":root").evaluate(f"() => {read}")
    assert ours.strip() == theirs.strip() == "rgb(1, 2, 3)"
    background = frame.locator("body").evaluate(
        "(body) => getComputedStyle(body).backgroundColor"
    )
    assert background == "rgb(1, 2, 3)"
