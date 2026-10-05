"""The deep_reasoner agent profile, which makes dr-acp the app's agent (D5 §4.5.1,
decision F)."""

import shlex
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final

from dr_app import texts
from dr_app.agent_server import AgentServer, AgentServerError
from dr_app.layout import EXIT_AGENT_SERVER, ProfileRecord, SetupError, SetupState

PROFILE_NAME: Final = "deep_reasoner"
HOME_FLAG: Final = "--home"
SPEND_CAP_FLAG: Final = "--spend-cap-usd"
DEFAULT_SPEND_CAP_USD: Final = "5"
OWNED_FIELDS: Final = ("agent_kind", "acp_server", "acp_command", "acp_subagents")
PROFILES: Final = "/api/agent-profiles"


def _with_home(args: list[str], home: Path) -> list[str]:
    """args with the --home pair set: replaced where it is, else put first."""
    if HOME_FLAG in args[:-1]:
        at = args.index(HOME_FLAG)
        return [*args[:at], HOME_FLAG, str(home), *args[at + 2 :]]
    return [HOME_FLAG, str(home), *args]


def desired_profile(
    existing: Mapping[str, Any] | None,
    *,
    dr_acp: Path,
    home: Path,
) -> dict[str, Any]:
    """§4.5.1's table: the owned fields (acp_subagents always true) and the --home pair
    set, everything else kept from existing."""
    if existing is None:
        return {
            "agent_kind": "acp",
            "acp_server": "custom",
            "acp_command": shlex.join([str(dr_acp)]),
            "acp_subagents": True,
            "acp_args": [HOME_FLAG, str(home), SPEND_CAP_FLAG, DEFAULT_SPEND_CAP_USD],
            "secret_refs": None,
            "mcp_server_refs": None,
        }
    return {
        **existing,
        "agent_kind": "acp",
        "acp_server": "custom",
        "acp_command": shlex.join([str(dr_acp)]),
        "acp_subagents": True,
        "acp_args": _with_home(list(existing.get("acp_args") or []), home),
    }


def needs_write(existing: Mapping[str, Any] | None, want: Mapping[str, Any]) -> bool:
    """No profile yet, or an owned field or the arguments differ."""
    return existing is None or any(
        existing.get(name) != want.get(name) for name in (*OWNED_FIELDS, "acp_args")
    )


def ensure_profile(
    server: AgentServer,
    state: SetupState,
    *,
    dr_acp: Path,
    home: Path,
    log: Callable[[str], None],
) -> ProfileRecord:
    """§4.5.1, steps 1–5. Any refusal raises SetupError(12,
    texts.agent_server_failed(...))."""
    profile = f"{PROFILES}/{PROFILE_NAME}"
    try:
        found = server.request("GET", profile)
        existing = found["profile"] if found else None
        want = desired_profile(existing, dr_acp=dr_acp, home=home)
        written = needs_write(existing, want)
        if written:
            server.request("POST", profile, want)
            existing = server.request("GET", profile)["profile"]  # the server's id
        profile_id = str(existing["id"])
        activated = state.profile is not None and state.profile.activated_by_setup
        if not activated:
            server.request("POST", f"{PROFILES}/{profile_id}/activate")
    except AgentServerError as error:
        raise SetupError(
            EXIT_AGENT_SERVER,
            texts.agent_server_failed(
                error.method, error.path, str(error.status), str(error.detail)
            ),
        ) from None
    if not activated:
        log(texts.PROFILE_CREATED)
    elif written:
        log(texts.PROFILE_UPDATED)
    return ProfileRecord(profile_id, activated_by_setup=True)
