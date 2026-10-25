"""Turn the old app's golden recordings into the prototype's mock chats.

Reads tests/acp/golden/<name>.native.jsonl and the scenarios' prompts from commit
a80bb2e, and writes prototype/data/recordings.json. The recordings carry no timings,
so the seconds are made up: a fixed time per step, sub-agents of one cell in parallel.

Run from the repo root: python3 scripts/mock_from_recordings.py
"""

import ast
import json
import subprocess
from pathlib import Path

COMMIT = "a80bb2e"
SCENARIOS = [
    "fanout2",
    "fanout20",
    "depth3",
    "failing",
    "unanswered",
    "exhausted",
    "fork",
    "namespace",
    "linear",
    "claude",
]
THINK_SECONDS = 0.6
CELL_SECONDS = 0.4
IGNORED_UPDATES = {"available_commands_update", "config_option_update"}
OUT = Path(__file__).resolve().parents[1] / "prototype" / "data" / "recordings.json"


def git_show(path):
    command = ["git", "show", f"{COMMIT}:{path}"]
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def scenario_prompts():
    prompts = {}
    for node in ast.walk(ast.parse(git_show("tests/acp/scenarios.py"))):
        if not (
            isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Scenario"
        ):
            continue
        fields = {keyword.arg: keyword.value for keyword in node.keywords}
        name = ast.literal_eval(fields["name"])
        prompts[name] = list(ast.literal_eval(fields["prompts"]))
    return prompts


def new_turn(prompt):
    return {
        "prompt": prompt,
        "steps": [],
        "answer": None,
        "outcome": None,
        "cost": None,
    }


def record_answer(agents, update):
    """A sub-agent's answer is the message it sends to another session."""
    sender = update["senderSessionId"]
    if sender in agents and sender != update["recipientSessionId"]:
        agents[sender]["result"] = update["content"][0]["text"]


def convert(messages, prompts):
    """The chat's turns: each a root run whose sub-agents nest under the cell that ran them."""
    prompts = iter(prompts)
    turns, turn = [], new_turn(next(prompts))
    agents, cells = {}, {}
    for message in messages:
        if "stopReason" in message.get("result", {}):
            turns.append(turn)
            turn = new_turn(next(prompts, None))
        if "params" not in message:
            continue
        session, update = message["params"]["sessionId"], message["params"]["update"]
        kind = update["sessionUpdate"]
        if kind in IGNORED_UPDATES:
            continue
        owner = agents.get(session, turn)
        meta = update.get("_meta", {}).get("deep_reasoner", {})
        if kind == "agent_thought_chunk":
            owner["steps"].append({"kind": "think", "text": update["content"]["text"]})
        elif kind == "tool_call":
            cell = {
                "kind": "cell",
                "code": update["rawInput"]["command"],
                "agents": [],
                "output": None,
                "status": "running",
            }
            cells[update["toolCallId"]] = cell
            owner["steps"].append(cell)
        elif kind == "tool_call_update":
            cell = cells[update["toolCallId"]]
            cell["output"] = update["rawOutput"]
            failed = cell["output"].startswith("Traceback")
            cell["status"] = "failed" if failed else "done"
        elif kind == "subagent_update" and update["state"]["state"] == "running":
            spawner = update["_meta"]["openhands"]["parentToolCallId"]
            row = {
                "kind": "agent",
                "task": update["title"],
                "status": "running",
                "namespace": meta["namespace"],
                "drive": meta["drive"],
                "steps": [],
                "result": None,
                "cost": None,
            }
            cells[spawner]["agents"].append(row)
            agents[update["sessionId"]] = row
        elif kind == "subagent_update":
            agents[update["sessionId"]]["status"] = meta["status"]
        elif kind == "session_message":
            record_answer(agents, update)
        elif kind == "usage_update":
            owner["cost"] = update["cost"]["amount"]
        elif kind == "agent_message_chunk" and "outcome" in meta:
            turn["answer"] = update["content"]["text"]
            turn["outcome"] = meta["outcome"]
        else:
            raise ValueError(f"no mock for a {kind} update")
    return turns


def add_seconds(holder):
    """A made-up duration for a run or sub-agent and everything under it."""
    total = 0.0
    for step in holder["steps"]:
        if step["kind"] == "think":
            total += THINK_SECONDS
            continue
        total += CELL_SECONDS + max(map(add_seconds, step["agents"]), default=0.0)
    holder["seconds"] = round(total, 1)
    return holder["seconds"]


def main():
    prompts = scenario_prompts()
    chats = []
    for name in SCENARIOS:
        lines = git_show(f"tests/acp/golden/{name}.native.jsonl").splitlines()
        turns = convert(map(json.loads, lines), prompts[name])
        for turn in turns:
            add_seconds(turn)
        chats.append({"id": name, "title": prompts[name][0], "turns": turns})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"chats": chats}, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
