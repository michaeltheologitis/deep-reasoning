"""An OpenAI-compatible endpoint on 127.0.0.1: chat completions and embeddings."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Self

EMBEDDING = [0.5, 0.5, 0.5, 0.5]


class _Server(ThreadingHTTPServer):
    daemon_threads = True


class FakeOpenAI:
    """Answers every chat call with reply and every embedding with EMBEDDING, as a
    context manager. .requests holds each chat request's body, in arrival order."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.requests: list[dict[str, Any]] = []
        self._server: _Server | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def answer(self, path: str, request: dict[str, Any]) -> dict[str, Any]:
        if path.endswith("/embeddings"):
            inputs = (
                request["input"]
                if isinstance(request["input"], list)
                else [request["input"]]
            )
            return {
                "object": "list",
                "model": request.get("model", ""),
                "data": [
                    {"object": "embedding", "index": i, "embedding": EMBEDDING}
                    for i in range(len(inputs))
                ],
                "usage": {"prompt_tokens": len(inputs), "total_tokens": len(inputs)},
            }
        self.requests.append(request)
        return {
            "id": f"chatcmpl-{len(self.requests)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.get("model", ""),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": self.reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    def __enter__(self) -> Self:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = fake.answer(self.path, json.loads(self.rfile.read(length)))
                data = json.dumps(body).encode()
                self.send_response(200)
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
