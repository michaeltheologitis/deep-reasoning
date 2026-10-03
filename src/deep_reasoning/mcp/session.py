"""The worker's side of MCP (D4 §4.4): connect the granted, reachable servers a run's
config names, all at once, before build_reasoner; install shim.SESSION."""

import codecs
import os
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, TextIO

from deep_reasoner.namespaces import (
    ROOT,
    NamespaceRegistry,
    NamespaceSpawnError,
    check_spawn,
    load_namespaces_from_dir,
)
from deep_reasoner.v2.cli import V2Config, build_namespace_registry
from deep_reasoner.v2.messages import func

from deep_reasoning.mcp import shim
from deep_reasoning.mcp.wire import (
    MCP_FACTORY,
    McpServerSpec,
    McpServerStatus,
    redact,
)

GRANTED_NOWHERE: Final = "granted to no namespace"
OUT_OF_REACH: Final = "granted only where this conversation cannot spawn"
LOG_TAIL: Final = 300  # characters of a failed server's own output in its status
PRINTED: Final = '{failure}; it printed: "{tail}"'
PIPE_READ: Final = 65_536  # bytes of a server's stderr read at a time
DRAIN_S: Final = 2.0  # a failed server's last output reaches its log within this


def _names(cfg: V2Config) -> list[str]:
    """Root, then every namespace of namespaces_dir and of cfg.namespaces."""
    found = load_namespaces_from_dir(cfg.namespaces_dir) if cfg.namespaces_dir else []
    return list(dict.fromkeys([ROOT, *(ns.name for ns in found), *cfg.namespaces]))


def reachable(
    registry: NamespaceRegistry, start: str, names: Sequence[str]
) -> set[str]:
    """The closure of {start} under deep_reasoner's check_spawn."""
    reached, frontier = {start}, [start]
    while frontier:
        src = frontier.pop()
        for dst in names:
            if dst in reached:
                continue
            try:
                check_spawn(registry, src, dst)
            except NamespaceSpawnError:
                continue
            reached.add(dst)
            frontier.append(dst)
    return reached


def _grants(
    cfg: V2Config, aliases: Sequence[str]
) -> tuple[dict[str, list[str]], set[str]]:
    """Each alias's granted namespaces (deep_reasoner's own resolution), and the
    namespaces this conversation's agents can reach."""
    names = _names(cfg)
    registry = build_namespace_registry(cfg)
    try:
        granted = {
            alias: [ns for ns in names if alias in registry.resolve(ns).tools]
            for alias in aliases
        }
        return granted, reachable(registry, cfg.entry_namespace, names)
    finally:
        registry.close()


def _shim_spec(spec: McpServerSpec) -> shim.ServerSpec:
    return shim.ServerSpec(
        name=spec.name,
        transport=spec.transport,
        command=spec.command,
        args=tuple(spec.args),
        env=dict(spec.env),
        url=spec.url,
        headers=dict(spec.headers),
    )


def _secrets(spec: McpServerSpec) -> list[str]:
    return [*spec.env.values(), *spec.headers.values()]


def _failed_detail(failure: str, log: Path, spec: McpServerSpec) -> str:
    """The failure and the tail of what the server printed, every secret of its spec
    redacted."""
    tail = log.read_text(errors="replace").strip()[-LOG_TAIL:]
    detail = PRINTED.format(failure=failure, tail=tail) if tail else failure
    return redact(detail, _secrets(spec))


def _copy_redacted(source: int, log: TextIO, secrets: list[str]) -> None:
    """What a server prints, from its pipe to its log with every secret redacted. A
    secret can arrive split over two reads, so each read's last characters wait for the
    next."""
    held = max((len(secret) for secret in secrets), default=1) - 1
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    pending = ""
    with open(source, "rb", buffering=0) as pipe, log:
        while chunk := pipe.read(PIPE_READ):
            pending = redact(pending + decoder.decode(chunk), secrets)
            cut = max(0, len(pending) - held)
            log.write(pending[:cut])
            log.flush()
            pending = pending[cut:]
        log.write(redact(pending + decoder.decode(b"", final=True), secrets))


class _Started:
    """A connection open_session started, and what deciding it needs. The server's
    stderr is a pipe that a thread copies into its log, redacted."""

    def __init__(
        self, alias: str, spec: McpServerSpec, block: dict[str, Any], log: Path
    ):
        self.spec, self.log = spec, log
        self.timeout = float(block.get("connect_timeout_s", shim.CONNECT_TIMEOUT_S))
        out = log.open("w", encoding="utf-8")
        source, sink = os.pipe()
        self.copier = threading.Thread(
            target=_copy_redacted,
            args=(source, out, _secrets(spec)),
            name=f"mcp-{alias}-log",
            daemon=True,
        )
        self.copier.start()
        # Closed in _decide once the server holds its own end; an abandoned connection's
        # is closed when the connection is collected, which its running task prevents.
        self.errlog = os.fdopen(sink, "w")
        self.connection = shim.Connection(
            _shim_spec(spec),
            name=alias,
            errlog=self.errlog,
            call_timeout_s=float(block.get("call_timeout_s", shim.CALL_TIMEOUT_S)),
        )
        self.connection.start()


def _decide(
    alias: str, started: _Started, granted: list[str], answered: float | None
) -> tuple[dict[str, Any], Any]:
    """The status's fields and the binding, once the server answered (after answered
    seconds) or its time is up (None)."""
    connection = started.connection
    if answered is not None:
        started.errlog.close()  # the connection has started its server, or never will
    if answered is not None and connection.failure is None:
        binding = shim.bound(alias, connection, granted=frozenset(granted))
        told = func(alias, binding.value, binding.description).describe()
        fields = {"state": "bound", "seconds": answered, "count": len(connection.tools)}
        return fields | {"told": told}, binding
    if answered is not None:
        started.copier.join(DRAIN_S)
        detail = _failed_detail(connection.failure, started.log, started.spec)
        reason = shim.COULD_NOT_START.format(detail=detail)
        return {"state": "failed", "detail": detail}, shim.unavailable(alias, reason)
    connection.abandon()
    reason = shim.NO_ANSWER.format(seconds=started.timeout)
    fields = {"state": "no_answer", "seconds": started.timeout}
    return fields, shim.unavailable(alias, reason)


def open_session(
    cfg: V2Config,
    specs: Sequence[McpServerSpec],
    *,
    run_dir: Path,
) -> list[McpServerStatus]:
    """§4.4: connect the granted, reachable servers at once under one deadline, install
    shim.SESSION for every MCP block, and return one status per block."""
    blocks = {
        alias: block
        for alias, block in cfg.tools.items()
        if block.get("factory") == MCP_FACTORY
    }
    if not blocks:
        shim.SESSION = {}
        return []
    granted, reach = _grants(cfg, list(blocks))
    forwarded = {spec.name: spec for spec in specs}
    statuses: dict[str, McpServerStatus] = {}
    session: dict[str, Any] = {}
    started: dict[str, _Started] = {}
    begun = time.monotonic()
    for alias, block in blocks.items():
        statuses[alias] = McpServerStatus(
            tool=alias,
            server=block["server"],
            transport=block.get("transport"),
            state="skipped",
            granted=granted[alias],
        )
        if not reach & set(granted[alias]):
            detail = OUT_OF_REACH if granted[alias] else GRANTED_NOWHERE
            statuses[alias].detail = detail
            session[alias] = shim.unavailable(alias, shim.NOT_REACHED)
        elif block["server"] not in forwarded:
            statuses[alias].state = "not_enabled"
            session[alias] = shim.unavailable(alias, shim.NOT_ENABLED)
        else:
            log = run_dir / f"mcp-{alias}.log"
            started[alias] = _Started(alias, forwarded[block["server"]], block, log)
    # Every server was started above; each wait costs only what is left of its time.
    for alias, server in started.items():
        left = begun + server.timeout - time.monotonic()
        ready = server.connection.wait_ready(left)
        answered = round(time.monotonic() - begun, 3) if ready else None
        fields, session[alias] = _decide(alias, server, granted[alias], answered)
        statuses[alias] = statuses[alias].model_copy(update=fields)
    shim.SESSION = session
    return [statuses[alias] for alias in blocks]
