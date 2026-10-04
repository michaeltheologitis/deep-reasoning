"""A fake MCP server of our own, written with FastMCP: stdio by default; streamable HTTP
with --http PORT, SSE with --sse PORT. With ECHO_MARKER_DIR set it writes a file named
after its pid there when it starts, so a test can tell it ran and find it."""

import argparse
import os
from pathlib import Path
from typing import TypedDict

import anyio
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.types import Image

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d4944415478da63f8ffff3f0005fe02fea7d6a9b70000000049454e44ae426082"
)

server = FastMCP("echo", log_level="WARNING")


class Sum(TypedDict):
    sum: int


@server.tool()
def echo(text: str) -> str:
    """Return the text unchanged."""
    return text


@server.tool()
def add(a: int, b: int = 1) -> Sum:
    """Add two whole numbers.
    The sum comes back as a dict."""
    return {"sum": a + b}


@server.tool(structured_output=False)
def plain(text: str) -> str:
    """Return the text as plain content, with no structured result."""
    return text


@server.tool()
def picture() -> Image:
    """A one-pixel image."""
    return Image(data=PNG, format="png")


@server.tool()
def fail(why: str) -> str:
    """Always fails, saying why."""
    raise ValueError(why)


@server.tool()
def token() -> str:
    """The ECHO_TOKEN this server was started with."""
    return os.environ["ECHO_TOKEN"]


@server.tool()
def env_names() -> list[str]:
    """The names of this server's environment variables."""
    return sorted(os.environ)


@server.tool()
async def sleep(seconds: float) -> str:
    """Sleep, then say so."""
    await anyio.sleep(seconds)
    return f"slept {seconds:g} s"


@server.tool()
def crash() -> str:
    """End this server's process at once."""
    os._exit(1)


@server.tool(name="2nd-opinion")
def second_opinion(question: str) -> str:
    """A tool whose name cannot be a Python attribute."""
    return f"ask again: {question}"


@server.tool()
def whoami(ctx: Context) -> str:
    """The Authorization header of an HTTP request."""
    return ctx.request_context.request.headers.get("authorization", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", type=int)
    parser.add_argument("--sse", type=int)
    args = parser.parse_args()
    if marker := os.environ.get("ECHO_MARKER_DIR"):
        Path(marker, str(os.getpid())).write_text("started")
    if args.http or args.sse:
        server.settings.port = args.http or args.sse
        server.run("streamable-http" if args.http else "sse")
    else:
        server.run()


if __name__ == "__main__":
    main()
