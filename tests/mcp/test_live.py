"""The live tier for MCP servers (D4 §10.5): a server of our own, granted to the
conversation's namespace through the App backend's API and forwarded as Canvas's bridge
forwards it, is used by a real agent on gpt-6-luna through dr-acp, and its secret goes
nowhere it should not.

Run with `uv run pytest -m live`; skipped without OPENAI_API_KEY. Cents per run.
"""

import os
import secrets
import sys
from pathlib import Path

import acp.schema
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

CATALOG = Path(__file__).parent / "servers" / "catalog_server.py"
# The task names the server: the test pins that a granted server is bound and works
# when called, not that the model chooses to call it (asked bare, it may guess).
TASK = "Use the catalog server to find what a student must finish before ZQ-417."


def test_live_an_mcp_server_granted_to_the_namespace_is_used_by_the_agent(
    home: Path, work: Path
):
    token = f"catalog-{secrets.token_hex(12)}"
    library = Library.open(library_path(home))  # the starter: gpt-6-luna on OpenAI
    api = TestClient(
        create_app(library, same_user=lambda c, s: True),
        base_url="http://127.0.0.1:8123",
    )
    granted = api.put(
        "/mcp/catalog",
        json={
            "server": "catalog",
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(CATALOG)],
            "env": ["CATALOG_TOKEN"],
            "granted_in": ["root"],
            "base_version": 0,
        },
    )
    assert granted.status_code == 201, granted.text
    forwarded = acp.schema.McpServerStdio(
        name="catalog",
        command=sys.executable,
        args=[str(CATALOG)],
        env=[acp.schema.EnvVariable(name="CATALOG_TOKEN", value=token)],
    )

    async def body():
        env = scripted_env(OPENAI_API_KEY=os.environ["OPENAI_API_KEY"])
        async with dr_acp(None, home, env=env) as client:
            session = await client.open_session(work, [forwarded])
            response = await client.ask(session, TASK)
            return client, session, response

    client, session, response = run(body())
    # Beside the runs, for the live job's artifact when this test fails.
    (home / "transcript.jsonl").write_bytes(b"".join(client.lines))
    (run_id,) = run_ids(client.printer.updates)
    log = client.run_log(run_id)
    ends = (e for e in log if e.kind in ("mcp.status", "agent.end", "prompt.end"))
    ended = "\n".join(map(str, ends))
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered", ended
    answer = next(
        u["content"]["text"]
        for u in reversed(client.updates_on(session))
        if u["sessionUpdate"] == "agent_message_chunk"
    )
    assert "ZQ-101" in answer
    [status] = [e for e in log if e.kind == "mcp.status"]
    assert [(s.tool, s.state) for s in status.servers] == [("catalog", "bound")]
    assert any("catalog.prerequisites(" in e.code for e in log if e.kind == "cell.end")
    assert token not in (home / "runs" / run_id / "events.jsonl").read_text()
    assert token not in b"".join(client.lines).decode()
