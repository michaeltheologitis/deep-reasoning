from collections.abc import Mapping
from typing import Any

Plan = Mapping[str, list[str]]  # task substring -> the reply at each turn


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
