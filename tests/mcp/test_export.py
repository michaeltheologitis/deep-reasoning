"""Under plain dr, an export's MCP grant connects by itself from its snapshot (D4 §4.8)."""

import asyncio
import subprocess
import sys
from pathlib import Path

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path, shapes
from deep_reasoning.mcp.grants import McpGrantBody, mcp_block, shim_source
from tests.acp.scenarios import repl, scripted
from tests.library.conftest import ROUTER, run_dr, write_config

ECHO = Path(__file__).parent / "servers" / "echo_server.py"
DR_LIBRARY = Path(sys.executable).parent / "dr-library"


def export_with_a_grant(home: Path, base_url: str, tmp: Path) -> Path:
    """dr-library export of a Library granting echo_server.py to router."""
    lib = Library.open(library_path(home), starter=False)
    config = {**ROUTER, "client": {**ROUTER["client"], "base_url": base_url}}
    lib.import_config(write_config(tmp / "router", config))
    body = McpGrantBody(
        server="echo",
        transport="stdio",
        command=sys.executable,
        args=[str(ECHO)],
        env=["ECHO_TOKEN"],
        granted_in=["router"],
        base_version=0,
    )
    lib.put_tool(
        "echo",
        shapes.canonical_yaml(mcp_block("echo", body)),
        source=shim_source(),
        granted_in=["router"],
    )
    export = tmp / "export"
    subprocess.run(
        [str(DR_LIBRARY), "export", str(export), "--home", str(home)],
        check=True,
        capture_output=True,
    )
    return export


def test_an_exported_grant_runs_under_dr(tmp_path):
    plan = {
        "Say hi": [repl("print(echo.echo('hi'))"), repl("FinalAnswer(echo.token())")]
    }

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            export = export_with_a_grant(tmp_path / "home", model.base_url, tmp_path)
            done = await asyncio.to_thread(
                run_dr,
                export / "main.yaml",
                "Say hi through echo.",
                cwd=tmp_path,
                env={"ECHO_TOKEN": "tok-from-the-environment"},
            )
            return done, model.calls

    done, calls = asyncio.run(body())
    assert done.returncode == 0, done.stderr[-2000:]
    assert done.stdout.strip().splitlines()[-1] == "tok-from-the-environment"
    assert calls[1].messages[-1]["content"].startswith("<observation>\nhi\n")
