"""Every sentence a user of dr-acp can read, verbatim from §5.6.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

from typing import Literal

ROOT_STOPPED = (
    "Stopped. The run was ended and its REPL state is gone: deep_reasoner cannot cancel a "
    "running cell yet (ask A3). Your next message starts a fresh run."
)
PROMPT_BUSY = "a prompt is already running in this session."
FRESH_AFTER_STOP = (
    "Starting a fresh run: the previous one was stopped, so its variables and sub-agents "
    "are gone."
)
FRESH_AFTER_ERROR = (
    "Starting a fresh run: the previous one ended with an error, so its variables and "
    "sub-agents are gone."
)
FRESH_AFTER_RESTART = (
    "Starting a fresh run: the previous one ended when dr-acp restarted, so its variables "
    "and sub-agents are gone."
)
FRESH_AFTER_CLOSE = (
    "Starting a fresh run: the previous one was closed, so its variables and sub-agents "
    "are gone."
)
REPLAY_LOST = "(This run ended when dr-acp stopped; its REPL state is gone.)"
NAMESPACE_OPEN = (
    "The namespace this conversation runs in. Fixed after the first message."
)
NAMESPACE_FIXED_NOTE = "Fixed for this conversation."
NEEDS_CONFIG = "dr-acp needs --config PATH (a dr main.yaml) until the Library exists."
STOP_AT_NEXT_TURN = (
    "Stop requested: this agent and its sub-agents stop at their next turn, before their "
    "next model call. A cell that is already running finishes first."
)
STOP_WHEN_CLAUDE_ENDS = (
    "Stop requested: this agent runs a Claude Code session, which is one turn, so it "
    "stops when that session ends."
)
STOP_ENDING_CLAUDE = "Stop requested: its Claude Code session is being ended."

_FRESH_AFTER = {
    "stopped": FRESH_AFTER_STOP,
    "failed": FRESH_AFTER_ERROR,
    "crashed": FRESH_AFTER_ERROR,
    "lost": FRESH_AFTER_RESTART,
    "closed": FRESH_AFTER_CLOSE,
}


def late_decomposition(name: str) -> str:
    return (
        f"/{name} starts a conversation with a decomposition, so it only works as the "
        "first message. Start a new conversation, or ask in plain words."
    )


def command_needs_task(name: str, hint: str) -> str:
    return f"/{name} needs a task after it: /{name} <{hint}>"


def namespace_fixed(namespace: str) -> str:
    return f"namespace is fixed once a conversation has started (it is '{namespace}')."


def unknown_namespace(value: str, names: list[str]) -> str:
    return f"unknown namespace '{value}'; this library has: {', '.join(names)}."


def unknown_option(config_id: str) -> str:
    return f"dr-acp has one option, 'namespace'; got '{config_id}'."


def unknown_session(session_id: str) -> str:
    return f"unknown session '{session_id}'."


def catalog_error(detail: str) -> str:
    return f"dr-acp could not read its configuration: {detail}"


def fresh_run_notice(after: str | None) -> str | None:
    """The notice a run starts with, chosen by how the previous run ended; None for none."""
    return _FRESH_AFTER.get(after or "")


def build_failed(detail: str) -> str:
    return f"Could not start the run: {detail}"


def root_failed(detail: str) -> str:
    return (
        f"The run failed: {detail}. Its REPL state is gone; your next message starts a "
        "fresh run."
    )


def crashed(code: int | None, path: str) -> str:
    return (
        f"The run crashed (exit code {code}) and its REPL state is gone. Your next "
        f"message starts a fresh run. The worker's log is {path}."
    )


def child_failed(detail: str) -> str:
    return f"Failed: {detail}"


def cell_interrupted(reason: str) -> str:
    """reason: 'the run was stopped', 'the run crashed' or 'the agent stopped'."""
    return f"Not finished: {reason}"


def stop_requested(mode: Literal["dean", "interim"], backbone: str | None) -> str:
    if backbone != "claude_code":
        return STOP_AT_NEXT_TURN
    return STOP_ENDING_CLAUDE if mode == "dean" else STOP_WHEN_CLAUDE_ENDS


def stopped_by_user(
    target: int, branch: tuple[int, ...], siblings: tuple[int, ...]
) -> str:
    """The interim's StoppedByUser message."""
    sentence = f"stopped #{target}"
    if branch:
        sentence += f" and its branch ({', '.join(f'#{n}' for n in branch)})"
    sentence += "."
    if len(siblings) == 1:
        sentence += f" Its running sibling #{siblings[0]} in this run_all was stopped with it (A3)."
    elif siblings:
        named = ", ".join(f"#{n}" for n in siblings)
        sentence += (
            f" Its running siblings {named} in this run_all were stopped with it (A3)."
        )
    return sentence
