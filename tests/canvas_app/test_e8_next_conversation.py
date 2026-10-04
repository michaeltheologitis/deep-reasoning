"""E8 (spec §4; D3 §7.4), end to end below Canvas: a decomposition saved in Create
decomposition is used, at its saved version, by the next conversation in its namespace,
and the open conversation does not change."""

import json

import pytest
from playwright.async_api import async_playwright
from playwright.async_api import expect as expect_async

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from tests.acp.harness import dr_acp, run, run_ids
from tests.canvas_app.conftest import SAFETY_ACK, serve, stop, ui_url

pytestmark = pytest.mark.browser

REPLY = '<think>ok</think>\n<repl>\nFinalAnswer("done")\n</repl>'
NAME = "rank by prerequisites"
TASK = "Which of CS201, CS310 and CS330 can I take first?"
USE_WHEN = "ordering courses by what they need first"


def contents(call) -> list[str]:
    return [str(message.get("content", "")) for message in call.messages]


async def save_in_create(url: str) -> str:
    """Create decomposition in a browser, as a user does; returns the line it shows."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        await context.add_init_script(SAFETY_ACK)
        page = await context.new_page()
        await page.goto(url)
        await page.get_by_test_id("dr-name").fill(NAME)
        await page.get_by_test_id("dr-use-when").fill(USE_WHEN)
        await page.get_by_test_id("dr-card-0-task").fill(TASK)
        await page.get_by_test_id("dr-card-1-code").fill('FinalAnswer("CS201")')
        await page.get_by_test_id("dr-namespace-router").check()
        await page.get_by_test_id("dr-save").click()
        result = page.get_by_test_id("dr-result")
        await expect_async(result).to_contain_text("v1 in router", timeout=10_000)
        line = await result.inner_text()
        await browser.close()
        return line


def test_a_decomposition_saved_in_create_is_used_by_the_next_conversation_in_its_namespace(
    library_home, work
):
    async def body():
        async with FakeOpenAI(lambda messages: REPLY) as model:
            library = Library.open(library_path(library_home))
            profile = library.profile().data
            client = {**profile["client"], "base_url": model.base_url}
            library.put_profile(json.dumps({**profile, "client": client}))
            server = serve(library_home)
            try:
                async with dr_acp(None, library_home) as acp:
                    a = await acp.open_session(work)
                    await acp.ask(a, "Q1: which course comes after CS101?")
                    line = await save_in_create(
                        ui_url(
                            server.url, tab="create", namespace="router", started=True
                        )
                    )
                    asked = len(model.calls)
                    await acp.ask(a, "Q2: and after CS201?")
                    a_second = model.calls[asked:]
                    b = await acp.open_session(work)
                    menu = {c.name: c for c in acp.printer.commands[b]}
                    asked = len(model.calls)
                    await acp.ask(b, "Q3: which course comes first?")
                    b_first = model.calls[asked]
                    (b_run,) = run_ids([u for u in acp.printer.updates if u[0] == b])
                    start = acp.run_log(b_run)[0]
            finally:
                stop(server)
            return line, a_second, menu, b_first, start

    line, a_second, menu, b_first, start = run(body())
    assert line.startswith("✓ Saved 'rank by prerequisites' v1 in router.")
    assert a_second and not any(TASK in c for call in a_second for c in contents(call))
    assert menu["rank-by-prerequisites"].description == USE_WHEN
    assert start.namespace == "router"
    assert start.source["versions"]["decompositions"][NAME] == 1
    assert TASK in contents(b_first)
