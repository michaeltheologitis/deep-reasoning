"""E10: provider keys reach the worker only as tokens, and a conversation's spend stops at
its cap, through a real dr-acp over stdio (D5 §2.1, §7.1); and again with D4's MCP server
bound (D5 §8.7)."""

import base64
import json
import secrets
import sys
from pathlib import Path

import pytest

from deep_reasoning.acp.runlog import McpStatus, PromptEnd, RunEnd, WorkerReady
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import Library, library_path
from tests.acp.harness import (
    dr_acp,
    run,
    run_ids,
    scripted_env,
    write_config,
)
from tests.acp.scenarios import repl, scripted
from tests.mcp.conftest import put_grant
from tests.mcp.test_acp import SERVERS, forwarded

E10_MODEL = "e10-model"
# Input $1 and output $2 per million tokens: FakeOpenAI's usage below costs $0.004.
E10_PRICES = {
    E10_MODEL: {"input_per_mtok": 1.0, "output_per_mtok": 2.0, "context_window": 200000}
}
CALL_USAGE = {"prompt_tokens": 2000, "completion_tokens": 1000, "total_tokens": 3000}
CALL_USD = 0.004
CAP_USD = 0.01
ENVIRONMENT_CELL = repl(
    "import os, subprocess",
    "rag.add([{'id': 'e10', 'text': 'keys stay with dr-acp'}])",
    "print(dict(os.environ))",
    "print(open('/proc/self/environ', 'rb').read())",
    "print(subprocess.run(['env'], capture_output=True, text=True).stdout)",
)
PLAN = {
    "Show me your environment.": [ENVIRONMENT_CELL, repl("FinalAnswer('shown')")],
    "Keep working.": [repl("print('still working')")],
}

linux_only = pytest.mark.skipif(
    sys.platform != "linux", reason="reads /proc/<pid>/environ"
)


def e10_config(directory: Path, base_url: str, **extra: object) -> Path:
    client = {"base_url": base_url, "api_key_env": "OPENAI_API_KEY", "max_retries": 0}
    return write_config(
        directory / "e10.yaml",
        {
            "model": E10_MODEL,
            "client": client,
            "system_prompt": "You are a scripted test agent.",
            "max_iter": 6,
            "max_depth": 2,
            "entry_namespace": "root",
            "namespaces": {"root": {"tools": ["rag"]}},
            "tools": {
                "rag": {
                    "embed_model": "e10-embed",
                    "client": {"base_url": base_url, "api_key_env": "OPENAI_API_KEY"},
                }
            },
            **extra,
        },
    )


def secret(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(16)}"


def forms(value: str) -> list[str]:
    """The value and its base64."""
    return [value, base64.b64encode(value.encode()).decode()]


@linux_only
def test_provider_keys_and_agent_server_secrets_never_reach_the_worker_a_cell_the_transcript_or_the_run_log(
    tmp_path, home, work
):
    key = secret("sk-e10-")
    secrets_ = {
        "OPENAI_API_KEY": key,
        "MY_KEY_COPY": key,
        "ANTHROPIC_API_KEY": secret("sk-ant-e10-"),
        "OH_SECRET_KEY": secret("oh-"),
        "OH_SESSION_API_KEYS_0": secret("session-"),
        "SESSION_API_KEY": secret("session-"),
        "OPENHANDS_AUTOMATION_API_KEY": secret("automation-"),
    }

    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = e10_config(tmp_path / "config", model.base_url)
            env = scripted_env(**secrets_)
            async with dr_acp(config, home, env=env, prices=E10_PRICES) as client:
                root = await client.open_session(work)
                response = await client.ask(root, "Show me your environment.")
                (run_id,) = run_ids(client.printer.updates)
                [ready] = [
                    e for e in client.run_log(run_id) if isinstance(e, WorkerReady)
                ]
                environ = Path(f"/proc/{ready.pid}/environ").read_bytes()
                updates = json.dumps(client.printer.updates)
                outputs = [
                    u["rawOutput"]
                    for u in client.updates_on(root)
                    if u["sessionUpdate"] == "tool_call_update" and u.get("rawOutput")
                ]
        return response, environ, updates, outputs, model

    response, environ, updates, outputs, model = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    worker = dict(
        line.split("=", 1) for line in environ.decode().split("\0") if "=" in line
    )
    assert "PYTHONUNBUFFERED" in worker
    assert worker["OPENAI_API_KEY"] != key
    assert len(worker["OPENAI_API_KEY"]) >= 40
    assert "MY_KEY_COPY" not in worker
    cell = "\n".join(outputs)
    assert worker["OPENAI_API_KEY"] in cell, "the cell printed its environment"
    files = {
        str(path): path.read_bytes().decode(errors="replace")
        for path in home.rglob("*")
        if path.is_file()
    }
    assert any(name.endswith("events.jsonl") for name in files)
    assert any(name.endswith("worker.log") for name in files)
    for name, value in secrets_.items():
        for form in forms(value):
            assert form not in environ.decode(errors="replace"), name
            assert form not in cell, name
            assert form not in updates, name
            for path, text in files.items():
                assert form not in text, (name, path)
    assert model.calls, "the main client called the model"
    assert model.embed_calls, "the tool's own client called the model"
    assert {c.authorization for c in (*model.calls, *model.embed_calls)} == {
        f"Bearer {key}"
    }


def test_a_call_past_the_spend_cap_is_refused_and_never_forwarded(tmp_path, home, work):
    key = secret("sk-e10-")
    args = ("--spend-cap-usd", str(CAP_USD))
    env = scripted_env(OPENAI_API_KEY=key)

    async def body():
        async with FakeOpenAI(
            scripted(PLAN), usage=lambda messages, reply: CALL_USAGE
        ) as model:
            config = e10_config(
                tmp_path / "config",
                model.base_url,
                max_iter=50,
                llm_kwargs={"max_tokens": 1000},
            )
            async with dr_acp(
                config, home, args=args, env=env, prices=E10_PRICES
            ) as client:
                root = await client.open_session(work)
                first = await client.ask(root, "Keep working.")
                forwarded = len(model.calls)
                again = await client.ask(root, "Keep working.")
                after_again = len(model.calls)
                runs = run_ids(client.printer.updates)
                ends = [
                    [e for e in client.run_log(r) if isinstance(e, (PromptEnd, RunEnd))]
                    for r in runs
                ]
                said = [
                    u["content"]["text"]
                    for u in client.updates_on(root)
                    if u["sessionUpdate"] == "agent_message_chunk"
                ]
            async with dr_acp(
                config, home, args=args, env=env, prices=E10_PRICES
            ) as reloaded:
                await reloaded.conn.load_session(
                    cwd=str(work), session_id=root, mcp_servers=[]
                )
                reloaded_answer = await reloaded.ask(root, "Keep working.")
        answers = (first, again, reloaded_answer)
        return answers, forwarded, after_again, ends, said, model

    answers, forwarded, after_again, ends, said, model = run(body())
    spend = json.loads(next((home / "spend").glob("*.json")).read_text())
    assert [a.field_meta["deep_reasoner"]["outcome"] for a in answers] == ["failed"] * 3
    for prompt_end, run_end in ends:
        assert (prompt_end.outcome, run_end.reason) == ("failed", "failed")
        assert "The key proxy refused this model call" in prompt_end.detail
    assert [text for text in said if "The key proxy refused this model call" in text]
    assert forwarded == spend["calls"] >= 1
    assert after_again == forwarded, "nothing forwarded once the cap was reached"
    assert len(model.calls) == forwarded, "nor after dr-acp restarted"
    assert spend["spent_usd"] <= CAP_USD + CALL_USD
    assert spend["refused"] >= 3
    assert {c.authorization for c in model.calls} == {f"Bearer {key}"}


# What every stdio server gets on top of its settings: mcp's six, and LC_CTYPE, which D4's
# guard (a Python) adds when it coerces a C locale (PEP 538).
MCP_INHERITED = {"HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER", "LC_CTYPE"}
MCP_PLAN = {
    "Call the echo server.": [
        repl("print(echo.env_names())"),
        repl("FinalAnswer('called')"),
    ]
}


def environ_of(pid: int | str) -> dict[str, str]:
    raw = Path(f"/proc/{pid}/environ").read_bytes().decode(errors="replace")
    return dict(line.split("=", 1) for line in raw.split("\0") if "=" in line)


@linux_only
@pytest.mark.parametrize("named", [False, True], ids=["unnamed", "named"])
def test_an_mcp_server_gets_a_provider_key_only_when_its_settings_name_it_and_the_worker_never_does(
    tmp_path, home, work, named
):
    key = secret("sk-e10-")
    secrets_ = {
        "OPENAI_API_KEY": key,
        "OH_SECRET_KEY": secret("oh-"),
        "SESSION_API_KEY": secret("session-"),
        "OPENHANDS_AUTOMATION_API_KEY": secret("automation-"),
    }
    markers = tmp_path / "markers"
    markers.mkdir()
    settings = {"ECHO_TOKEN": secret("echo-"), "ECHO_MARKER_DIR": str(markers)}
    if named:
        settings["OPENAI_API_KEY"] = key

    async def body():
        async with FakeOpenAI(scripted(MCP_PLAN)) as model:
            library = Library.open(library_path(home), starter=False)
            library.import_config(e10_config(tmp_path / "config", model.base_url))
            put_grant(
                library,
                "echo",
                ["root"],
                command=sys.executable,
                args=[str(SERVERS / "echo_server.py")],
                env=sorted(settings),
            )
            env = scripted_env(**secrets_)
            async with dr_acp(None, home, env=env, prices=E10_PRICES) as client:
                root = await client.open_session(work, [forwarded("echo", **settings)])
                response = await client.ask(root, "Call the echo server.")
                (run_id,) = run_ids(client.printer.updates)
                log = client.run_log(run_id)
                [ready] = [e for e in log if isinstance(e, WorkerReady)]
                [server_pid] = [marker.name for marker in markers.iterdir()]
                worker, server = environ_of(ready.pid), environ_of(server_pid)
                updates = json.dumps(client.printer.updates)
        return response, log, worker, server, updates, model

    response, log, worker, server, updates, model = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    [status] = [e for e in log if isinstance(e, McpStatus)]
    assert [(s.tool, s.state) for s in status.servers] == [("echo", "bound")]
    assert set(settings) <= set(server) <= set(settings) | MCP_INHERITED
    token = worker["OPENAI_API_KEY"]
    assert token != key and token not in server.values()
    assert (server.get("OPENAI_API_KEY") == key) is named
    worker_text = "\0".join(f"{k}={v}" for k, v in worker.items())
    files = [
        p.read_bytes().decode(errors="replace") for p in home.rglob("*") if p.is_file()
    ]
    for value in (*secrets_.values(), settings["ECHO_TOKEN"]):
        for form in forms(value):
            assert form not in worker_text
            assert form not in updates
            assert not [text for text in files if form in text]
    for name, value in secrets_.items():
        if name != "OPENAI_API_KEY":
            assert value not in server.values(), name
    assert {c.authorization for c in model.calls} == {f"Bearer {key}"}
