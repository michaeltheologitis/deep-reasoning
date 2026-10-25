"""An OpenAI-compatible chat endpoint on 127.0.0.1 for scripted runs: real HTTP, so the
worker runs unmodified. A plan scripts it: for an agent whose task contains a key, the
reply at each turn of its drive."""

import json
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Self

import structlog

log = structlog.get_logger()

Messages = list[dict[str, Any]]
Plan = Mapping[str, list[str]]


@dataclass(frozen=True)
class FakeCall:
    started: float
    model: str
    messages: Messages


def word_count_usage(messages: Messages, reply: str) -> dict[str, Any]:
    """One token per whitespace-separated word, plus one: the same on every machine."""
    prompt = sum(len(str(m.get("content", "")).split()) for m in messages) + 1
    completion = len(reply.split()) + 1
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }


def repl(*lines: str, think: str = "") -> str:
    """One assistant turn: an optional <think>, then a <repl> block."""
    head = f"<think>{think}</think>\n" if think else ""
    return head + "<repl>\n" + "\n".join(lines) + "\n</repl>"


def task_and_turn(messages: Messages) -> tuple[str, int]:
    """The live task (the last user message that is not an observation) and how many
    assistant turns its drive has had."""
    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]
        content = str(message.get("content", ""))
        if message.get("role") == "user" and not content.startswith("<observation>"):
            turns = sum(m.get("role") == "assistant" for m in messages[i + 1 :])
            return content, turns
    return "", 0


def scripted(plan: Plan) -> Callable[[Messages], str]:
    """A responder that follows the plan; its last reply repeats."""

    def respond(messages: Messages) -> str:
        task, turn = task_and_turn(messages)
        for key, replies in plan.items():
            if key in task:
                return replies[min(turn, len(replies) - 1)]
        raise AssertionError(f"no plan for task {task!r}")

    return respond


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128


class FakeOpenAI:
    """POST /v1/chat/completions on 127.0.0.1, as a context manager.

    `responder(messages)` gives each reply; one that raises answers HTTP 500 with its
    text. `.calls` records every request; `.base_url` is the endpoint.
    """

    def __init__(
        self,
        responder: Callable[[Messages], str],
        *,
        usage: Callable[[Messages, str], dict[str, Any]] = word_count_usage,
    ) -> None:
        self.calls: list[FakeCall] = []
        self._responder = responder
        self._usage = usage
        self._server: ThreadingHTTPServer | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def answer(self, request: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        messages = request.get("messages", [])
        model = request.get("model", "")
        self.calls.append(FakeCall(time.time(), model, messages))
        try:
            reply = self._responder(messages)
        except Exception as error:
            log.exception("fake_model.answered_500")
            return HTTPStatus.INTERNAL_SERVER_ERROR, {"error": {"message": str(error)}}
        return HTTPStatus.OK, {
            "id": f"chatcmpl-{len(self.calls)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": self._usage(messages, reply),
        }

    def __enter__(self) -> Self:
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

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
