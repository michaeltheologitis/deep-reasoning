"""dr-acp: deep_reasoner as a stdio ACP agent.

Only the standard library is imported at module level: the stdout guard has to be in
place before anything of ours (or of a dependency) can print.
"""

import argparse
import asyncio
import logging
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

EXIT_USAGE = 2


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
    parser = argparse.ArgumentParser(prog="dr-acp", description=__doc__)
    parser.add_argument("--config", type=Path, help="a plain dr main.yaml")
    parser.add_argument(
        "--home", type=Path, help="run logs and sessions (default $DR_HOME)"
    )
    parser.add_argument(
        "--flat", action="store_true", help="never send sub-agent sessions"
    )
    parser.add_argument("--heartbeat", type=float, default=60.0, metavar="SECONDS")
    parser.add_argument("--log-level", default="WARNING")
    args = parser.parse_args(argv)
    return Options(
        args.config, args.home, args.flat, args.heartbeat, args.log_level.upper()
    )


def guard_stdout() -> int:
    """Point fd 1 and sys.stdout at stderr; the returned dup of the original fd 1 is
    the ACP writer's alone."""
    acp_fd = os.dup(1)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    return acp_fd


def configure_logging(level_name: str) -> None:
    """structlog and the standard library's logging (ACP Python's own), both to stderr."""
    import structlog

    level = logging.getLevelNamesMapping()[level_name]
    logging.basicConfig(
        stream=sys.stderr, level=level, format="%(levelname)s %(name)s: %(message)s"
    )
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


def main(argv: Sequence[str] | None = None) -> int:
    acp_fd = guard_stdout()
    options = parse_options(argv)
    # Everything of ours is imported only now, behind the stdout guard.
    from deep_reasoning.acp import texts
    from deep_reasoning.acp.agent import DrAcpAgent
    from deep_reasoning.acp.catalog import ConfigCatalog
    from deep_reasoning.acp.costs import PriceTable
    from deep_reasoning.acp.route import DirectRoute
    from deep_reasoning.acp.runlog import Home
    from deep_reasoning.acp.wire import ClientMode, Outbox, serve

    configure_logging(options.log_level)
    if options.config is None:
        sys.stderr.write(texts.NEEDS_CONFIG + "\n")
        return EXIT_USAGE
    home = Home.resolve(options.home)
    catalog, route, prices = (
        ConfigCatalog(options.config),
        DirectRoute(),
        PriceTable.load(home),
    )

    def make_agent(outbox: Outbox, client: ClientMode) -> DrAcpAgent:
        return DrAcpAgent(
            outbox,
            client,
            catalog=catalog,
            home=home,
            route=route,
            prices=prices,
            heartbeat_s=options.heartbeat_s,
        )

    asyncio.run(serve(make_agent, acp_out_fd=acp_fd, flat=options.flat))
    return 0
