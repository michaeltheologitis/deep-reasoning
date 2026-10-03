"""A fake MCP server whose one tool has a property schema of `true` (any value, valid JSON
Schema), which the shim cannot describe today."""

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

server = Server("odd")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    schema = {"type": "object", "properties": {"anything": True}}
    return [types.Tool(name="odd", inputSchema=schema)]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


anyio.run(main)
