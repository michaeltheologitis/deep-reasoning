"""A fake MCP server that never answers: it never reads its stdin. With ECHO_MARKER_DIR
set it writes a file named after its pid there when it starts."""

import os
import time
from pathlib import Path

if marker := os.environ.get("ECHO_MARKER_DIR"):
    Path(marker, str(os.getpid())).write_text("started")
while True:
    time.sleep(3600)
