"""An OpenAI-compatible chat endpoint on 127.0.0.1 for scripted runs (§8.2)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Self


@dataclass(frozen=True)
class FakeCall:
    started: float  # time.time() when the request arrived
    model: str
    messages: list[dict[str, Any]]


class FakeOpenAI:
    """POST /v1/chat/completions on 127.0.0.1, as an async context manager.

    .base_url is the endpoint; .calls records each call's start time and messages. A
    responder that raises answers HTTP 500 with the exception's text.
    """

    def __init__(
        self,
        responder: Callable[[list[dict[str, Any]]], str],
        *,
        latency_s: float = 0.0,
        usage: Callable[[list[dict[str, Any]], str], dict[str, Any]] | None = None,
    ) -> None:
        raise NotImplementedError

    @property
    def base_url(self) -> str:
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        raise NotImplementedError

    async def __aexit__(self, *exc: object) -> None:
        raise NotImplementedError
