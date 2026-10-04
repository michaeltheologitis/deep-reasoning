import shlex
from pathlib import Path

import pytest

from dr_app import texts
from dr_app.agent_server import AgentServer
from dr_app.layout import ProfileRecord, SetupError, SetupState
from dr_app.profile import PROFILE_NAME, ensure_profile

DR_ACP = Path("/Users/u/.deep-reasoning/runtime/current/bin/dr-acp")
HOME = Path("/Users/u/.deep-reasoning")
PROFILE = f"/api/agent-profiles/{PROFILE_NAME}"
FRESH = SetupState(1, str(HOME), None, None, None)


def ensure(agent_server, state=FRESH, *, dr_acp=DR_ACP, home=HOME):
    said: list[str] = []
    server = AgentServer(agent_server.url, agent_server.session_key)
    record = ensure_profile(server, state, dr_acp=dr_acp, home=home, log=said.append)
    return record, said


def after(state: SetupState, record: ProfileRecord) -> SetupState:
    return SetupState(state.v, state.dr_home, state.runtime, record, state.canvas_app)


def test_the_profile_is_created_and_made_the_default_once(agent_server):
    record, said = ensure(agent_server)
    profile = agent_server.profiles[PROFILE_NAME]
    assert profile == {
        "agent_kind": "acp",
        "acp_server": "custom",
        "acp_command": str(DR_ACP),
        "acp_subagents": True,
        "acp_args": ["--home", str(HOME), "--spend-cap-usd", "5"],
        "secret_refs": None,
        "mcp_server_refs": None,
        "name": PROFILE_NAME,
        "id": profile["id"],
        "revision": 0,
    }
    assert agent_server.active == profile["id"]
    assert record == ProfileRecord(profile["id"], activated_by_setup=True)
    assert said == [texts.PROFILE_CREATED]
    assert {c.session_key for c in agent_server.calls} == {agent_server.session_key}


def test_a_relaunch_writes_nothing(agent_server):
    record, _ = ensure(agent_server)
    agent_server.calls.clear()
    again, said = ensure(agent_server, after(FRESH, record))
    assert again == record
    assert agent_server.requests() == [
        ("GET", PROFILE),
        ("GET", "/api/agent-profiles"),
    ]
    assert said == []


def test_the_users_spend_cap_and_other_arguments_survive(agent_server):
    record, _ = ensure(agent_server)
    profile = agent_server.profiles[PROFILE_NAME]
    profile["acp_args"] = ["--home", "/old", "--spend-cap-usd", "20", "--flat"]
    profile["acp_model"] = "theirs"
    agent_server.active = "the-users-own-default"
    moved = Path("/var/tmp/deep-reasoning-501")
    _, said = ensure(agent_server, after(FRESH, record), home=moved)
    profile = agent_server.profiles[PROFILE_NAME]
    assert profile["acp_args"] == [
        "--home",
        str(moved),
        "--spend-cap-usd",
        "20",
        "--flat",
    ]
    assert profile["acp_model"] == "theirs"
    assert agent_server.active == "the-users-own-default"
    assert said == [texts.PROFILE_UPDATED]


def test_the_profile_always_turns_sub_agent_sessions_on(agent_server):
    record, _ = ensure(agent_server)
    agent_server.profiles[PROFILE_NAME]["acp_subagents"] = False
    agent_server.profiles[PROFILE_NAME]["acp_args"] = ["--spend-cap-usd", "1"]
    ensure(agent_server, after(FRESH, record))
    profile = agent_server.profiles[PROFILE_NAME]
    assert profile["acp_subagents"] is True
    assert profile["acp_args"] == ["--home", str(HOME), "--spend-cap-usd", "1"]


def test_a_refused_profile_fails_setup_with_exit_12(agent_server):
    agent_server.refuse[("POST", PROFILE)] = (422, [{"loc": ["body", "x"]}])
    with pytest.raises(SetupError) as refused:
        ensure(agent_server)
    assert refused.value.exit_code == 12
    assert refused.value.message == texts.agent_server_failed(
        "POST", PROFILE, "422", "[{'loc': ['body', 'x']}]"
    )


def test_a_deleted_profile_is_recreated_but_not_reactivated(agent_server):
    record, _ = ensure(agent_server)
    del agent_server.profiles[PROFILE_NAME]
    agent_server.active = None
    again, said = ensure(agent_server, after(FRESH, record))
    assert PROFILE_NAME in agent_server.profiles
    assert agent_server.active is None
    assert again.id == agent_server.profiles[PROFILE_NAME]["id"] != record.id
    assert said == [texts.PROFILE_UPDATED]


def test_a_command_path_with_spaces_is_shell_quoted(agent_server):
    spaced = Path("/Users/Jane Doe/.deep-reasoning/runtime/current/bin/dr-acp")
    ensure(agent_server, dr_acp=spaced)
    command = agent_server.profiles[PROFILE_NAME]["acp_command"]
    assert shlex.split(command) == [str(spaced)]
