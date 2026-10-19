"""How a run reaches its model, and what the worker's environment holds (§4.7)."""

import fnmatch
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Final, Protocol

NO_TOOL_UPSTREAMS: Mapping[str, Mapping[str, Any]] = MappingProxyType({})
# build_client's fallback, config.py:256
OPENAI_FALLBACK_KEY_ENV: Final = "OPENAI_API_KEY"
# ClientConfig.api_key_env's default
DEEP_REASONER_DEFAULT_KEY_ENV: Final = "NOVITA_API_KEY"
# build_client gives a client on these an "EMPTY" key instead of refusing.
KEYLESS_BASE_URL_PREFIXES: Final = ("http://localhost", "http://127.0.0.1")


@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any] = field(default_factory=dict)
    env_add: Mapping[str, str] = field(default_factory=dict)
    env_remove: frozenset[str] = frozenset()
    # tool name -> overrides merged over that tool's own client block
    tool_client_overrides: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


class ModelRoute(Protocol):
    """Grants each run its client settings and environment; release(run) follows the
    run's end. tool_upstreams holds each tool's own client block, by tool name."""

    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = NO_TOOL_UPSTREAMS,
    ) -> RouteGrant: ...

    def release(self, run: str) -> None: ...


# Glob patterns. The agent-server's own secrets: each opens its API, secrets included.
# OPENHANDS_AUTOMATION_API_KEY is its session key as Canvas's launcher names it.
ALWAYS_REMOVED: tuple[str, ...] = (
    "OH_SECRET_KEY",
    "OH_SESSION_API_KEYS_*",
    "SESSION_API_KEY",
    "OPENHANDS_AUTOMATION_API_KEY",
)


class DirectRoute:
    """No overrides: the provider keys stay in the worker's environment."""

    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = NO_TOOL_UPSTREAMS,
    ) -> RouteGrant:
        return RouteGrant()

    def release(self, run: str) -> None:
        return None


def worker_env(base: Mapping[str, str], grant: RouteGrant) -> dict[str, str]:
    """base minus ALWAYS_REMOVED and grant.env_remove, plus grant.env_add and
    PYTHONUNBUFFERED=1."""
    removed = (*ALWAYS_REMOVED, *grant.env_remove)
    env = {
        key: value
        for key, value in base.items()
        if not any(fnmatch.fnmatchcase(key, pattern) for pattern in removed)
    }
    return env | dict(grant.env_add) | {"PYTHONUNBUFFERED": "1"}


def missing_model_keys(
    clients: Iterable[Mapping[str, Any]],
    env: Mapping[str, str],
) -> list[str]:
    """The key variables the clients would fail to build without, as deep_reasoner's
    build_client decides: a client's api_key_env (DEEP_REASONER_DEFAULT_KEY_ENV when
    unset) when neither it nor OPENAI_FALLBACK_KEY_ENV has a non-empty value in env, and
    its base_url does not start with one of KEYLESS_BASE_URL_PREFIXES. Each name once,
    in the clients' order; empty when every client builds."""
    missing: list[str] = []
    for client in clients:
        name = client.get("api_key_env") or DEEP_REASONER_DEFAULT_KEY_ENV
        keyed = env.get(name) or env.get(OPENAI_FALLBACK_KEY_ENV)
        keyless = (client.get("base_url") or "").startswith(KEYLESS_BASE_URL_PREFIXES)
        if not keyed and not keyless and name not in missing:
            missing.append(name)
    return missing
