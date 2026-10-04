"""Check (D4 §3): will this tool build when a conversation starts, and what will the agent
be told? A static stage in the backend, then a throwaway process that builds the tool as
make_tools does, without secrets or a model, under time limits."""

import contextlib
import json
import os
import pwd
import queue
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from deep_reasoner.tools.base import TOOL_BUILDERS
from pydantic import BaseModel

from deep_reasoning.library import shapes
from deep_reasoning.library.library import Library
from deep_reasoning.library.records import (
    FieldError,
    LibraryBadRequest,
    LibraryError,
    LibraryRefused,
    LibraryValidationError,
)
from deep_reasoning.mcp.grants import is_mcp_tool
from deep_reasoning.mcp.wire import MCP_FACTORY
from deep_reasoning.tools import texts
from deep_reasoning.tools._upstream_standin import UnknownToolFactory

Outcome = Literal[
    "built",
    "builtin",
    "invalid",
    "syntax",
    "import_failed",
    "bad_factory",
    "not_func",
    "raised",
    "timeout",
    "unavailable",
]
OK_OUTCOMES: Final = frozenset({"built", "builtin"})
SAVE_ANYWAY_OUTCOMES: Final = frozenset({"raised", "timeout", "unavailable"})
RESERVED_NAMES: Final = frozenset(
    {"FinalAnswer", "Func", "Var", "run_all", "subagent", "task"}
)
CHECK_MODEL_URL: Final = "http://127.0.0.1:9/v1"
PASSED_ENV: Final = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "TZ")
# Characters of printed output, tracebacks and example values a report carries.
SHOWN_LIMIT: Final = 2_000
CHILD: Final = "deep_reasoning.tools.check_child"


@dataclass(frozen=True)
class CheckLimits:
    ready_s: float = 30.0  # the throwaway process imports deep_reasoner
    build_s: float = 10.0  # the tool's file is imported and its factory called
    example_s: float = 10.0  # the tried expression


DEFAULT_LIMITS: Final = CheckLimits()


class ExampleResult(BaseModel):
    expression: str
    ok: bool
    value: str | None  # repr of the result, at most SHOWN_LIMIT characters
    error: str | None  # "TypeName: message"
    seconds: float


class CheckReport(BaseModel):
    ok: bool
    outcome: Outcome
    message: str
    told: str | None  # deep_reasoner's func(name, value, description).describe()
    traceback: (
        str | None
    )  # raised: the frames in tools/<name>.py and the exception line
    example: ExampleResult | None
    printed: str  # the last SHOWN_LIMIT characters the tool printed
    seconds: float | None  # loading the file and calling the factory
    deep_reasoner: str  # the build that checked it
    can_save: bool
    can_save_anyway: bool


def tool_name_errors(name: str) -> list[FieldError]:
    """RESERVED_NAME for a name in RESERVED_NAMES; D2's TOOL_NAME rule is shapes.validate_tool's."""
    if name in RESERVED_NAMES:
        return [FieldError(loc="name", msg=texts.reserved_name(name))]
    return []


def check_env(base: Mapping[str, str]) -> dict[str, str]:
    """PASSED_ENV from base; HOME, USER and LOGNAME from the password database;
    PYTHONUNBUFFERED=1 and PYTHONDONTWRITEBYTECODE=1. Nothing else."""
    user = pwd.getpwuid(os.getuid())
    return {name: base[name] for name in PASSED_ENV if name in base} | {
        "HOME": user.pw_dir,
        "USER": user.pw_name,
        "LOGNAME": user.pw_name,
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _report(
    outcome: Outcome,
    message: str,
    *,
    told: str | None = None,
    traceback: str | None = None,
    example: ExampleResult | None = None,
    printed: str = "",
    seconds: float | None = None,
) -> CheckReport:
    return CheckReport(
        ok=outcome in OK_OUTCOMES,
        outcome=outcome,
        message=message,
        told=told,
        traceback=traceback,
        example=example,
        printed=printed,
        seconds=seconds,
        deep_reasoner=shapes.deep_reasoner_build(),
        can_save=outcome in OK_OUTCOMES,
        can_save_anyway=outcome in SAVE_ANYWAY_OUTCOMES,
    )


class _Reports:
    """The child's report lines, read on a thread so that each can be awaited with a
    deadline. get() returns a line, None at the end, or raises queue.Empty."""

    def __init__(self, fd: int) -> None:
        self._lines: queue.Queue[dict[str, Any] | None] = queue.Queue()
        threading.Thread(target=self._read, args=(fd,), daemon=True).start()

    def _read(self, fd: int) -> None:
        with os.fdopen(fd, "rb") as stream:
            for line in stream:
                with contextlib.suppress(ValueError):
                    self._lines.put(json.loads(line))
        self._lines.put(None)

    def get(self, phases: set[str], seconds: float) -> dict[str, Any] | None:
        """The next line of one of these phases, or None when the child closed its end."""
        deadline = time.monotonic() + seconds
        while True:
            line = self._lines.get(timeout=max(0.0, deadline - time.monotonic()))
            if line is None or line.get("phase") in phases:
                return line


def _how(code: int) -> str:
    return f"signal {-code}" if code < 0 else f"exit code {code}"


def _tail(path: Path) -> str:
    """The last SHOWN_LIMIT characters of what the tool printed."""
    with path.open("rb") as printed:
        printed.seek(max(0, path.stat().st_size - 4 * SHOWN_LIMIT))
        return printed.read().decode(errors="replace")[-SHOWN_LIMIT:]


def _end(child: subprocess.Popen[bytes]) -> int:
    """SIGKILL the child's group before reaping it (so its pid, the group's id, cannot
    have been reused), then its exit code."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(child.pid, signal.SIGKILL)
    return child.wait()


def _follow(
    name: str,
    reports: _Reports,
    child: subprocess.Popen[bytes],
    example: str | None,
    limits: CheckLimits,
) -> dict[str, Any]:
    """The report's fields from the child's lines, each phase under its limit; the
    child's group is ended before this returns."""
    try:
        ready = reports.get({"ready"}, limits.ready_s)
    except queue.Empty:
        _end(child)
        return {
            "outcome": "unavailable",
            "message": texts.ready_timeout(limits.ready_s),
        }
    if ready is None:
        ended = _how(_end(child))
        return {
            "outcome": "unavailable",
            "message": texts.child_ended(name, ended, "starting"),
        }
    try:
        line = reports.get({"built", "failed"}, limits.build_s)
    except queue.Empty:
        _end(child)
        return {
            "outcome": "timeout",
            "message": texts.build_timeout(name, limits.build_s),
        }
    if line is None:
        ended = _how(_end(child))
        return {
            "outcome": "raised",
            "message": texts.child_ended(name, ended, "building the tool"),
        }
    if line["phase"] == "failed":
        _end(child)
        return {k: line.get(k) for k in ("outcome", "message", "traceback")}
    built = {
        "outcome": "built",
        "message": texts.BUILT,
        "told": line["told"],
        "seconds": line["seconds"],
    }
    if example is None:
        _end(child)
        return built
    try:
        tried = reports.get({"example"}, limits.example_s)
        error = None
    except queue.Empty:
        tried, error = None, texts.example_timeout(limits.example_s)
    ended = _how(_end(child))
    if tried is None:
        error = error or texts.child_ended(name, ended, "trying it")
        tried = {
            "ok": False,
            "value": None,
            "error": error,
            "seconds": limits.example_s,
        }
    fields = {k: tried[k] for k in ("ok", "value", "error", "seconds")}
    return built | {"example": ExampleResult(expression=example, **fields)}


def _argv(name: str, main: Path, report_fd: int, example: str | None) -> Sequence[str]:
    tried = ("--example", example) if example is not None else ()
    return [
        sys.executable,
        "-m",
        CHILD,
        "--report-fd",
        str(report_fd),
        "--name",
        name,
        *tried,
        str(main),
    ]


def _build_in_a_child(
    name: str,
    block: Mapping[str, Any],
    source: str,
    example: str | None,
    limits: CheckLimits,
) -> CheckReport:
    """§3.3: a one-tool config in a 0700 folder, built by check_child in its own group."""
    folder = Path(tempfile.mkdtemp(prefix="dr-check-"))
    try:
        config = folder / "config"
        (config / shapes.TOOL_DIR).mkdir(parents=True)
        (config / shapes.tool_file(name)).write_bytes(source.encode())
        main = {
            "client": {"base_url": CHECK_MODEL_URL, "max_retries": 0},
            "tools": {name: dict(block)},
        }
        (config / "main.yaml").write_text(shapes.canonical_yaml(main))
        printed = folder / "printed.txt"
        read_fd, write_fd = os.pipe()
        with printed.open("wb") as out:
            try:
                child = subprocess.Popen(
                    _argv(name, config / "main.yaml", write_fd, example),
                    cwd=config,
                    env=check_env(os.environ),
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=out,
                    pass_fds=(write_fd,),
                    start_new_session=True,
                )
            except OSError as exc:
                os.close(read_fd)
                how = f"{type(exc).__name__}: {exc}"
                return _report("unavailable", texts.child_ended(name, how, "starting"))
            finally:
                os.close(write_fd)
        fields = _follow(name, _Reports(read_fd), child, example, limits)
        return _report(**fields, printed=_tail(printed))
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def check_tool(
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    example: str | None = None,
    limits: CheckLimits = DEFAULT_LIMITS,
) -> CheckReport:
    """§3.2's static stage, then §3.3's throwaway process under limits; never raises for
    anything the tool does.

    shape (D2's validate_tool) → invalid; a reserved name → invalid; an MCP grant's block →
    invalid; no source: a built-in factory → builtin, else bad_factory; a SyntaxError →
    syntax. Otherwise materialize a one-tool config in a 0700 temporary folder, run
    check_child in its own process group with check_env, read its report lines against
    the limits, kill the group, remove the folder.
    """
    try:
        shaped = shapes.validate_tool(name, yaml_text, source)
    except LibraryValidationError as exc:
        return _report("invalid", str(exc))
    if errors := tool_name_errors(name):
        return _report("invalid", errors[0].msg)
    factory = shaped.data.get("factory", name)
    if factory == MCP_FACTORY:
        return _report("invalid", texts.mcp_via_grant(name))
    if source is None:
        if factory == "llm" or factory in TOOL_BUILDERS:
            return _report("builtin", texts.builtin(factory))
        return _report("bad_factory", str(UnknownToolFactory(factory, name)))
    try:
        compile(source, shapes.tool_file(name), "exec")
    except SyntaxError as exc:
        return _report("syntax", texts.syntax(name, exc.lineno, exc.msg))
    return _build_in_a_child(name, shaped.data, source, example, limits)


class ToolCheckFailed(LibraryError):
    code = "check_failed"
    status = 422

    def __init__(self, name: str, report: CheckReport) -> None:
        super().__init__(texts.check_failed(name))
        self.report = report

    def payload(self) -> dict[str, Any]:
        """{"error", "message", "check": report.model_dump(mode="json")}."""
        return {**super().payload(), "check": self.report.model_dump(mode="json")}


def require_check(
    library: Library,
    name: str,
    yaml_text: str,
    source: str | None,
    *,
    accept_failure: bool,
) -> None:
    """§3.5: returns when the PUT may proceed; raises ToolCheckFailed, LibraryBadRequest
    or LibraryRefused.

    YAML D2 refuses → return (put_tool raises D2's 422); an MCP grant's block → 400; a
    head that is an MCP grant → 409; canonical block and source equal the head's →
    return; otherwise check_tool, and refuse unless it can be saved (or saved anyway,
    when asked).
    """
    try:
        shaped = shapes.validate_tool(name, yaml_text, source)
    except LibraryValidationError:
        return
    if shaped.data.get("factory", name) == MCP_FACTORY:
        raise LibraryBadRequest(texts.mcp_via_grant(name))
    head = library.state().tools.get(name)
    if head is not None and is_mcp_tool(head):
        raise LibraryRefused(texts.mcp_via_grant(name))
    if head is not None and (head.yaml, head.source) == (shaped.yaml, source):
        return
    report = check_tool(name, yaml_text, source)
    if report.can_save or (report.can_save_anyway and accept_failure):
        return
    raise ToolCheckFailed(name, report)
