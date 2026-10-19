import os

import pytest
from deep_reasoner.config import ClientConfig, build_client

from deep_reasoning.acp.route import (
    DirectRoute,
    RouteGrant,
    missing_model_keys,
    worker_env,
)


def test_the_agent_servers_secrets_never_reach_the_worker():
    base = {
        "PATH": "/bin",
        "OPENAI_API_KEY": "sk-1",
        "OH_SECRET_KEY": "x",
        "OH_SESSION_API_KEYS_0": "y",
        "SESSION_API_KEY": "z",
        "OPENHANDS_AUTOMATION_API_KEY": "the agent-server's session key",
    }
    assert worker_env(base, DirectRoute().grant(session="s", run="r", upstream={})) == {
        "PATH": "/bin",
        "OPENAI_API_KEY": "sk-1",
        "PYTHONUNBUFFERED": "1",
    }


def test_a_grant_adds_and_removes_variables():
    grant = RouteGrant(
        env_add={"DR_PROXY_TOKEN": "t"}, env_remove=frozenset({"OPENAI_API_KEY"})
    )
    env = worker_env({"OPENAI_API_KEY": "sk-1", "HOME": "/h"}, grant)
    assert env == {"HOME": "/h", "DR_PROXY_TOKEN": "t", "PYTHONUNBUFFERED": "1"}


def test_the_direct_route_overrides_nothing():
    grant = DirectRoute().grant(
        session="s",
        run="r",
        upstream={"base_url": "u"},
        tool_upstreams={"rag": {"base_url": "v"}},
    )
    assert grant == RouteGrant()
    assert grant.tool_client_overrides == {}
    DirectRoute().release("r")


KEY_VARIABLES = ("DR_TEST_KEY", "OPENAI_API_KEY", "NOVITA_API_KEY")
REMOTE = "https://models.example.invalid/v1"


@pytest.mark.parametrize(
    ("client", "env"),
    [
        ({"api_key_env": "DR_TEST_KEY", "base_url": REMOTE}, {"DR_TEST_KEY": "k"}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": REMOTE}, {}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": REMOTE}, {"DR_TEST_KEY": ""}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": REMOTE}, {"OPENAI_API_KEY": "k"}),
        ({"base_url": REMOTE}, {}),
        ({"base_url": REMOTE}, {"NOVITA_API_KEY": "k"}),
        ({"api_key_env": "DR_TEST_KEY"}, {}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": "http://localhost:8000/v1"}, {}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": "http://127.0.0.1:9/v1"}, {}),
        ({"api_key_env": "DR_TEST_KEY", "base_url": "https://localhost/v1"}, {}),
    ],
    ids=[
        "key-set",
        "key-unset",
        "key-empty",
        "fallback-set",
        "default-name-unset",
        "default-name-set",
        "no-base-url",
        "localhost",
        "127.0.0.1",
        "https-localhost",
    ],
)
def test_missing_model_keys_says_what_build_client_refuses(client, env, monkeypatch):
    for name in KEY_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    try:
        build_client(ClientConfig(**client))
        refused = False
    except ValueError:
        refused = True
    missing = missing_model_keys([client], os.environ)
    assert missing == ([client.get("api_key_env", "NOVITA_API_KEY")] if refused else [])


def test_missing_model_keys_names_each_key_once_in_the_clients_order():
    clients = [
        {"api_key_env": "B_KEY", "base_url": REMOTE},
        {"api_key_env": "A_KEY", "base_url": REMOTE},
        {"api_key_env": "B_KEY", "base_url": REMOTE},
        {"api_key_env": "C_KEY", "base_url": REMOTE},
    ]
    assert missing_model_keys(clients, {"C_KEY": "k"}) == ["B_KEY", "A_KEY"]
