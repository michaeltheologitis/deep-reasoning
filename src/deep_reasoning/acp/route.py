"""How a run reaches its model, and what the worker's environment holds (§4.7, D5's seam)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any] = field(default_factory=dict)
    env_add: Mapping[str, str] = field(default_factory=dict)
    env_remove: frozenset[str] = frozenset()


class ModelRoute(Protocol):
    def grant(
        self, *, session: str, run: str, upstream: Mapping[str, Any]
    ) -> RouteGrant: ...

    def release(self, run: str) -> None: ...


# Glob patterns.
ALWAYS_REMOVED: tuple[str, ...] = (
    "OH_SECRET_KEY",
    "OH_SESSION_API_KEYS_*",
    "SESSION_API_KEY",
)


class DirectRoute:
    """D1's only route: no overrides; the provider keys stay in the environment."""

    def grant(
        self, *, session: str, run: str, upstream: Mapping[str, Any]
    ) -> RouteGrant:
        raise NotImplementedError

    def release(self, run: str) -> None:
        raise NotImplementedError


def worker_env(base: Mapping[str, str], grant: RouteGrant) -> dict[str, str]:
    """base minus ALWAYS_REMOVED and grant.env_remove, plus grant.env_add and
    PYTHONUNBUFFERED=1."""
    raise NotImplementedError
