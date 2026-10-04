"""Claude Code as deep_reasoner's backbone, through dr-acp: the session acts through
`dr repl exec`, and each snippet it runs is a cell of the root.

The live test runs the real `claude` CLI on Michael's subscription
(CLAUDE_CODE_OAUTH_TOKEN), never on an API key: `uv run pytest -m live`. The other test
runs the same config against a fake CLI that acts the same way.
"""

import asyncio
import json
import os
import shlex
import shutil
from pathlib import Path

import pytest

from deep_reasoning.acp.testing.tree import tree
from tests.acp.harness import dr_acp, run, run_ids, scripted_env, write_config
from tests.acp.scenarios import acp_tree, deep_reasoner_tree

QUESTION = "What is 17 times 23?"
ANSWER = "391"
CONFIG = {
    "system_prompt": "You answer arithmetic questions.",
    # deep_reasoner builds a chat client for every run (build_reasoner), and a loopback
    # one needs no key; nothing in this run calls it.
    "client": {"base_url": "http://127.0.0.1:9/v1"},
    "entry_namespace": "root",
    "namespaces": {"root": {"tools": []}},
    # A Claude session has no turn cap in deep_reasoner: its budget and the timeout
    # after which deep_reasoner kills the CLI are what bound it.
    "reasoner": {
        "type": "claude_code",
        "model": "sonnet",
        "max_budget_usd": 0.5,
        "timeout_s": 180,
    },
}
LIVE_TIMEOUT_S = 300
TOKEN_ENV = "DR_ACP_LIVE_CLAUDE_TOKEN"
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, shlex, subprocess, sys
from pathlib import Path

if sys.argv[1:3] == ["auth", "status"]:
    print(json.dumps({"loggedIn": True, "authMethod": "fake"}))
    sys.exit(0)
Path(__file__).with_name("argv.json").write_text(json.dumps(sys.argv[1:]))
print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
for i, snippet in enumerate(["x = 17 * 23\\nprint(x)", "FinalAnswer(x)"]):
    command = "dr repl exec --code " + shlex.quote(snippet)
    done = subprocess.run(command, shell=True, capture_output=True, text=True)
    use = {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": command}}
    result = {"type": "tool_result", "tool_use_id": f"t{i}", "content": done.stdout}
    print(json.dumps({"type": "assistant", "message": {"content": [use]}}), flush=True)
    print(json.dumps({"type": "user", "message": {"content": [result]}}), flush=True)
print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                  "result": "391", "session_id": "fake", "total_cost_usd": 0.01,
                  "usage": {"input_tokens": 1, "output_tokens": 1}, "num_turns": 3}))
"""


def claude_config(directory: Path, executable: Path) -> Path:
    reasoner = {**CONFIG["reasoner"], "executable": str(executable)}
    return write_config(directory / "claude.yaml", {**CONFIG, "reasoner": reasoner})


def claude_with_token(directory: Path) -> Path:
    """The installed `claude`, given the subscription token under the name it reads.

    deep_reasoner drops every CLAUDE_CODE* variable from a Claude child's environment
    (claude_code.child_env), the token's among them, so it travels as TOKEN_ENV."""
    claude = shutil.which("claude")
    assert claude, "the Claude Code CLI is not on PATH"
    path = directory / "claude-with-token"
    path.write_text(
        "#!/bin/sh\n"
        f'export CLAUDE_CODE_OAUTH_TOKEN="${TOKEN_ENV}"\n'
        f'exec {shlex.quote(claude)} "$@"\n'
    )
    path.chmod(0o755)
    return path


def repl_snippets(transcript: Path) -> list[str]:
    """The code of each `dr repl exec` in a session's stream, as deep_reasoner kept it."""
    snippets = []
    for line in transcript.read_text().splitlines():
        try:
            event = json.loads(line)
            blocks = event["message"]["content"] if event["type"] == "assistant" else []
        except (ValueError, KeyError, TypeError):
            continue
        for block in blocks:
            if block.get("type") != "tool_use" or block.get("name") != "Bash":
                continue
            try:
                argv = shlex.split(block["input"]["command"])
            except ValueError:
                continue
            if argv[:3] == ["dr", "repl", "exec"] and "--code" in argv[:-1]:
                snippets.append(argv[argv.index("--code") + 1].strip())
    return snippets


def in_order_within(items: list[str], within: list[str]) -> bool:
    rest = iter(within)
    return all(item in rest for item in items)


async def ask_once(config: Path, home: Path, work: Path, env: dict[str, str]):
    async with dr_acp(config, home, env=env) as client:
        root = await client.open_session(work)
        async with asyncio.timeout(LIVE_TIMEOUT_S):
            response = await client.ask(root, QUESTION)
        return client, root, response


def assert_claude_code_answered_with_its_snippets_as_cells(
    client, root, response, home: Path
):
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    answer = [
        u["content"]["text"]
        for u in client.updates_on(root)
        if u["sessionUpdate"] == "agent_message_chunk"
    ][-1]
    assert ANSWER in answer
    (run_id,) = run_ids(client.printer.updates)
    log = client.run_log(run_id)
    start = next(e for e in log if e.kind == "agent.start" and e.parent is None)
    assert start.backbone == "claude_code"
    calls = {(e.call, e.model) for e in log if e.kind == "usage"}
    assert calls == {("claude", "sonnet")}
    run_dir = home / "runs" / run_id
    agents = acp_tree(tree(client.printer.updates))
    own = deep_reasoner_tree(run_dir)
    assert {n: parent for n, (parent, _) in agents.items()} == {
        n: parent for n, (parent, _) in own.items()
    }
    cells = [e.code for e in log if e.kind == "cell.end" and e.node == start.node]
    assert cells and agents[start.node][1] == len(cells)
    assert "FinalAnswer" in cells[-1]
    calls_file = run_dir / "claude_calls.jsonl"
    (session,) = map(json.loads, calls_file.read_text().splitlines())
    assert in_order_within(cells, repl_snippets(Path(session["transcript"])))


def test_a_claude_code_root_on_sonnet_answers_and_each_snippet_it_runs_is_a_cell(
    tmp_path: Path, home: Path, work: Path
):
    fake = tmp_path / "bin" / "claude"
    fake.parent.mkdir()
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(0o755)
    config = claude_config(tmp_path, fake)
    client, root, response = run(ask_once(config, home, work, scripted_env()))
    assert_claude_code_answered_with_its_snippets_as_cells(client, root, response, home)
    argv = json.loads((fake.parent / "argv.json").read_text())
    assert argv[argv.index("--model") + 1] == "sonnet"


@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"),
    reason="CLAUDE_CODE_OAUTH_TOKEN is not set: no Claude subscription to run on",
)
def test_live_claude_code_on_sonnet_answers_through_acp_and_each_snippet_is_a_cell(
    tmp_path: Path, home: Path, work: Path
):
    assert not os.environ.get("ANTHROPIC_API_KEY"), (
        "ANTHROPIC_API_KEY is set: Claude Code would bill it per token, not the subscription"
    )
    config = claude_config(tmp_path, claude_with_token(tmp_path))
    env = scripted_env(**{TOKEN_ENV: os.environ["CLAUDE_CODE_OAUTH_TOKEN"]})
    client, root, response = run(ask_once(config, home, work, env))
    assert_claude_code_answered_with_its_snippets_as_cells(client, root, response, home)
