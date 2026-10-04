"""A fake MCP server that prints its CRASH_TOKEN to stderr and exits 1 at start. With
CRASH_SPLIT set, the token is printed in two writes, 0.2 s apart."""

import os
import sys
import time

token = os.environ.get("CRASH_TOKEN", "")
half = len(token) // 2 if "CRASH_SPLIT" in os.environ else len(token)
print(f"invalid token {token[:half]}", end="", file=sys.stderr, flush=True)
if "CRASH_SPLIT" in os.environ:
    time.sleep(0.2)
print(token[half:], file=sys.stderr, flush=True)
sys.exit(1)
