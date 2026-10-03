"""E1's scripted runs, and deep_reasoner's own account of each run's tree.

Each scenario is a small dr config and a script: for an agent whose task contains a key,
the reply at each turn of its drive. The model is FakeOpenAI, over real HTTP.
"""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from deep_reasoner.mocks import write_fake_claude_cli

from deep_reasoning.acp.testing.tree import AgentNode, CellNode, Tree

Plan = Mapping[str, list[str]]  # task substring -> the reply at each turn
NodeTree = dict[int, tuple[int | None, int]]  # agent node -> (parent agent, cells)
CELL_ID = re.compile(r"-n(\d+)-[ca]\d+$")


def repl(*lines: str, think: str = "") -> str:
    """One assistant turn: an optional <think>, then a <repl> block."""
    head = f"<think>{think}</think>\n" if think else ""
    return head + "<repl>\n" + "\n".join(lines) + "\n</repl>"


def task_and_turn(messages: list[dict[str, Any]]) -> tuple[str, int]:
    """The live task (the last user message that is not an observation) and how many
    assistant turns its drive has had."""
    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]
        content = str(message.get("content", ""))
        if message.get("role") == "user" and not content.startswith("<observation>"):
            turns = sum(m.get("role") == "assistant" for m in messages[i + 1 :])
            return content, turns
    return "", 0


def scripted(plan: Plan, failing: frozenset[tuple[str, int]] = frozenset()):
    """A FakeOpenAI responder that follows the plan; (key, turn) in failing answers 500."""

    def respond(messages: list[dict[str, Any]]) -> str:
        task, turn = task_and_turn(messages)
        for key, replies in plan.items():
            if key in task:
                if (key, turn) in failing:
                    raise RuntimeError(f"the model is unavailable for {key!r}")
                return replies[min(turn, len(replies) - 1)]
        raise AssertionError(f"no plan for task {task!r}")

    return respond


BASE_CONFIG: dict[str, Any] = {
    "model": "fake-model",
    "client": {"base_url": "", "api_key_env": "DR_ACP_TEST_KEY", "max_retries": 0},
    "system_prompt": "You are a scripted test agent.",
    "max_iter": 6,
    "max_depth": 4,
    "entry_namespace": "root",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    prompts: tuple[str, ...]
    plan: Plan
    outcomes: tuple[str, ...]  # each prompt's PromptResult.outcome
    config: Mapping[str, Any] = field(default_factory=dict)  # over BASE_CONFIG
    failing: frozenset[tuple[str, int]] = frozenset()
    claude: bool = False  # the root runs on the Claude backbone, with a fake claude CLI

    def write_config(self, directory: Path, base_url: str) -> Path:
        config = {**BASE_CONFIG, **self.config}
        config["client"] = {**BASE_CONFIG["client"], "base_url": base_url}
        if self.claude:
            fake = write_fake_claude_cli(directory / "bin")
            config["reasoner"] = {"type": "claude_code", "executable": str(fake)}
        path = directory / f"{self.name}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(config, sort_keys=False))
        return path

    def responder(self):
        return scripted(self.plan, self.failing)


COURSES = [f"C{i}" for i in range(20)]

SCENARIOS = [
    Scenario(
        name="linear",
        prompts=("/count-up Count to three.", "Now add one."),
        config={
            "decompositions": [
                {
                    "name": "count up",
                    "messages": [
                        {"role": "user", "content": "{{ task }}"},
                        {
                            "role": "assistant",
                            "content": repl("xs = [1, 2, 3]", "print(xs)"),
                        },
                    ],
                }
            ]
        },
        plan={
            "Count to three.": [
                repl("print(len(xs))", think="xs holds the count."),
                repl("FinalAnswer(len(xs))"),
            ],
            "Now add one.": [repl("FinalAnswer(len(xs) + 1)", think="Resume.")],
        },
        outcomes=("answered", "answered"),
    ),
    Scenario(
        name="fanout2",
        prompts=("Summarize two courses.",),
        plan={
            "Summarize two courses.": [
                repl(
                    "r = run_all({c: anext(subagent().send(f'Summarize {c}.')) for c in ['C1', 'C2']})",
                    "print(r)",
                    think="Fan out.",
                ),
                repl("FinalAnswer(r)"),
            ],
            "Summarize C1.": [
                repl("print('C1 has 3 credits')"),
                repl("FinalAnswer('C1: 3')"),
            ],
            "Summarize C2.": [repl("FinalAnswer('C2: 4')", think="Easy.")],
        },
        outcomes=("answered",),
    ),
    Scenario(
        name="fanout20",
        prompts=("Summarize twenty courses.",),
        plan={
            "Summarize twenty courses.": [
                repl(
                    f"r = run_all({{c: anext(subagent().send(f'Count {{c}}.')) for c in {COURSES!r}}})",
                    "print(len(r))",
                ),
                repl("FinalAnswer(sorted(r))"),
            ],
            **{f"Count {c}.": [repl(f"FinalAnswer({c!r})")] for c in COURSES},
        },
        outcomes=("answered",),
    ),
    Scenario(
        name="depth3",
        prompts=("Plan the term.",),
        plan={
            "Plan the term.": [
                repl("plan = subagent('Survey CS.')", "print(plan)"),
                repl("FinalAnswer(plan)"),
            ],
            "Survey CS.": [
                repl("course = subagent('Read CS101.')", "print(course)"),
                repl("FinalAnswer('CS: ' + course)"),
            ],
            "Read CS101.": [repl("FinalAnswer('CS101 is light')")],
        },
        outcomes=("answered",),
    ),
    Scenario(
        name="namespace",
        prompts=("Use the math namespace.",),
        config={"namespaces": {"math": {"vars": {"pi": 3.14}}}},
        plan={
            "Use the math namespace.": [
                repl("x = subagent('Add pi and one.', namespace='math')", "print(x)"),
                repl("FinalAnswer(x)"),
            ],
            "Add pi and one.": [repl("FinalAnswer(pi + 1)")],
        },
        outcomes=("answered",),
    ),
    Scenario(
        name="fork",
        prompts=("Remember and fork.",),
        plan={
            "Remember and fork.": [
                repl(
                    "s = subagent()",
                    "first = run_all([anext(s.send('Note that the answer is 42.'))])",
                    "again = run_all([anext(s.send('Say it again.'))])",
                    "f = s.fork()",
                    "forked = run_all([anext(f.send('Repeat it from the fork.'))])",
                    "print(first, again, forked)",
                ),
                repl("FinalAnswer([first, again, forked])"),
            ],
            "Note that the answer is 42.": [repl("FinalAnswer(42)")],
            "Say it again.": [repl("FinalAnswer('again 42')")],
            "Repeat it from the fork.": [repl("FinalAnswer('forked 42')")],
        },
        outcomes=("answered",),
    ),
    Scenario(
        name="exhausted",
        prompts=("Never finish.",),
        config={"max_iter": 3},
        plan={
            "Never finish.": [
                repl(
                    "r = run_all([anext(subagent().send('Loop forever.'))])", "print(r)"
                ),
                repl("print('still thinking')"),
            ],
            "Loop forever.": [repl("print('looping')")],
        },
        outcomes=("exhausted",),
    ),
    Scenario(
        name="failing",
        prompts=("Survive failures.",),
        plan={
            "Survive failures.": [
                repl("print(1 / 0)", think="This cell fails."),
                repl("r = subagent('Break the model.')", "print(r)"),
                repl("FinalAnswer('recovered')"),
            ],
            "Break the model.": [repl("print('trying')")],
        },
        failing=frozenset({("Break the model.", 1)}),
        outcomes=("answered",),
    ),
    Scenario(
        name="claude",
        prompts=("Ask Claude.",),
        plan={},
        claude=True,
        outcomes=("exhausted",),
    ),
]
BY_NAME = {s.name: s for s in SCENARIOS}


def deep_reasoner_tree(run_dir: Path) -> NodeTree:
    """deep_reasoner's own tree, from what it wrote in the run directory.

    An agent is a node whose model calls are logged as kind agent (llm_calls.jsonl); a
    fork, whose own LLM logs as a kind llm node directly under it that writes code; or
    the agent a Claude session runs for (claude_calls.jsonl). Its cells are the turns
    with a <repl> block in its conversation (the node YAML holds every turn); a fork's,
    those after its own task, since its conversation starts with its origin's.
    """
    agents: dict[int, tuple[tuple[int, ...], int]] = {}
    for row in _jsonl(run_dir / "llm_calls.jsonl"):
        node, ancestry = row["node_id"], tuple(row["ancestry"])
        conversation = _conversation(run_dir, node)
        if row["kind"] == "agent":
            agents[node] = (ancestry, _repl_turns(conversation))
        elif _repl_turns(conversation):
            agents[ancestry[-2]] = (
                ancestry[:-1],
                _repl_turns(_since_task(conversation)),
            )
    for row in _jsonl(run_dir / "claude_calls.jsonl"):
        ancestry = tuple(row["ancestry"])
        agents.setdefault(ancestry[-2], (ancestry[:-1], 0))
    tree: NodeTree = {}
    for node, (ancestry, cells) in agents.items():
        parents = [a for a in ancestry[:-1] if a in agents]
        tree[node] = (parents[-1] if parents else None, cells)
    return tree


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _conversation(run_dir: Path, node: int) -> list[dict[str, str]]:
    files = list(run_dir.glob(f"n_{node}_d_*.yaml"))
    return yaml.safe_load(files[0].read_text())["conversation"] if files else []


def _repl_turns(conversation: list[dict[str, str]]) -> int:
    """The turns that ran a cell. When the system prompt sits inside the conversation
    (deep_reasoner records a puppeteered turn before it, so its YAML writer does not
    split the prefix off), the prompt and its demonstrations, from the first system
    message to the last, ran nothing."""
    systems = [i for i, turn in enumerate(conversation) if "system" in turn]
    if systems:
        conversation = conversation[: systems[0]] + conversation[systems[-1] + 1 :]
    return sum("<repl>" in turn.get("assistant", "") for turn in conversation)


def _since_task(conversation: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks = [
        i
        for i, turn in enumerate(conversation)
        if "user" in turn and not turn["user"].startswith("<observation>")
    ]
    return conversation[tasks[-1] :] if tasks else conversation


def acp_tree(tree: Tree) -> NodeTree:
    """The same shape, from testing.tree's rebuild of the ACP stream: an agent's parent is
    the owner of the cell it was drawn under; its cells are summed over its drives."""
    result: dict[int, list[Any]] = {}

    def visit(agent: AgentNode, parent: int | None) -> None:
        entry = result.setdefault(agent.node, [parent, 0])
        for item in agent.items:
            if isinstance(item, CellNode):
                entry[1] += 1
                for child in item.agents:
                    visit(child, int(CELL_ID.search(item.tool_call_id).group(1)))

    for run in tree.runs:
        # A root with no cell names no node on the wire; every run's root is node 1.
        run.root.node = run.root.node or 1
        visit(run.root, None)
    return {node: (parent, cells) for node, (parent, cells) in result.items()}
