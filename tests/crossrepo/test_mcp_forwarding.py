"""D4's forwarding across the repositories (D4 §10.6, D5 §8.7): an MCP server in the
SDK fork's agent-server settings reaches dr-acp through the deep_reasoner profile setup
writes and the ACP bridge, with its secret, and the Library's grant binds it for a
cell."""

import secrets
import sys
import time
from pathlib import Path

import pytest

from deep_reasoning.acp.runlog import CellEnd, Home, McpStatus, RunLog
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from dr_app.profile import PROFILE_NAME, desired_profile
from tests.acp.scenarios import BASE_CONFIG, repl, scripted
from tests.crossrepo.agent_server import agent_server, sdk_checkout
from tests.library.conftest import write_config
from tests.mcp.conftest import put_grant
from tests.mcp.test_acp import SERVERS

QUESTION = "Ask the echo server for its token."
PLAN = {QUESTION: [repl("print(echo.token())"), repl("FinalAnswer('asked')")]}
TIMEOUT_S = 120.0


@pytest.mark.crossrepo
def test_an_mcp_server_in_the_agent_servers_settings_reaches_a_cell_with_its_secret(
    tmp_path, home
):
    token = f"echo-{secrets.token_hex(16)}"
    work = tmp_path / "work"
    work.mkdir()
    with (
        FakeOpenAI(scripted(PLAN)) as model,
        agent_server(sdk_checkout(), tmp_path / "agent-server") as server,
    ):
        library = Library.open(library_path(home), starter=False)
        client = {**BASE_CONFIG["client"], "base_url": model.base_url}
        library.import_config(
            write_config(tmp_path / "config", BASE_CONFIG | {"client": client})
        )
        put_grant(
            library,
            "echo",
            ["root"],
            command=sys.executable,
            args=[str(SERVERS / "echo_server.py")],
            env=["ECHO_TOKEN"],
        )
        server.request(
            "POST",
            "/api/settings/mcp/echo",
            {
                "command": sys.executable,
                "args": [str(SERVERS / "echo_server.py")],
                "env": {"ECHO_TOKEN": token},
            },
        )
        dr_acp = Path(sys.executable).parent / "dr-acp"
        profile = desired_profile(None, dr_acp=dr_acp, home=home)
        server.request("POST", f"/api/agent-profiles/{PROFILE_NAME}", profile)
        saved = server.request("GET", f"/api/agent-profiles/{PROFILE_NAME}")["profile"]
        conversation = server.request(
            "POST",
            "/api/conversations",
            {
                "agent_profile_id": saved["id"],
                "workspace": {"kind": "LocalWorkspace", "working_dir": str(work)},
            },
        )["id"]
        server.ask(conversation, QUESTION, time.monotonic() + TIMEOUT_S)
    [run_id] = [path.name for path in (home / "runs").iterdir()]
    events = list(RunLog.read(Home(home), run_id))
    [status] = [e for e in events if isinstance(e, McpStatus)]
    assert [(s.tool, s.server, s.state) for s in status.servers] == [
        ("echo", "echo", "bound")
    ]
    [cell, _] = [e for e in events if isinstance(e, CellEnd)]
    assert cell.output.strip() == token
