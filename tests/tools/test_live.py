"""The live tier for your own tools (D4 §10.5): a tool written in the Library, through the
App backend's API and its Check, is used by a real agent on gpt-6-luna through dr-acp.

Run with `uv run pytest -m live`; skipped without OPENAI_API_KEY. Cents per run.
"""

import os
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from deep_reasoning.library import Library, library_path
from deep_reasoning.library.api import create_app
from tests.acp.harness import dr_acp, run, run_ids, scripted_env

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not set"
    ),
]

# A fact that exists only in the tool: no model can know it.
COURSE_CREDITS = '''from deep_reasoner import Func

CREDITS = {"ZQ-417": 7, "ZQ-101": 3}


def make(client, params):
    def course_credits(code: str) -> int:
        """How many credits a course is worth, by its course code."""
        return CREDITS[code.strip().upper()]

    return Func(
        course_credits,
        description="course_credits(code) -> int: the credits of a course, by its code.",
    )
'''
TOOL = {"yaml": "factory: make", "source": COURSE_CREDITS}


def test_live_a_tool_written_in_the_library_is_used_by_the_agent(
    home: Path, work: Path
):
    library = Library.open(library_path(home))  # the starter: gpt-6-luna on OpenAI
    api = TestClient(
        create_app(library, same_user=lambda c, s: True),
        base_url="http://127.0.0.1:8123",
    )
    saved = api.put(
        "/tools/course_credits",
        json=TOOL | {"granted_in": ["root"], "base_version": 0},
    )
    assert saved.status_code == 201, saved.text
    checked = api.post("/tools/course_credits/check", json=TOOL).json()
    assert checked["outcome"] == "built", checked

    async def body():
        env = scripted_env(OPENAI_API_KEY=os.environ["OPENAI_API_KEY"])
        async with dr_acp(None, home, env=env) as client:
            session = await client.open_session(work)
            response = await client.ask(session, "How many credits is course ZQ-417?")
            return client, session, response

    client, session, response = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    answer = next(
        u["content"]["text"]
        for u in reversed(client.updates_on(session))
        if u["sessionUpdate"] == "agent_message_chunk"
    )
    assert "7" in answer
    (run_id,) = run_ids(client.printer.updates)
    cells = [e for e in client.run_log(run_id) if e.kind == "cell.end"]
    assert any("course_credits(" in c.code and "7" in c.output for c in cells)
