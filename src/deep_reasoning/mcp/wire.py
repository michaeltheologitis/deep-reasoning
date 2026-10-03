"""What crosses between dr-acp's front and its worker about MCP servers (D4 §4.1, §4.7):
the forwarded specs, each server's status, redaction, and the seen cache. Pydantic and
yaml only: the front imports it."""

import hashlib
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Literal

import yaml
from pydantic import BaseModel, ValidationError

Transport = Literal["stdio", "http", "sse"]
McpState = Literal["bound", "no_answer", "failed", "not_enabled", "skipped"]
MCP_FACTORY: Final = "mcp_server"
SEEN_DIR: Final = "mcp"
REDACTED: Final = "[redacted]"
SECRET_MIN: Final = 4  # shorter values are not redacted: they would match everywhere
SEEN_VERSION: Final = 1
REMOTE: Final = ("http", "sse")


class McpServerSpec(BaseModel):
    """A server as OpenHands forwarded it, secrets included: control pipe only."""

    name: str
    transport: Transport
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: str | None = None
    headers: dict[str, str] = {}


class McpServerStatus(BaseModel):
    tool: str  # the name it is bound under
    server: str  # its name in Canvas's MCP settings
    transport: Transport | None
    state: McpState
    detail: str | None = None  # failed and skipped: why; secrets redacted
    granted: list[str] = []  # the namespaces whose resolved tools name it
    seconds: float | None = None  # bound: time to connect; no_answer: the time waited
    count: int = 0  # bound: its tools
    told: str | None = None  # bound: deep_reasoner's describe() of its binding


class McpSeen(BaseModel):
    at: datetime
    run: str
    count: int
    told: str


class _SeenFile(McpSeen):
    v: Literal[1] = SEEN_VERSION
    server: str
    tool: str
    transport: Transport | None


def _pairs(entries: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """ACP's [{name, value}] lists (env, headers) as a mapping."""
    return {entry["name"]: entry["value"] for entry in entries}


def forwarded_specs(servers: Sequence[Mapping[str, Any]]) -> list[McpServerSpec]:
    """ACP mcpServers as D1 keeps them (dumped by alias): stdio (no type, or "stdio"),
    "http", "sse"; any other type is left out."""
    specs = []
    for server in servers:
        kind = server.get("type") or "stdio"
        if kind == "stdio":
            specs.append(
                McpServerSpec(
                    name=server["name"],
                    transport="stdio",
                    command=server["command"],
                    args=server.get("args") or [],
                    env=_pairs(server.get("env") or []),
                )
            )
        elif kind in REMOTE:
            specs.append(
                McpServerSpec(
                    name=server["name"],
                    transport=kind,
                    url=server["url"],
                    headers=_pairs(server.get("headers") or []),
                )
            )
    return specs


def servers_named(config_path: Path) -> set[str]:
    """The `server` of every tool block in main.yaml whose factory is MCP_FACTORY."""
    tools = (yaml.safe_load(config_path.read_text()) or {}).get("tools") or {}
    return {
        block["server"]
        for block in tools.values()
        if isinstance(block, dict) and block.get("factory") == MCP_FACTORY
    }


def specs_for_run(
    forwarded: Sequence[Mapping[str, Any]],
    config_path: Path,
) -> list[McpServerSpec]:
    """forwarded_specs(forwarded), keeping only the servers servers_named(config_path) names:
    what the front puts in Start.mcp_servers."""
    named = servers_named(config_path)
    return [spec for spec in forwarded_specs(forwarded) if spec.name in named]


def redact(text: str, secrets: Iterable[str]) -> str:
    """Every secret of at least SECRET_MIN characters replaced by REDACTED."""
    # Longest first, so a secret that contains another is replaced whole.
    for secret in sorted(set(secrets), key=len, reverse=True):
        if len(secret) >= SECRET_MIN:
            text = text.replace(secret, REDACTED)
    return text


def _seen_path(home: Path, server: str) -> Path:
    """home/mcp/<the first 16 hex of sha256(server)>.json."""
    digest = hashlib.sha256(server.encode()).hexdigest()[:16]
    return home / SEEN_DIR / f"{digest}.json"


def remember_seen(
    home: Path, run: str, servers: Sequence[McpServerStatus], at: datetime
) -> None:
    """§4.7: one file per bound server, atomically, 0600 in a 0700 directory."""
    directory = home / SEEN_DIR
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    for status in servers:
        if status.state != "bound":
            continue
        seen = _SeenFile(
            server=status.server,
            tool=status.tool,
            transport=status.transport,
            at=at,
            run=run,
            count=status.count,
            told=status.told or "",
        )
        # mkstemp creates the file 0600; os.replace makes it appear whole.
        fd, temporary = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(seen.model_dump_json())
        os.replace(temporary, _seen_path(home, status.server))


def read_seen(home: Path, server: str) -> McpSeen | None:
    """The last bound status remember_seen wrote for server; None when there is none."""
    try:
        seen = _SeenFile.model_validate_json(_seen_path(home, server).read_text())
    except (OSError, ValidationError):
        return None
    return McpSeen(at=seen.at, run=seen.run, count=seen.count, told=seen.told)
