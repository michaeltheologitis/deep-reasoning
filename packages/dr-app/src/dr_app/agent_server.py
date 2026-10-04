"""The agent-server's REST API, with the session key the launcher passes (D5 §4.5)."""

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, Final

from dr_app import texts
from dr_app.layout import SetupError

EXIT_USAGE: Final = 2


class AgentServerError(Exception):
    def __init__(self, method: str, path: str, status: int, detail: Any) -> None:
        super().__init__(f"{method} {path} ({status}): {detail}")
        self.method = method
        self.path = path
        self.status = status
        self.detail = detail


def _detail(raw: bytes) -> Any:
    """The body's "detail" when it is JSON with one, else its text."""
    text = raw.decode(errors="replace")
    try:
        body = json.loads(text)
    except ValueError:
        return text
    return body.get("detail", body) if isinstance(body, dict) else body


class AgentServer:
    """The agent-server's REST API with the session key; never through an HTTP proxy."""

    def __init__(self, url: str, session_key: str, *, timeout_s: float = 60.0) -> None:
        self._url = url.rstrip("/")
        self._session_key = session_key
        self._timeout_s = timeout_s
        # On macOS urllib would send loopback traffic to the system's HTTP proxy.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(self, method: str, path: str, body: Any = None) -> Any:
        """JSON in and out; 404 returns None; any other non-2xx raises AgentServerError,
        as does an agent-server that cannot be reached (status 0)."""
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            self._url + path,
            data=data,
            method=method,
            headers={
                "X-Session-API-Key": self._session_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self._opener.open(request, timeout=self._timeout_s) as response:
                raw = response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise AgentServerError(method, path, error.code, _detail(error.read()))
        except (urllib.error.URLError, OSError) as error:
            reason = getattr(error, "reason", error)
            raise AgentServerError(method, path, 0, str(reason)) from None
        return json.loads(raw) if raw else None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "AgentServer":
        """AGENT_SERVER_URL and SESSION_API_KEY (C3 §4.2). Raises SetupError(2, …) if
        either is missing."""
        url, key = env.get("AGENT_SERVER_URL"), env.get("SESSION_API_KEY")
        if not url or not key:
            raise SetupError(EXIT_USAGE, texts.NO_AGENT_SERVER)
        return cls(url, key)
