"""dr-acp: deep_reasoner as a stdio ACP agent.

Only the standard library is imported at module level: the stdout guard has to be in
place before anything of ours (or of a dependency) can print.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Options:
    config: Path | None  # --config PATH: a plain dr main.yaml; required until D2
    home: (
        Path | None
    )  # --home DIR, else $DR_HOME, else ~/.deep-reasoning (Home.resolve)
    flat: bool  # --flat: never send sub-agent sessions, whatever the client advertises
    heartbeat_s: float  # --heartbeat SECONDS, default 60
    log_level: str  # --log-level, default WARNING


def parse_options(argv: Sequence[str] | None) -> Options:
    raise NotImplementedError


def guard_stdout() -> int:
    """os.dup(1) -> acp_fd; os.dup2(2, 1); sys.stdout = sys.stderr; return acp_fd.

    Called before any other import of ours. acp_fd, the original fd 1, is the ACP writer's.
    """
    raise NotImplementedError


def main(argv: Sequence[str] | None = None) -> int:
    raise NotImplementedError
