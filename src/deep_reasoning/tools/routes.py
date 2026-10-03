"""The routes D4 adds to the App backend (D4 §7.2), behind D2's guard."""

from typing import Any

from pydantic import BaseModel, ConfigDict
from starlette.requests import Request
from starlette.routing import Route

from deep_reasoning.library import shapes
from deep_reasoning.library.api import _parse, json_route
from deep_reasoning.library.library import Library
from deep_reasoning.library.records import LibraryRefused, LibraryValidationError
from deep_reasoning.mcp.grants import (
    McpGrantBody,
    grant_record,
    is_mcp_tool,
    mcp_block,
    shim_source,
)
from deep_reasoning.mcp.wire import read_seen
from deep_reasoning.tools import texts
from deep_reasoning.tools.check import check_tool, tool_name_errors


class CheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yaml: str
    source: str | None = None
    example: str | None = None


def tool_routes(library: Library) -> list[Route]:
    """POST /tools/{name}/check, GET /mcp, PUT /mcp/{name} (§7.2), built with D2's json_route."""
    lib = library
    home = lib.path.parent  # $DR_HOME, where dr-acp remembers the tools it saw (§4.7)

    def check(request: Request, body: bytes) -> Any:
        sent = _parse(CheckBody, body)
        name = request.path_params["name"]
        return check_tool(name, sent.yaml, sent.source, example=sent.example)

    def grants(request: Request, body: bytes) -> Any:
        return [
            grant_record(tool, read_seen(home, tool.data["server"]))
            for tool in lib.tools()
            if is_mcp_tool(tool)
        ]

    def put_grant(request: Request, body: bytes) -> Any:
        name, sent = request.path_params["name"], _parse(McpGrantBody, body)
        shapes.validate_tool(name, "{}", None)  # D2's name rule
        if errors := tool_name_errors(name):
            raise LibraryValidationError(errors[0].msg, errors)
        tools = lib.state().tools
        taken = [
            t.name
            for t in tools.values()
            if t.name != name and is_mcp_tool(t) and t.data["server"] == sent.server
        ]
        if taken:
            raise LibraryRefused(texts.mcp_server_taken(sent.server, taken[0]))
        record = lib.put_tool(
            name,
            shapes.canonical_yaml(mcp_block(name, sent)),
            source=shim_source(),
            granted_in=sent.granted_in,
            base_version=sent.base_version,
        )
        listed = grant_record(record, read_seen(home, sent.server))
        return listed, 200 if name in tools else 201

    return [
        json_route("/tools/{name}/check", "POST", check),
        json_route("/mcp", "GET", grants),
        json_route("/mcp/{name}", "PUT", put_grant),
    ]
