from deep_reasoning.acp.route import DirectRoute, RouteGrant, worker_env


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
