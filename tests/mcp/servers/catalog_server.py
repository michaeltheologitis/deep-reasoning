"""A course catalog only this MCP server knows, for the live tier (D4 §10.5). It refuses
to answer without the CATALOG_TOKEN its settings give it."""

import os

from mcp.server.fastmcp import FastMCP

PREREQUISITES = {"ZQ-417": ["ZQ-101"], "ZQ-101": []}

server = FastMCP("catalog", log_level="WARNING")


@server.tool()
def prerequisites(course: str) -> list[str]:
    """The courses a student must finish before this one, by course code."""
    if not os.environ.get("CATALOG_TOKEN"):
        raise PermissionError("CATALOG_TOKEN is not set")
    return PREREQUISITES.get(course.strip().upper(), [])


if __name__ == "__main__":
    server.run()
