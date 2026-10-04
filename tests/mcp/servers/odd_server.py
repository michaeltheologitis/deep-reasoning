"""A fake MCP server with one tool, `odd`, whose input properties are ODD_PROPERTIES (JSON),
by default {"anything": true, "nothing": false}: JSON Schema's schemas that accept any
value and none."""

import json
import os

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

PROPERTIES = json.loads(
    os.environ.get("ODD_PROPERTIES", '{"anything": true, "nothing": false}')
)

server = Server("odd")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    schema = {"type": "object", "properties": PROPERTIES}
    return [types.Tool(name="odd", inputSchema=schema)]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


anyio.run(main)
