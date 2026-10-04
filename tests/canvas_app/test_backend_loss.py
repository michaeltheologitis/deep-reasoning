from urllib.parse import quote

import pytest
from playwright.sync_api import expect

from tests.canvas_app.conftest import SAFETY_ACK, stop

pytestmark = pytest.mark.browser

# Canvas's page, reduced to what the frame talks to: it frames the UI and records the
# messages the frame posts to it.
PARENT = """<!doctype html>
<meta charset="utf-8">
<iframe id="frame" style="width: 600px; height: 600px"></iframe>
<script>
  window.received = [];
  window.addEventListener("message", (event) => window.received.push(event.data));
  const frame = document.getElementById("frame");
  frame.src = new URLSearchParams(location.search).get("frame");
</script>
"""


def test_a_backend_that_stops_answering_offers_restart(
    browser, library_server, parent_site
):
    origin = parent_site({"parent.html": PARENT})
    frame_url = f"{library_server.url}/ui/?tab=browse&parent={origin}"
    context = browser.new_context()
    context.add_init_script(SAFETY_ACK)
    page = context.new_page()
    page.goto(f"{origin}/parent.html?frame={quote(frame_url, safe='')}")
    frame = page.frame_locator("#frame")
    expect(frame.get_by_test_id("dr-group-router")).to_be_visible()
    stop(library_server)
    expect(frame.get_by_test_id("dr-backend-lost")).to_contain_text(
        "The Library stopped answering (0)."
    )
    frame.get_by_test_id("dr-restart").click()
    page.wait_for_function("window.received.length > 0")
    assert page.evaluate("window.received") == [{"type": "dr-library/reload"}]
    context.close()
