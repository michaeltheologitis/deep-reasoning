"""A fake MCP server that prints its CRASH_TOKEN to stderr and exits 1 at start."""

import os
import sys

print(f"invalid token {os.environ.get('CRASH_TOKEN', '')}", file=sys.stderr, flush=True)
sys.exit(1)
