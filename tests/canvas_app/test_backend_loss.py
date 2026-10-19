import pytest
from playwright.sync_api import expect

from tests.canvas_app.conftest import stop

pytestmark = pytest.mark.browser


def test_a_backend_that_stops_answering_offers_restart(open_framed_ui, library_server):
    page, frame = open_framed_ui(tab="browse")
    expect(frame.get_by_test_id("dr-group-router")).to_be_visible()
    stop(library_server)
    expect(frame.get_by_test_id("dr-backend-lost")).to_contain_text(
        "The Library stopped answering (0)."
    )
    frame.get_by_test_id("dr-restart").click()
    page.wait_for_function("window.received.length > 0")
    assert page.evaluate("window.received") == [{"type": "dr-library/reload"}]
