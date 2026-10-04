"""MCP grants written into a Library, as PUT /mcp writes them."""

from deep_reasoning.library import Library, shapes
from deep_reasoning.mcp.grants import McpGrantBody, mcp_block, shim_source


def put_grant(
    lib: Library, alias: str, granted_in: list[str], *, block=None, **fields
) -> None:
    """A grant of the server named alias, a stdio one that runs npx unless fields (the
    body's) say otherwise; block adds fields to the stored block."""
    body = McpGrantBody(
        **{
            "server": alias,
            "transport": "stdio",
            "command": "npx",
            "granted_in": granted_in,
            "base_version": 0,
        }
        | fields
    )
    yaml_text = shapes.canonical_yaml(mcp_block(alias, body) | (block or {}))
    lib.put_tool(alias, yaml_text, source=shim_source(), granted_in=granted_in)
