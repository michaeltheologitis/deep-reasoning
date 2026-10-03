"""Golden recordings of E1's scripted runs (§8.3).

`uv run python -m tests.acp.golden record` reruns every scenario in both modes and writes
tests/acp/golden/<scenario>.<native|flat>.jsonl: what dr-acp sent, normalized. The check
compares what can be compared: each stream's sequence (an agent's own updates, one child's
updates on its parent, the responses) and the tree, not the global interleaving, which
concurrent children make nondeterministic. Whoever changes the encoding re-records, and
the diff is reviewed.
"""

import asyncio
import json
import re
import sys
import sysconfig
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import deep_reasoner

from deep_reasoning.acp import ids
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.acp.testing.tree import Tree, tree
from tests.acp.harness import DrAcp, dr_acp
from tests.acp.scenarios import SCENARIOS, Scenario

GOLDEN = Path(__file__).parent / "golden"
SITE = str(Path(deep_reasoner.__file__).resolve().parents[1])
STDLIB = sysconfig.get_paths()["stdlib"]
_RUN = re.compile(ids.RUN_ID)
_ROOT = re.compile(r"s-[0-9a-f]{16}")
RUN = "00000000-000000-000000"  # every run id becomes this one, still a valid run id
_NODE = re.compile(rf"{RUN}-n(\d+)")
AMOUNT_DECIMALS = 10  # concurrent children add their costs in any order


@dataclass
class Played:
    client: DrAcp
    root: str
    outcomes: list[str]


async def play(scenario: Scenario, native: bool, directory: Path) -> Played:
    """One scenario, start to finish, on a fresh dr-acp."""
    home, work = directory / "home", directory / "work"
    work.mkdir(parents=True, exist_ok=True)
    async with FakeOpenAI(scenario.responder()) as model:
        config = scenario.write_config(directory / "config", model.base_url)
        async with dr_acp(config, home, native=native) as client:
            root = await client.open_session(work)
            outcomes = []
            for text in scenario.prompts:
                response = await client.ask(root, text)
                outcomes.append(response.field_meta["deep_reasoner"]["outcome"])
    return Played(client, root, outcomes)


def normalized(lines: list[bytes], directory: Path) -> list[dict[str, Any]]:
    """The messages, with ids, paths and float noise taken out, and only each session's
    last usage_update (the others are sent on a timer). Paths differ between machines
    (tracebacks carry them), so site-packages, the standard library and the test's
    directory are named, not spelled."""
    text = "".join(line.decode() for line in lines)
    text = (
        text.replace(SITE, "SITE")
        .replace(STDLIB, "STDLIB")
        .replace(str(directory), "TMP")
    )
    text = _ROOT.sub("s-0000000000000000", _RUN.sub(RUN, text))
    messages = [json.loads(line) for line in text.splitlines()]
    last_usage: dict[str, int] = {}
    for i, message in enumerate(messages):
        update = message.get("params", {}).get("update", {})
        if update.get("sessionUpdate") == "usage_update":
            last_usage[message["params"]["sessionId"]] = i
            if "cost" in update:
                update["cost"]["amount"] = round(
                    update["cost"]["amount"], AMOUNT_DECIMALS
                )
    kept = set(last_usage.values())
    return [
        m
        for i, m in enumerate(messages)
        if i in kept
        or m.get("params", {}).get("update", {}).get("sessionUpdate") != "usage_update"
    ]


def _stream(message: dict[str, Any]) -> tuple[str, ...]:
    """Which ordered stream a message belongs to."""
    if "params" not in message:
        return ("responses",)
    session = message["params"]["sessionId"]
    update = message["params"]["update"]
    for key in ("toolCallId", "messageId"):
        if key in update:
            return (session, *_NODE.findall(update[key])[:1])
    if update["sessionUpdate"] == "subagent_update":
        return (session, update["sessionId"])
    return (session,)


def streams(
    messages: list[dict[str, Any]],
) -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for message in messages:
        grouped.setdefault(_stream(message), []).append(message)
    return grouped


def as_tree(messages: list[dict[str, Any]]) -> Tree:
    updates = [
        (m["params"]["sessionId"], m["params"]["update"])
        for m in messages
        if "params" in m
    ]
    return tree(updates)


def golden_path(scenario: Scenario, native: bool) -> Path:
    return GOLDEN / f"{scenario.name}.{'native' if native else 'flat'}.jsonl"


def read_golden(scenario: Scenario, native: bool) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in golden_path(scenario, native).read_text().splitlines()
    ]


async def record() -> None:
    GOLDEN.mkdir(exist_ok=True)
    for scenario in SCENARIOS:
        for native in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                played = await play(scenario, native, Path(directory))
                messages = normalized(played.client.lines, Path(directory))
            path = golden_path(scenario, native)
            path.write_text(
                "".join(json.dumps(m, sort_keys=True) + "\n" for m in messages)
            )
            print(f"recorded {path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    if sys.argv[1:] != ["record"]:
        sys.exit("usage: python -m tests.acp.golden record")
    asyncio.run(record())
