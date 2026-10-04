"""A fake MCP server that prints much more than a pipe holds to stderr: 1 MB at start and
256 KB on each call of its one tool, with its LOUD_TOKEN on every line."""

import os
import sys

from mcp.server.fastmcp import FastMCP

LINE = f"noise {os.environ.get('LOUD_TOKEN', '')} " + "x" * 200 + "\n"
START_BYTES = 1024 * 1024
CALL_BYTES = 256 * 1024

server = FastMCP("loud", log_level="WARNING")


def shout(size: int) -> None:
    sys.stderr.write(LINE * (size // len(LINE)))
    sys.stderr.flush()


@server.tool()
def say(text: str) -> str:
    """Return the text, after printing CALL_BYTES to stderr."""
    shout(CALL_BYTES)
    return text


if __name__ == "__main__":
    shout(START_BYTES)
    server.run()
