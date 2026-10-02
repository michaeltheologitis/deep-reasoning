"""An OpenAI-compatible chat endpoint on 127.0.0.1 for scripted runs (§8.2).

Real HTTP, so the worker runs unmodified and D5's key proxy can later sit in front of it.
"""

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Self

import structlog

logger = structlog.get_logger(__name__)

Messages = list[dict[str, Any]]


@dataclass(frozen=True)
class FakeCall:
    started: float  # time.time() when the request arrived
    model: str
    messages: Messages


def token_usage(messages: Messages, reply: str) -> dict[str, Any]:
    """A deterministic count: one token per four characters, at least one."""
    prompt = sum(len(str(m.get("content", ""))) for m in messages) // 4 + 1
    completion = len(reply) // 4 + 1
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128  # a 20-way fan-out connects at once


class FakeOpenAI:
    """POST /v1/chat/completions on 127.0.0.1, as an async context manager.

    .base_url is the endpoint; .calls records each call's start time and messages. A
    responder that raises answers HTTP 500 with the exception's text.
    """

    def __init__(
        self,
        responder: Callable[[Messages], str],
        *,
        latency_s: float = 0.0,
        usage: Callable[[Messages, str], dict[str, Any]] | None = None,
    ) -> None:
        self.calls: list[FakeCall] = []
        self._responder = responder
        self._latency_s = latency_s
        self._usage = usage or token_usage
        self._server: ThreadingHTTPServer | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def answer(self, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """The HTTP status and body for one chat completion request."""
        messages = request.get("messages", [])
        self.calls.append(FakeCall(time.time(), request.get("model", ""), messages))
        time.sleep(self._latency_s)
        try:
            reply = self._responder(messages)
        except Exception as exc:
            logger.exception("fake_model.answered_500")
            return 500, {"error": {"message": str(exc), "type": "server_error"}}
        return 200, {
            "id": f"chatcmpl-{len(self.calls)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.get("model", ""),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": self._usage(messages, reply),
        }

    async def __aenter__(self) -> Self:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                status, body = fake.answer(json.loads(self.rfile.read(length)))
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, format: str, *args: Any) -> None:
                return None

        self._server = _Server(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
