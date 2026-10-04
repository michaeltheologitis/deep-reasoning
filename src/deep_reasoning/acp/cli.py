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

# proxy.DEFAULT_SPEND_CAP_USD, which imports too much for here; test_cli pins it.
DEFAULT_SPEND_CAP_USD = 5.0
PROXY_STOP_S = 0.5  # inside D1's shutdown budget


@dataclass(frozen=True)
class Options:
    config: Path | None  # --config PATH: a plain dr main.yaml; else the Library
    home: (
        Path | None
    )  # --home DIR, else $DR_HOME, else ~/.deep-reasoning (Home.resolve)
    flat: bool  # --flat: never send sub-agent sessions, whatever the client advertises
    heartbeat_s: float  # --heartbeat SECONDS, default 60
    log_level: str  # --log-level, default WARNING
    key_proxy: (
        bool  # --no-key-proxy: D1's DirectRoute, keys stay in the worker's environment
    )
    spend_cap_usd: (
        float  # --spend-cap-usd USD: per conversation, through the key proxy; default 5
    )


def parse_options(argv: Sequence[str] | None) -> Options:
    parser = argparse.ArgumentParser(prog="dr-acp", description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="a plain dr main.yaml (default: the Library at --home)",
    )
    parser.add_argument(
        "--home", type=Path, help="run logs and sessions (default $DR_HOME)"
    )
    parser.add_argument(
        "--flat", action="store_true", help="never send sub-agent sessions"
    )
    parser.add_argument("--heartbeat", type=float, default=60.0, metavar="SECONDS")
    parser.add_argument("--log-level", default="WARNING")
    parser.add_argument(
        "--no-key-proxy",
        action="store_true",
        help="give the worker the provider keys themselves (debugging)",
    )
    parser.add_argument(
        "--spend-cap-usd",
        type=float,
        default=DEFAULT_SPEND_CAP_USD,
        metavar="USD",
        help="what one conversation may spend through the key proxy (default 5)",
    )
    args = parser.parse_args(argv)
    return Options(
        args.config,
        args.home,
        args.flat,
        args.heartbeat,
        args.log_level.upper(),
        not args.no_key_proxy,
        args.spend_cap_usd,
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
    from deep_reasoning.acp.agent import DrAcpAgent
    from deep_reasoning.acp.catalog import ConfigCatalog
    from deep_reasoning.acp.costs import PriceTable
    from deep_reasoning.acp.proxy import KeyProxy, ProxyRoute, SpendLedger
    from deep_reasoning.acp.route import DirectRoute, ModelRoute
    from deep_reasoning.acp.runlog import Home
    from deep_reasoning.acp.wire import ClientMode, Outbox, serve
    from deep_reasoning.library.catalog import LibraryCatalog, library_path

    configure_logging(options.log_level)
    home = Home.resolve(options.home)
    catalog = (
        ConfigCatalog(options.config)
        if options.config is not None
        else LibraryCatalog(library_path(options.home))
    )
    prices = PriceTable.load(home)
    proxy = None
    route: ModelRoute = DirectRoute()
    if options.key_proxy:
        ledger = SpendLedger(home, options.spend_cap_usd)
        proxy = KeyProxy(ledger=ledger, prices=prices, home=home)
        route = ProxyRoute(proxy, os.environ)

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

    try:
        asyncio.run(serve(make_agent, acp_out_fd=acp_fd, flat=options.flat))
    finally:
        if proxy is not None:
            proxy.stop(PROXY_STOP_S)
    return 0
