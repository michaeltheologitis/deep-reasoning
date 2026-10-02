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


def late_decomposition(name: str) -> str:
    raise NotImplementedError


def command_needs_task(name: str, hint: str) -> str:
    raise NotImplementedError


def namespace_fixed(namespace: str) -> str:
    raise NotImplementedError


def unknown_namespace(value: str, names: list[str]) -> str:
    raise NotImplementedError


def unknown_option(config_id: str) -> str:
    raise NotImplementedError


def unknown_session(session_id: str) -> str:
    raise NotImplementedError


def catalog_error(detail: str) -> str:
    raise NotImplementedError


def fresh_run_notice(after: str | None) -> str | None:
    """The notice a run starts with, chosen by how the previous run ended; None for none."""
    raise NotImplementedError


def build_failed(detail: str) -> str:
    raise NotImplementedError


def root_failed(detail: str) -> str:
    raise NotImplementedError


def crashed(code: int | None, path: str) -> str:
    raise NotImplementedError


def child_failed(detail: str) -> str:
    raise NotImplementedError


def cell_interrupted(reason: str) -> str:
    """reason: 'the run was stopped', 'the run crashed' or 'the agent stopped'."""
    raise NotImplementedError


def stop_requested(mode: Literal["dean", "interim"], backbone: str | None) -> str:
    raise NotImplementedError


def stopped_by_user(
    target: int, branch: tuple[int, ...], siblings: tuple[int, ...]
) -> str:
    """The interim's StoppedByUser message."""
    raise NotImplementedError
