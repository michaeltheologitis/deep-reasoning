"""Check's throwaway process (D4 §3.3): build one tool as make_tools does and report each
phase as a JSON line on the report fd, never on stdout, which the tool may print to.

python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN
"""

import argparse
import json
import os
import time
import traceback
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from deep_reasoner.config import build_client, load_cli_config
from deep_reasoner.primitives import Func
from deep_reasoner.v2.cli import V2Config
from deep_reasoner.v2.messages import func

from deep_reasoning.library.shapes import tool_file
from deep_reasoning.tools import texts
from deep_reasoning.tools._upstream_standin import (
    ToolBuildError,
    ToolImportFailed,
    ToolNotFunc,
    build_tool,
)
from deep_reasoning.tools.check import SHOWN_LIMIT

Say = Callable[..., None]


def _frames(exc: BaseException, path: Path, shown: str) -> str:
    """The traceback's frames in the tool's own file (named as shown), then the
    exception line; at most SHOWN_LIMIT characters, the end kept."""
    frames = [
        traceback.FrameSummary(shown, frame.lineno, frame.name, line=frame.line)
        for frame in traceback.extract_tb(exc.__traceback__)
        if Path(frame.filename).resolve() == path
    ]
    text = "".join(traceback.format_list(frames))
    return (text + "".join(traceback.format_exception_only(exc)))[-SHOWN_LIMIT:]


def _build(name: str, cfg: Any, say: Say) -> Func | None:
    """The tool, as make_tools builds it; None when it failed, each way told apart (§8.1)."""
    block = cfg.tools[name]
    path = (Path(cfg.config_path).parent / block["factory_from"]).resolve()
    try:
        return build_tool(name, block, build_client(cfg.client), cfg.config_path)
    except ToolImportFailed as exc:
        if isinstance(exc.__cause__, ImportError):
            say("failed", outcome="import_failed", message=str(exc))
        else:
            shown = _frames(exc.__cause__, path, tool_file(name))
            say("failed", outcome="raised", message=str(exc), traceback=shown)
    except ToolNotFunc as exc:
        say("failed", outcome="not_func", message=str(exc))
    except ToolBuildError as exc:
        say("failed", outcome="bad_factory", message=str(exc))
    except Exception as exc:  # noqa: BLE001 -- whatever the tool raises is the report
        factory = block.get("factory", name)
        message = texts.factory_raised(name, factory, type(exc).__name__, str(exc))
        shown = _frames(exc, path, tool_file(name))
        say("failed", outcome="raised", message=message, traceback=shown)
    return None


def _try(expression: str, name: str, value: Any) -> dict[str, Any]:
    """The expression evaluated with the tool bound under its name."""
    started = time.monotonic()
    try:
        result = eval(compile(expression, "<try>", "eval"), {name: value})
    except Exception as exc:  # noqa: BLE001 -- whatever the expression raises is shown
        error = f"{type(exc).__name__}: {exc}"[:SHOWN_LIMIT]
        seconds = time.monotonic() - started
        return {"ok": False, "value": None, "error": error, "seconds": seconds}
    seconds = time.monotonic() - started
    value_shown = repr(result)[:SHOWN_LIMIT]
    return {"ok": True, "value": value_shown, "error": None, "seconds": seconds}


def main(argv: Sequence[str] | None = None) -> int:
    """python -m deep_reasoning.tools.check_child --report-fd N --name NAME [--example EXPR] MAIN
    Writes §3.3's JSON lines to fd N; prints nothing of its own to stdout."""
    parser = argparse.ArgumentParser(prog="python -m deep_reasoning.tools.check_child")
    parser.add_argument("--report-fd", type=int, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--example")
    parser.add_argument("main")
    args = parser.parse_args(argv)
    report = os.fdopen(args.report_fd, "w", encoding="utf-8")

    def say(phase: str, **fields: Any) -> None:
        report.write(json.dumps({"phase": phase, **fields}) + "\n")
        report.flush()

    say("ready")
    cfg = load_cli_config(args.main, schema=V2Config)
    started = time.monotonic()
    built = _build(args.name, cfg, say)
    if built is None:
        return 0
    told = func(args.name, built.value, built.description).describe()
    say("built", told=told, seconds=time.monotonic() - started)
    if args.example is not None:
        say("example", **_try(args.example, args.name, built.value))
    say("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
