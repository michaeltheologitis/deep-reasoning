import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from deep_reasoning.library import shapes
from deep_reasoning.mcp.grants import McpGrantBody, is_mcp_tool, mcp_block, shim_source
from deep_reasoning.mcp.wire import McpServerStatus, remember_seen
from tests.canvas_app.test_notice import SAFETY_5

# D4's sentences, as the frame shows them (D4 §9.3).
TOOLS_RISK = (
    "Tools and MCP servers run as you, with your files and network: your tools inside the "
    "agent's process, a stdio MCP server as a program started for each conversation that "
    "can use it. Check runs your code too. Add only code and servers you trust."
)
CANNOT_SAVE = (
    "Fix this before saving: a tool that does not build stops every conversation from "
    "starting."
)
SAVE_ANYWAY_NOTE = (
    "Check could not build this tool here, where it has no secrets, no model and only its "
    "own folder. If it builds in a conversation, save it anyway; if it does not, no "
    "conversation will start until you fix it."
)
MCP_NOT_SEEN = "Its tools are listed here after the first conversation that starts it."
MCP_DISABLED = (
    "Disabled in Canvas's MCP settings: not started until you enable it there."
)
MCP_GONE = "Granted, but no longer in Canvas's MCP settings."
MCP_CHANGED = (
    "Canvas's settings for this server changed since it was granted; an export still has "
    "the old ones."
)
MCP_SETTINGS_UNKNOWN = (
    "Canvas's MCP settings could not be read; showing the servers already granted."
)

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


# ── D4: your own tools and MCP servers (D4 §2, §10.4) ─────────────────────────────

TOOL_FIXTURES = Path(__file__).parents[1] / "tools" / "fixtures"
SHOUT = '''from deep_reasoner import Func


def make(client, params):
    def shout(text: str) -> str:
        """Say it louder."""
        return text.upper()

    return Func(shout, description="shout(text) -> str: the text in capitals.")
'''
GITHUB = {
    "name": "github",
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "url": None,
    "env": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "headers": [],
    "forwarded": True,
    "why_not": None,
}
CHECK_S = 30_000  # a Check starts deep_reasoner in a process of its own


def fixture_source(name: str) -> str:
    return (TOOL_FIXTURES / f"{name}.py").read_text()


def mcp_param(*servers: dict) -> str:
    return json.dumps(list(servers))


def set_source(page: Page, text: str) -> None:
    """Replace the editor's whole text, as a paste would (no auto-indent)."""
    page.get_by_test_id("dr-tool-source").locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.insert_text(text)


def new_tool(page: Page, name: str, source: str, block: str = "factory: make") -> None:
    page.get_by_test_id("dr-tool-new").click()
    page.get_by_test_id("dr-tool-name").fill(name)
    page.get_by_test_id("dr-tool-yaml").fill(block)
    set_source(page, source)


def stored_when(read, done, timeout_s: float = 10):
    """What read() returns once done(it) holds: a save the page made has landed."""
    deadline = time.monotonic() + timeout_s
    while not done(found := read()) and time.monotonic() < deadline:
        time.sleep(0.1)
    return found


def grant(library, name: str, granted_in: list[str], **fields) -> None:
    """An MCP grant as PUT /mcp writes it."""
    body = McpGrantBody(
        **{
            "server": name,
            "transport": "stdio",
            "command": "npx",
            "granted_in": granted_in,
            "base_version": 0,
        }
        | fields
    )
    library.put_tool(
        name,
        shapes.canonical_yaml(mcp_block(name, body)),
        source=shim_source(),
        granted_in=granted_in,
    )


def test_the_risk_line_is_under_the_safety_banner(open_ui):
    page = open_ui(tab="tools")
    risk = page.get_by_test_id("dr-tools-risk")
    expect(risk).to_have_text("⚠ " + TOOLS_RISK)
    follows = page.evaluate(
        "() => document.querySelector('[data-testid=dr-notice]')"
        ".compareDocumentPosition(document.querySelector('[data-testid=dr-tools-risk]'))"
    )
    assert follows & 4, "the risk line comes after the safety banner"


def test_a_new_tool_is_written_checked_and_saved_with_its_grants(
    open_ui, library_server
):
    page = open_ui(tab="tools")
    new_tool(page, "shout", SHOUT)
    page.get_by_test_id("dr-tool-grant-router").check()
    page.get_by_test_id("dr-tool-save").click()
    expect(page.get_by_test_id("dr-tool-result")).to_have_text(
        "✓ Saved 'shout' v1. New conversations build it; conversations already started "
        "keep the version they began with.",
        timeout=CHECK_S,
    )
    stored = library_server.library().tool("shout")
    assert (stored.source, stored.granted_in, stored.data) == (
        SHOUT,
        ["router"],
        {"factory": "make", "factory_from": "tools/shout.py"},
    )


def test_check_shows_what_the_agent_is_told_and_the_tried_value(open_ui):
    page = open_ui(tab="tools")
    page.get_by_test_id("dr-tool-new").click()
    page.get_by_test_id("dr-tool-name").fill("counter")
    page.get_by_test_id("dr-tool-example").fill('counter("one two three")')
    page.get_by_test_id("dr-check").click()
    result = page.get_by_test_id("dr-check-result")
    expect(result).to_contain_text("✓ builds (", timeout=CHECK_S)
    expect(page.get_by_test_id("dr-check-told")).to_have_text(
        "- `word_count(text: str) -> int`\n"
        "  word_count(text) -> int: number of words in text."
    )
    expect(page.get_by_test_id("dr-check-example")).to_have_text(
        'counter("one two three") → 3'
    )


@pytest.mark.parametrize(
    ("fixture", "block", "said"),
    [
        ("not_func", "factory: make", "returned function, not a Func."),
        ("word_count", "factory: mkae", "defines no 'mkae'."),
        ("import_error", "factory: make", "No module named 'yaml_x'"),
    ],
    ids=["not_func", "misspelled", "import_error"],
)
def test_a_tool_that_cannot_build_shows_why_and_cannot_be_saved(
    open_ui, library_server, fixture, block, said
):
    page = open_ui(tab="tools")
    new_tool(page, "broken", fixture_source(fixture), block)
    page.get_by_test_id("dr-tool-save").click()
    result = page.get_by_test_id("dr-check-result")
    expect(result).to_contain_text(said, timeout=CHECK_S)
    expect(result).to_contain_text(CANNOT_SAVE)
    expect(page.get_by_test_id("dr-tool-save-anyway")).to_have_count(0)
    assert "broken" not in library_server.library().state().tools


def test_a_hanging_factory_shows_the_limit(open_ui):
    page = open_ui(tab="tools")
    new_tool(page, "slow", fixture_source("hang"))
    page.get_by_test_id("dr-check").click()
    expect(page.get_by_test_id("dr-check-status")).to_have_text(
        "Checking… (building your tool in a separate process)"
    )
    result = page.get_by_test_id("dr-check-result")
    expect(result).to_contain_text(
        "✗ tool 'slow': building it took longer than 10 s, so Check stopped it.",
        timeout=CHECK_S + 10_000,
    )
    expect(page.get_by_test_id("dr-tool-save-anyway")).to_be_visible()


def test_a_raising_factory_offers_save_anyway(open_ui, library_server):
    page = open_ui(tab="tools")
    new_tool(page, "token", fixture_source("env_at_build"))
    page.get_by_test_id("dr-tool-save").click()
    result = page.get_by_test_id("dr-check-result")
    expect(result).to_contain_text(
        "✗ tool 'token': make raised KeyError: 'D4_TOKEN'", timeout=CHECK_S
    )
    expect(result).to_contain_text(SAVE_ANYWAY_NOTE)
    assert "token" not in library_server.library().state().tools
    page.get_by_test_id("dr-tool-save-anyway").click()
    expect(page.get_by_test_id("dr-tool-result")).to_contain_text(
        "✓ Saved 'token' v1.", timeout=CHECK_S
    )
    assert library_server.library().tool("token").source == fixture_source(
        "env_at_build"
    )


def test_a_grant_tick_on_a_saved_tool_saves_without_unsaved_code(
    open_ui, library_server
):
    before = library_server.library().tool("word_count")
    page = open_ui(tab="tools")
    page.get_by_test_id("dr-tool-word_count").click()
    set_source(page, "this is not saved\n")
    page.get_by_test_id("dr-tool-grant-router").check()
    expect(page.get_by_test_id("dr-tool-result")).to_contain_text(
        "✓ Saved 'word_count' v1."
    )
    after = library_server.library().tool("word_count")
    assert (after.version, after.source, after.granted_in) == (
        before.version,
        before.source,
        ["router", "course_advisor"],
    )


def test_an_inherited_grant_is_fixed(open_ui, library_server):
    library = library_server.library()
    word_count = library.tool("word_count")
    library.put_tool(
        "word_count", word_count.yaml, source=word_count.source, granted_in=["router"]
    )
    page = open_ui(tab="tools")
    page.get_by_test_id("dr-tool-word_count").click()
    archive = page.get_by_test_id("dr-tool-grant-router.archive")
    expect(archive).to_be_checked()
    expect(archive).to_be_disabled()
    expect(page.get_by_test_id("dr-tool-grant-list")).to_contain_text(
        "router.archive inherited from router"
    )
    expect(page.get_by_test_id("dr-tool-grant-router")).to_be_enabled()


def test_the_editor_keeps_python_indentation(open_ui):
    page = open_ui(tab="tools")
    page.get_by_test_id("dr-tool-new").click()
    page.get_by_test_id("dr-tool-source").locator(".cm-content").click()
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.press("Backspace")
    page.keyboard.type("def make(client, params):")
    page.keyboard.press("Enter")
    page.keyboard.type("return None")
    page.keyboard.press("Enter")
    page.keyboard.press("Tab")
    page.keyboard.type("x")
    draft = page.evaluate(
        "() => JSON.parse(localStorage.getItem('dr-library.draft.tool.new')).source"
    )
    assert draft == "def make(client, params):\n    return None\n        x"


def test_canvas_mcp_servers_are_listed_and_granted_per_namespace(
    open_ui, library_server
):
    page = open_ui(tab="tools", mcp=mcp_param(GITHUB))
    row = page.get_by_test_id("dr-mcp-github")
    expect(row).to_contain_text("npx -y @modelcontextprotocol/server-github")
    expect(page.get_by_test_id("dr-mcp-name-github")).to_have_value("github")
    page.get_by_test_id("dr-mcp-grant-github-router").check()
    expect(row).to_contain_text("as github")
    expect(page.get_by_test_id("dr-mcp-seen-github")).to_have_text(MCP_NOT_SEEN)
    page.get_by_test_id("dr-mcp-grant-github-course_advisor").check()
    stored = stored_when(
        lambda: library_server.library().tool("github"),
        lambda t: t.granted_in == ["router", "course_advisor"],
    )
    assert is_mcp_tool(stored)
    assert stored.version == 1
    assert stored.data["env"] == ["GITHUB_PERSONAL_ACCESS_TOKEN"]
    expect(page.get_by_test_id("dr-tool-github")).to_have_count(0)


def test_a_disabled_server_says_so_and_can_still_be_granted(open_ui, library_server):
    slack = GITHUB | {"name": "slack", "forwarded": False, "why_not": "disabled"}
    page = open_ui(tab="tools", mcp=mcp_param(slack))
    expect(page.get_by_test_id("dr-mcp-state-slack")).to_have_text(MCP_DISABLED)
    page.get_by_test_id("dr-mcp-grant-slack-router").check()
    expect(page.get_by_test_id("dr-mcp-slack")).to_contain_text("as slack")
    assert library_server.library().tool("slack").granted_in == ["router"]


def test_a_grant_gone_from_canvas_offers_remove(open_ui, library_server):
    grant(library_server.library(), "old_wiki", ["router"], server="old-wiki")
    page = open_ui(tab="tools", mcp=mcp_param(GITHUB))
    expect(page.get_by_test_id("dr-mcp-state-old-wiki")).to_contain_text(MCP_GONE)
    page.get_by_test_id("dr-mcp-remove-old-wiki").click()
    expect(page.get_by_test_id("dr-mcp-old-wiki")).to_have_count(0)
    assert "old_wiki" not in library_server.library().state().tools


def test_a_changed_server_offers_update(open_ui, library_server):
    grant(library_server.library(), "github", ["router"], env=["OLD_TOKEN"])
    page = open_ui(tab="tools", mcp=mcp_param(GITHUB))
    expect(page.get_by_test_id("dr-mcp-state-github")).to_contain_text(MCP_CHANGED)
    page.get_by_test_id("dr-mcp-update-github").click()
    expect(page.get_by_test_id("dr-mcp-state-github")).to_have_count(0)
    stored = library_server.library().tool("github")
    assert (stored.version, stored.data["env"], stored.granted_in) == (
        2,
        ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        ["router"],
    )


def test_the_last_seen_tools_are_shown(open_ui, library_server):
    grant(library_server.library(), "github", ["router"])
    told = "- `github(tool, /, **arguments)`\n  MCP server 'github' (stdio): …"
    bound = McpServerStatus(
        tool="github",
        server="github",
        transport="stdio",
        state="bound",
        count=12,
        told=told,
    )
    remember_seen(library_server.home, "run-1", [bound], datetime.now(UTC))
    page = open_ui(tab="tools", mcp=mcp_param(GITHUB))
    seen = page.get_by_test_id("dr-mcp-seen-github")
    expect(seen).to_contain_text("12 tools, as the conversation of")
    seen.locator("summary").click()
    expect(seen.locator("pre")).to_have_text(told)


def test_without_canvas_settings_only_grants_are_shown(open_ui, library_server):
    grant(library_server.library(), "github", ["router"])
    page = open_ui(tab="tools")
    expect(page.get_by_test_id("dr-mcp-unknown")).to_have_text(MCP_SETTINGS_UNKNOWN)
    expect(page.get_by_test_id("dr-mcp-github")).to_contain_text("as github")
    expect(page.locator("[data-testid^=dr-mcp-name-]")).to_have_count(0)
