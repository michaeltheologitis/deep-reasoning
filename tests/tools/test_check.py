"""Check (D4 §3, E9): a tool is built as a conversation builds it, in a throwaway process
without secrets or a model, and each way it can fail is told apart in deep_reasoner's own
words where it has them."""

import asyncio
import json
import os
import pwd
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml
from deep_reasoner.config import build_client, load_cli_config
from deep_reasoner.tools.base import TOOL_BUILDERS
from deep_reasoner.v2.cli import V2Config, make_tools

from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from deep_reasoning.library import shapes
from deep_reasoning.tools import check, texts
from deep_reasoning.tools.check import (
    CHECK_MODEL_URL,
    DEFAULT_LIMITS,
    RESERVED_NAMES,
    CheckLimits,
    ExampleResult,
    check_env,
    check_tool,
)
from tests.processes import running_after

FIXTURES = Path(__file__).parent / "fixtures"
QUICK = CheckLimits(build_s=3, example_s=3)
SYNTAX_ERROR = "def make(\n"
MAKE_TOOLS = """
import json, sys
from deep_reasoner.config import build_client, load_cli_config
from deep_reasoner.v2.cli import V2Config, make_tools
cfg = load_cli_config(sys.argv[1], schema=V2Config)
try:
    make_tools(cfg, build_client(cfg.client))
except Exception as exc:
    print(json.dumps({"ok": False, "message": str(exc)}))
else:
    print(json.dumps({"ok": True}))
"""
MAKE_TOOLS_LIMIT_S = 15


def source(fixture: str) -> str:
    return (FIXTURES / f"{fixture}.py").read_text()


def materialized(tmp_path: Path, name: str, block: str, source_text: str) -> Path:
    """The one-tool config Check builds from, as D2 materializes a tool: main.yaml and
    tools/<name>.py."""
    config = tmp_path / "config"
    (config / "tools").mkdir(parents=True)
    (config / "tools" / f"{name}.py").write_text(source_text)
    main = {
        "client": {"base_url": CHECK_MODEL_URL, "max_retries": 0},
        "tools": {name: {**yaml.safe_load(block), "factory_from": f"tools/{name}.py"}},
    }
    (config / "main.yaml").write_text(yaml.safe_dump(main))
    return config


def make_tools_in_a_subprocess(config: Path) -> dict:
    """deep_reasoner's own make_tools on the config, in its folder; {"ok": False} when it
    does not return within MAKE_TOOLS_LIMIT_S or ends its process."""
    process = subprocess.Popen(
        [sys.executable, "-c", MAKE_TOOLS, str(config / "main.yaml")],
        cwd=config,
        env=check_env(os.environ),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        text=True,
    )
    try:
        out, _ = process.communicate(timeout=MAKE_TOOLS_LIMIT_S)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        return {"ok": False, "message": None}
    lines = out.strip().splitlines()
    return json.loads(lines[-1]) if lines else {"ok": False, "message": None}


@pytest.fixture
def no_process(monkeypatch):
    """Any attempt to start Check's process fails the test."""

    def refuse(*args, **kwargs):
        raise AssertionError("Check started a process")

    monkeypatch.setattr(check.subprocess, "Popen", refuse)


def test_a_working_tool_builds_and_says_what_the_agent_is_told():
    report = check_tool("word_count", "factory: make", source("word_count"))
    assert (report.ok, report.outcome, report.can_save, report.can_save_anyway) == (
        True,
        "built",
        True,
        False,
    )
    assert report.message == texts.BUILT
    assert report.told == (
        "- `word_count(text: str) -> int`\n"
        "  word_count(text) -> int: number of words in text."
    )
    assert 0 <= report.seconds < DEFAULT_LIMITS.build_s
    assert report.deep_reasoner == shapes.deep_reasoner_build()
    assert (report.example, report.traceback, report.printed) == (None, None, "")


def test_the_tried_expression_is_evaluated_with_the_tool_bound():
    report = check_tool(
        "word_count",
        "factory: make",
        source("word_count"),
        example='word_count("one two three")',
    )
    assert report.example == ExampleResult(
        expression='word_count("one two three")',
        ok=True,
        value="3",
        error=None,
        seconds=report.example.seconds,
    )


def test_a_factory_that_returns_no_func_fails_check_in_deep_reasoners_words():
    report = check_tool("word_count", "factory: make", source("not_func"))
    assert (report.ok, report.outcome, report.can_save, report.can_save_anyway) == (
        False,
        "not_func",
        False,
        False,
    )
    assert report.message == texts.not_func(
        "word_count", "make", "tools/word_count.py", "function"
    )


def test_a_misspelled_factory_fails_check_naming_what_the_file_defines():
    report = check_tool("word_count", "factory: mkae", source("word_count"))
    assert (report.outcome, report.can_save, report.can_save_anyway) == (
        "bad_factory",
        False,
        False,
    )
    assert report.message == (
        "tool 'word_count': 'tools/word_count.py' defines no 'mkae'.\n"
        "  It defines: make, make_broken.\n"
        "  Known built-in factories: claude_code, kg, llm, rag, safe_url."
    )


def test_an_import_of_a_missing_module_fails_check_and_cannot_be_saved_anyway():
    report = check_tool("word_count", "factory: make", source("import_error"))
    assert (report.outcome, report.can_save, report.can_save_anyway) == (
        "import_failed",
        False,
        False,
    )
    assert report.message == (
        "tool 'word_count': importing 'tools/word_count.py' raised "
        "ModuleNotFoundError: No module named 'yaml_x'"
    )


def test_a_hanging_factory_is_stopped_at_the_build_limit():
    started = time.monotonic()
    check_tool("word_count", "factory: make", source("word_count"))
    ready_and_built = time.monotonic() - started

    started = time.monotonic()
    report = check_tool("word_count", "factory: make", source("hang"))
    took = time.monotonic() - started

    assert (report.ok, report.outcome, report.can_save_anyway) == (
        False,
        "timeout",
        True,
    )
    assert report.message == texts.build_timeout("word_count", DEFAULT_LIMITS.build_s)
    assert DEFAULT_LIMITS.build_s <= took < ready_and_built + DEFAULT_LIMITS.build_s + 1


def test_nothing_a_stopped_tool_started_is_left_running(tmp_path):
    pid_file = tmp_path / "pid"
    block = f"factory: make\npid_file: {pid_file}\n"
    report = check_tool("spawner", block, source("spawns"), limits=QUICK)
    assert report.outcome == "timeout"
    assert running_after([int(pid_file.read_text())], 1) == []


@pytest.mark.parametrize(
    ("fixture", "block", "worded"),
    [
        ("word_count", "factory: make", False),
        ("not_func", "factory: make", True),
        ("word_count", "factory: mkae", True),
        ("import_error", "factory: make", True),
        ("hang", "factory: make", False),
        ("env_at_build", "factory: make", False),
        ("prints", "factory: make", False),
        ("exits", "factory: make", False),
    ],
    ids=[
        "works",
        "not_func",
        "misspelled",
        "import_error",
        "hang",
        "env_at_build",
        "prints",
        "exits",
    ],
)
def test_check_and_make_tools_agree(tmp_path, fixture, block, worded):
    report = check_tool("word_count", block, source(fixture), limits=QUICK)
    built = make_tools_in_a_subprocess(
        materialized(tmp_path, "word_count", block, source(fixture))
    )
    assert report.ok == built["ok"]
    if worded:
        assert report.message == built["message"]


def test_a_syntax_error_fails_before_any_process_starts(no_process):
    report = check_tool("word_count", "factory: make", SYNTAX_ERROR)
    assert (report.outcome, report.can_save, report.can_save_anyway) == (
        "syntax",
        False,
        False,
    )
    assert (
        report.message
        == "tool 'word_count': tools/word_count.py line 1: '(' was never closed"
    )
    assert report.seconds is None


@pytest.mark.parametrize("name", sorted(RESERVED_NAMES))
def test_a_reserved_name_is_invalid(no_process, name):
    report = check_tool(name, "factory: make", source("word_count"))
    assert (report.outcome, report.can_save, report.message) == (
        "invalid",
        False,
        texts.reserved_name(name),
    )


def test_a_name_d2_refuses_is_invalid_in_d2s_words(no_process):
    report = check_tool("word count", "factory: make", source("word_count"))
    assert report.outcome == "invalid"
    assert report.message.startswith(
        "'word count' is not a valid deep_reasoner tool:\n  name: 'word count' is not a tool name"
    )


def test_llm_is_not_reserved():
    report = check_tool("llm", "factory: make", source("word_count"))
    assert (report.outcome, report.can_save) == ("built", True)


@pytest.mark.parametrize(
    ("name", "block", "factory"),
    [
        ("rag", "factory: rag\nindex: notes\n", "rag"),
        ("kg", "{}", "kg"),
        ("ask", "factory: llm", "llm"),
    ],
)
def test_a_built_in_factory_is_named_not_built(no_process, name, block, factory):
    report = check_tool(name, block, None)
    assert (report.ok, report.outcome, report.message, report.can_save) == (
        True,
        "builtin",
        texts.builtin(factory),
        True,
    )


def test_an_unknown_built_in_factory_is_refused_in_deep_reasoners_words(no_process):
    report = check_tool("notes", "factory: ragg", None)
    assert (report.outcome, report.can_save, report.can_save_anyway) == (
        "bad_factory",
        False,
        False,
    )
    assert report.message == texts.unknown_factory("ragg", "notes", TOOL_BUILDERS)


def test_an_mcp_grant_is_not_checked_as_a_tool_of_your_own(no_process):
    report = check_tool("github", "factory: mcp_server\nserver: github\n", "# shim")
    assert (report.outcome, report.message) == (
        "invalid",
        texts.mcp_via_grant("github"),
    )


def test_a_factory_raising_can_be_saved_anyway():
    report = check_tool("word_count", "factory: make", source("env_at_build"))
    assert (report.ok, report.outcome, report.can_save, report.can_save_anyway) == (
        False,
        "raised",
        False,
        True,
    )
    assert report.message == "tool 'word_count': make raised KeyError: 'D4_TOKEN'"
    assert report.traceback == (
        '  File "tools/word_count.py", line 7, in make\n'
        '    token = os.environ["D4_TOKEN"]\n'
        "KeyError: 'D4_TOKEN'\n"
    )


def test_a_tool_that_ends_the_process_is_raised_saying_how_it_ended():
    report = check_tool("word_count", "factory: make", source("exits"))
    assert (report.outcome, report.can_save_anyway) == ("raised", True)
    assert report.message == texts.child_ended(
        "word_count", "exit code 3", "building the tool"
    )


def test_a_check_that_cannot_start_deep_reasoner_in_time_is_unavailable():
    limits = CheckLimits(ready_s=0.01)
    report = check_tool(
        "word_count", "factory: make", source("word_count"), limits=limits
    )
    assert (report.outcome, report.message, report.can_save_anyway) == (
        "unavailable",
        texts.ready_timeout(0.01),
        True,
    )


def test_check_never_reaches_a_model(monkeypatch):
    async def body():
        async with FakeOpenAI(lambda messages: "the fake model answered") as model:
            monkeypatch.setenv("OPENAI_BASE_URL", model.base_url)
            monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
            report = await asyncio.to_thread(
                check_tool, "asks", "factory: make", source("calls_model")
            )
            return report, model.calls

    report, calls = asyncio.run(body())
    assert report.outcome == "built"
    assert "APIConnectionError" in report.told
    assert calls == []


def test_check_gets_no_secret():
    base = {
        "PATH": "/usr/bin",
        "LANG": "C.UTF-8",
        "TZ": "UTC",
        "OPENAI_API_KEY": "sk-secret",
        "OH_SECRET_KEY": "oh-secret",
        "DR_HOME": "/home/me/.deep-reasoning",
        "HOME": "/elsewhere",
    }
    user = pwd.getpwuid(os.getuid())
    assert check_env(base) == {
        "PATH": "/usr/bin",
        "LANG": "C.UTF-8",
        "TZ": "UTC",
        "HOME": user.pw_dir,
        "USER": user.pw_name,
        "LOGNAME": user.pw_name,
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def test_printing_cannot_corrupt_the_report():
    report = check_tool("word_count", "factory: make", source("prints"))
    assert report.outcome == "built"
    assert report.printed.endswith("x\nthe end of what the tool printed\n")
    assert len(report.printed) == check.SHOWN_LIMIT


def test_an_example_that_raises_is_reported_and_the_build_stays_ok():
    report = check_tool(
        "word_count", "factory: make", source("word_count"), example="word_count(3)"
    )
    assert (report.ok, report.outcome) == (True, "built")
    assert (report.example.ok, report.example.value, report.example.error) == (
        False,
        None,
        "AttributeError: 'int' object has no attribute 'split'",
    )


def test_a_slow_example_is_stopped_at_its_limit():
    limits = CheckLimits(example_s=1)
    report = check_tool(
        "word_count",
        "factory: make",
        source("word_count"),
        example="__import__('time').sleep(60)",
        limits=limits,
    )
    assert (report.ok, report.outcome) == (True, "built")
    assert (report.example.ok, report.example.error) == (
        False,
        texts.example_timeout(1),
    )


@pytest.mark.parametrize("fixture", ["word_count", "hang"])
def test_the_temporary_folder_is_removed(tmp_path, monkeypatch, fixture):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    check_tool("word_count", "factory: make", source(fixture), limits=QUICK)
    assert list(tmp_path.iterdir()) == []


def test_not_func_and_unknown_factory_sentences_equal_make_tools(tmp_path):
    config = materialized(tmp_path, "word_count", "factory: make", source("not_func"))
    unknown = tmp_path / "unknown.yaml"
    unknown.write_text(
        yaml.safe_dump(
            {
                "client": {"base_url": CHECK_MODEL_URL},
                "tools": {"notes": {"factory": "ragg"}},
            }
        )
    )
    said = []
    for main in (config / "main.yaml", unknown):
        cfg = load_cli_config(main, schema=V2Config)
        with pytest.raises(ValueError) as raised:
            make_tools(cfg, build_client(cfg.client))
        said.append(str(raised.value))
    assert said == [
        texts.not_func("word_count", "make", "tools/word_count.py", "function"),
        texts.unknown_factory("ragg", "notes", TOOL_BUILDERS),
    ]
