"""Whether a process is still running, for tests that pin what is left behind."""

import os
import time
from collections.abc import Iterable
from pathlib import Path


def alive(pid: int) -> bool:
    """Running, and not a zombie waiting to be reaped."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def running_after(pids: Iterable[int], seconds: float) -> list[int]:
    """The pids still alive once seconds have passed (polled, returning early when none is)."""
    pids = list(pids)
    deadline = time.monotonic() + seconds
    while (left := [p for p in pids if alive(p)]) and time.monotonic() < deadline:
        time.sleep(0.05)
    return left
