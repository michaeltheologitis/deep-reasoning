"""TASK-46 across the repositories (TASK-65 §7.3): an LLM profile as Canvas's Settings →
LLM saves it, with no key and no base URL, active and named as the title profile, is never
called, and the chat's first message titles it with no error. Every outbound connection
goes to a recording proxy, so nothing can reach a provider and every attempt is seen."""

import shlex
import time

import pytest

from dr_app.profile import PROFILE_NAME
from tests.crossrepo.agent_server import (
    agent_server,
    conversation_events,
    recording_proxy,
    sdk_checkout,
)

QUESTION = "What is 2 + 2?"
TITLE_PROFILE = "gpt-5-5"
TITLED_S = 30.0


@pytest.mark.crossrepo
def test_a_title_profile_without_a_key_is_never_called_and_the_first_message_titles_the_chat(
    tmp_path,
):
    checkout = sdk_checkout()
    work = tmp_path / "work"
    work.mkdir()
    with (
        recording_proxy() as proxy,
        agent_server(
            checkout, tmp_path / "agent-server", outbound_proxy=proxy.url
        ) as server,
    ):
        scripted = checkout / "tests" / "fixtures" / "acp" / "scripted_agent.py"
        agent = shlex.join([server.python, str(scripted), "--no-commands"])
        profiles = f"/api/agent-profiles/{PROFILE_NAME}"
        server.request(
            "POST",
            profiles,
            {
                "agent_kind": "acp",
                "acp_server": "custom",
                "acp_command": agent,
                "acp_subagents": True,
            },
        )
        profile_id = server.request("GET", profiles)["profile"]["id"]
        server.request("POST", f"/api/agent-profiles/{profile_id}/activate")
        llm = f"/api/profiles/{TITLE_PROFILE}"
        server.request("POST", llm, {"llm": {"model": "gpt-5.5"}})
        server.request("POST", f"{llm}/activate")
        before = list(proxy.attempts)
        conversation = server.request(
            "POST",
            "/api/conversations",
            {
                "agent_profile_id": profile_id,
                "workspace": {"kind": "LocalWorkspace", "working_dir": str(work)},
                "initial_message": {
                    "role": "user",
                    "content": [{"type": "text", "text": QUESTION}],
                    "run": True,
                },
                "autotitle": True,
                "title_llm_profile": TITLE_PROFILE,
            },
        )["id"]
        deadline = time.monotonic() + TITLED_S
        while (
            title := server.request("GET", f"/api/conversations/{conversation}")[
                "title"
            ]
        ) != QUESTION and time.monotonic() < deadline:
            time.sleep(0.2)
        events = conversation_events(server, conversation)
    assert (before, proxy.attempts) == ([], [])
    assert title == QUESTION
    assert [e for e in events if e["kind"] == "ConversationErrorEvent"] == []
