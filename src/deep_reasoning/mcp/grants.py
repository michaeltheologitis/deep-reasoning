"""An MCP grant in the Library (D4 §4.2): a D2 tool row whose block snapshots a server's
non-secret settings and whose source is the shim. The App backend's side."""

import re
from importlib import resources
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field

from deep_reasoning.library.records import LibraryBadRequest, ToolRecord
from deep_reasoning.mcp.wire import MCP_FACTORY, McpSeen, Transport
from deep_reasoning.tools import texts

SHIM_MARKER: Final = "# deep-reasoning MCP shim"


class McpGrantBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: str = Field(min_length=1, max_length=128)
    transport: Transport
    command: str | None = None
    args: list[str] = []
    url: str | None = None
    env: list[str] = []  # names only
    headers: list[str] = []  # names only
    granted_in: list[str]
    base_version: int


class McpGrant(BaseModel):
    name: str  # the tool row's name: how the agent calls it
    version: int
    server: str
    transport: Transport
    command: str | None
    args: list[str]
    url: str | None
    env: list[str]
    headers: list[str]
    granted_in: list[str]
    shim_current: bool
    seen: McpSeen | None


def shim_source() -> str:
    """The installed shim.py's text (importlib.resources)."""
    return resources.files("deep_reasoning.mcp").joinpath("shim.py").read_text("utf-8")


def is_mcp_tool(record: ToolRecord) -> bool:
    """Factory MCP_FACTORY and a source starting with SHIM_MARKER."""
    return record.data.get("factory") == MCP_FACTORY and (
        record.source or ""
    ).startswith(SHIM_MARKER)


def header_env_name(server: str, header: str) -> str:
    """f"{server}_{header}" upper-cased, every run of characters other than [A-Z0-9] as
    "_", trimmed of "_": the variable dr reads a header's value from."""
    return re.sub(r"[^A-Z0-9]+", "_", f"{server}_{header}".upper()).strip("_")


def mcp_block(name: str, body: McpGrantBody) -> dict[str, Any]:
    """§4.2's block, without factory_from (D2 adds it). Raises LibraryBadRequest for a
    stdio grant without a command or a remote one without a URL."""
    block: dict[str, Any] = {
        "factory": MCP_FACTORY,
        "name": name,
        "server": body.server,
        "transport": body.transport,
    }
    if body.transport == "stdio":
        if not body.command:
            raise LibraryBadRequest(texts.MCP_NEEDS_COMMAND)
        return block | {"command": body.command, "args": body.args, "env": body.env}
    if not body.url:
        raise LibraryBadRequest(texts.MCP_NEEDS_URL)
    headers = {header: header_env_name(body.server, header) for header in body.headers}
    return block | {"url": body.url, "headers": headers}


def grant_record(record: ToolRecord, seen: McpSeen | None) -> McpGrant:
    data = record.data
    return McpGrant(
        name=record.name,
        version=record.version,
        server=data["server"],
        transport=data["transport"],
        command=data.get("command"),
        args=data.get("args", []),
        url=data.get("url"),
        env=data.get("env", []),
        headers=list(data.get("headers", {})),
        granted_in=record.granted_in,
        shim_current=record.source == shim_source(),
        seen=seen,
    )
