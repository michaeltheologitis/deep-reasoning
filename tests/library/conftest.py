import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
import yaml

from deep_reasoning.library import Library


def example(
    name: str,
    ask: str = "Which course comes after CS101?",
    *,
    answer: str = "CS201",
) -> dict[str, Any]:
    """A decomposition's body: one question, one answering turn."""
    return {
        "name": name,
        "messages": [
            {"role": "user", "content": ask},
            {
                "role": "assistant",
                "content": f"<think>{ask}</think>\n<repl>\nFinalAnswer({answer!r})\n</repl>\n",
            },
        ],
    }


def text(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False)


def user_texts(messages: list[dict[str, Any]]) -> list[str]:
    """What a model request's user turns say."""
    return [m["content"] for m in messages if m["role"] == "user"]


def write_config(directory: Path, main: dict[str, Any], **files: Any) -> Path:
    """main.yaml in directory, plus files by relative path (dicts are dumped as YAML)."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = directory / name.replace("__", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else text(content))
    path = directory / "main.yaml"
    path.write_text(text(main))
    return path


ROUTER = {
    "model": "m-small",
    "client": {"base_url": "http://127.0.0.1:9/v1", "api_key_env": "FAKE_KEY"},
    "system_prompt": "Act in one <repl> block per turn.\nAnswer with FinalAnswer(value).\n",
    "max_iter": 5,
    "entry_namespace": "router",
    "namespaces": {
        "root": {"tools": ["llm"]},
        "router": {
            "spawn": ["courses"],
            "decompositions": [example("route a course question"), example("decline")],
        },
        "courses": {
            "vars": {
                "catalog": {"CS101": {"prereqs": []}, "CS201": {"prereqs": ["CS101"]}}
            },
            "decompositions": [example("catalog lookup")],
        },
    },
}


@pytest.fixture
def lib(tmp_path: Path) -> Library:
    """A fresh Library holding revision 1: an empty profile and a bare root."""
    return Library.open(tmp_path / "home" / "library.sqlite", starter=False)


@pytest.fixture
def router(tmp_path: Path) -> Path:
    """A plain dr config of our own: root, router (entry) and courses."""
    return write_config(tmp_path / "router", ROUTER)


DR = Path(sys.executable).parent / "dr"


def run_dr(
    config: Path,
    task: str,
    *,
    cwd: Path,
    sets: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """deep_reasoner's own `dr` on config, one task, logs under cwd/runs."""
    argv = [str(DR), str(config), task, "--no-progress", "--run-dir", str(cwd / "runs")]
    return subprocess.run(
        [*argv, *(["--set", *sets] if sets else [])],
        cwd=cwd,
        env={**os.environ, "FAKE_KEY": "fake", **(env or {})},
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
