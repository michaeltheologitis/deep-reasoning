"""An in-test HTTP server answering like the agent-server's agent-profile, secrets and
Canvas App APIs, as far as dr-app uses them (SDK fork 34c540c)."""

import hashlib
import json
import platform
import re
import threading
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Self

PROFILES = re.compile(
    r"^/api/agent-profiles(?:/(?P<name>[^/]+))?(?P<activate>/activate)?$"
)
INSTALLED = re.compile(
    r"^/api/canvas-extensions/installed/(?P<name>[a-z0-9-]+)(?P<rest>/.*)?$"
)
PLATFORM = {
    "Linux": "linux",
    "Darwin": "darwin",
}[platform.system()] + {"x86_64": "-amd64", "aarch64": "-arm64", "arm64": "-arm64"}[
    platform.machine()
]


@dataclass
class Call:
    method: str
    path: str
    body: Any
    session_key: str | None


@dataclass
class App:
    manifest: dict[str, Any]
    path: Path
    enabled: bool = False
    prepared: str | None = None
    state: str = "stopped"

    @property
    def revision(self) -> str:
        payload = json.dumps(self.manifest, sort_keys=True).encode()
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass
class FakeAgentServer:
    session_key: str
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    active: str | None = None
    secrets: list[str] = field(default_factory=list)
    apps: dict[str, App] = field(default_factory=dict)
    calls: list[Call] = field(default_factory=list)
    # (method, path) -> (status, detail): answered instead of the real thing
    refuse: dict[tuple[str, str], tuple[int, Any]] = field(default_factory=dict)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def restart(self) -> None:
        """Backends do not survive an agent-server restart; approvals do."""
        for app in self.apps.values():
            app.state = "stopped"

    def answer(self, method: str, path: str, body: Any) -> tuple[int, Any]:
        if (method, path) in self.refuse:
            status, detail = self.refuse[(method, path)]
            return status, {"detail": detail}
        if path == "/api/settings/secrets" and method == "GET":
            return 200, {
                "secrets": [{"name": n, "description": None} for n in self.secrets]
            }
        if path == "/api/canvas-extensions/install" and method == "POST":
            return self.install(body)
        if match := PROFILES.match(path):
            return self.profile(method, match["name"], bool(match["activate"]), body)
        if match := INSTALLED.match(path):
            return self.app(method, match["name"], match["rest"] or "", body)
        return 404, {"detail": "Not Found"}

    def profile(
        self, method: str, name: str | None, activate: bool, body: Any
    ) -> tuple[int, Any]:
        if name is None and method == "GET":
            listed = [{"id": p["id"], "name": n} for n, p in self.profiles.items()]
            return 200, {"profiles": listed, "active_agent_profile_id": self.active}
        if activate and method == "POST":
            if name not in {p["id"] for p in self.profiles.values()}:
                return 404, {"detail": "not found"}
            self.active = name
            return 200, {"active_agent_profile_id": name}
        if method == "GET":
            if name not in self.profiles:
                return 404, {"detail": f"Agent profile '{name}' not found"}
            return 200, {"name": name, "profile": self.profiles[name]}
        if method == "POST":
            before = self.profiles.get(name)
            saved = {**body, "name": name}
            saved["id"] = before["id"] if before else str(uuid.uuid4())
            saved["revision"] = before["revision"] + 1 if before else 0
            self.profiles[name] = saved
            return 201, {"name": name, "message": "saved"}
        return 405, {"detail": "Method Not Allowed"}

    def install(self, body: dict[str, Any]) -> tuple[int, Any]:
        source = Path(body["source"])
        manifest = json.loads((source / "canvas-extension.json").read_text())
        name = manifest["name"]
        before = self.apps.get(name)
        if before and not body.get("force"):
            return 409, {"detail": "Canvas extension already installed."}
        if body.get("force") and any(a.state == "ready" for a in self.apps.values()):
            return 409, {
                "detail": "Stop running Canvas App backends before a forced install"
            }
        self.apps[name] = App(manifest, source, enabled=bool(before and before.enabled))
        return 200, {"name": name, "enabled": self.apps[name].enabled}

    def app(self, method: str, name: str, rest: str, body: Any) -> tuple[int, Any]:
        app = self.apps.get(name)
        if app is None:
            return 404, {"detail": f"Canvas extension '{name}' is not installed"}
        if rest == "" and method == "GET":
            return 200, {"name": name, "enabled": app.enabled, "manifest": app.manifest}
        if rest == "" and method == "PATCH":
            app.enabled = body["enabled"]
            return 200, {"name": name, "enabled": app.enabled}
        if rest == "/backend/prepare":
            artifact = app.manifest["backend"]["artifacts"].get(PLATFORM)
            if artifact is None:
                return 200, self.status(name)
            data = (app.path / artifact["path"]).read_bytes()
            if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                return 409, {
                    "detail": "backend artifact checksum does not match manifest"
                }
            app.prepared = body["revision"]
        elif rest == "/backend/start":
            if app.prepared != body["revision"]:
                return 409, {"detail": "backend revision must be prepared before start"}
            app.state = "ready"
        elif rest == "/backend/stop":
            app.state = "stopped"
        elif rest != "/backend":
            return 404, {"detail": "Not Found"}
        return 200, self.status(name)

    def status(self, name: str) -> dict[str, Any]:
        app = self.apps[name]
        supported = PLATFORM in app.manifest.get("backend", {}).get("artifacts", {})
        return {
            "name": name,
            "state": app.state if supported else "unsupported",
            "revision": app.revision,
            "prepared_revision": app.prepared,
            "detail": None
            if supported
            else "Canvas App backend does not support this platform",
        }

    def requests(self) -> list[tuple[str, str]]:
        return [(c.method, c.path) for c in self.calls]

    def __enter__(self) -> Self:
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def _any(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length else None
                key = self.headers.get("X-Session-API-Key")
                fake.calls.append(Call(self.command, self.path, body, key))
                status, answer = (
                    (401, {"detail": "bad session key"})
                    if key != fake.session_key
                    else fake.answer(self.command, self.path, body)
                )
                data = json.dumps(answer).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = do_PATCH = do_DELETE = _any

            def log_message(self, format: str, *args: Any) -> None:
                return None

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
