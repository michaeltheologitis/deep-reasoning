"""The runtime: deep-reasoning at the setup command's commit, with deep_reasoner and
every other dependency as that commit's uv.lock pins them, in a venv of its own that
runtime/current links to (D5 §4.4.2, §4.4.3, decisions C and P).

A launch whose runtime is current costs one exec of its Python. Otherwise setup fetches
the commit's tree, checks that deep_reasoner is readable, and syncs the tree into a new
venv, so a user runs the set CI tested; the link moves only once the new runtime
imports. Every subprocess runs through run_logged: its output reaches the startup log,
and nothing it leaves behind holds the launcher's phase open.
"""

import hashlib
import os
import re
import select
import shutil
import subprocess
import time
import tomllib
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dr_app import texts
from dr_app.layout import EXIT_CHECK, EXIT_INSTALL, AppLayout, RuntimeRecord, SetupError

PYTHON_VERSION: Final = "3.12"
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
DEEP_REASONER: Final = "deep-reasoner"  # its package name in uv.lock
# The import check of §4.4.3: what dr-acp, dr-library and dr need at their start.
IMPORT_CHECK: Final = (
    "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
)
# (decision P) How long the line pump may run on after its process has exited.
PUMP_DRAIN_S: Final = 1.0
READ_CHUNK: Final = 65536
Step = tuple[str, Sequence[str], Path | None]  # its name in install_failed, argv, cwd


def runtime_is_current(
    layout: AppLayout, record: RuntimeRecord | None, commit: str
) -> bool:
    """The record is the commit's (which fixes its uv.lock), runtime/current resolves to
    it, and its Python starts: one exec, offline."""
    if record is None or record.commit != commit:
        return False
    if layout.current_runtime.resolve() != Path(record.path).resolve():
        return False
    python = Path(record.path) / "bin" / "python"
    try:
        done = subprocess.run(
            [str(python), "-I", "-c", ""],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


def check_git() -> str:
    """git's version string. Raises SetupError(10, texts.NO_GIT)."""
    try:
        done = subprocess.run(
            ["git", "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        raise SetupError(EXIT_CHECK, texts.NO_GIT) from None
    if done.returncode != 0:
        raise SetupError(EXIT_CHECK, texts.NO_GIT)
    return done.stdout.strip().removeprefix("git version ")


def check_readable(url: str) -> None:
    """git ls-remote url HEAD. Raises SetupError(10, texts.no_access_dr(...)). Its output
    goes nowhere, so a credential helper that stays behind holds no pipe."""
    done = subprocess.run(
        ["git", "ls-remote", url, "HEAD"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=git_environment(os.environ),
        check=False,
    )
    if done.returncode != 0:
        raise SetupError(EXIT_CHECK, texts.no_access_dr(host_path(url)))


@dataclass(frozen=True)
class Pin:
    url: str  # https URL of the repository
    commit: str  # 40 hex


def deep_reasoner_pin(source: Path) -> Pin:
    """deep_reasoner's repository and commit, as the tree's uv.lock pins them."""
    lock = tomllib.loads((source / "uv.lock").read_text())
    [git] = [p["source"]["git"] for p in lock["package"] if p["name"] == DEEP_REASONER]
    url, _, commit = git.partition("#")
    return Pin(url.partition("?")[0], commit)


def host_path(url: str) -> str:
    """https://github.com/a/b -> github.com/a/b, as the sentences name a repository."""
    return re.sub(r"^[a-z+]+://", "", url).removesuffix(".git")


@contextmanager
def fetched_source(
    layout: AppLayout, repo: str, commit: str, *, log: Callable[[str], None]
) -> Iterator[Path]:
    """deep-reasoning's tree at commit, fetched alone, in runtime/ while it is needed;
    whatever an interrupted install left there is removed first. Raises
    SetupError(11, texts.install_failed(...)) naming the git step that failed."""
    runtime = layout.runtime_dir
    runtime.mkdir(parents=True, exist_ok=True)
    for leftover in runtime.glob("*.tmp-*"):
        _remove(leftover)
    source = runtime / f"{commit}.tmp-{os.getpid()}-source"
    fetch: list[Step] = [
        ("git init", ["git", "init", "-q", str(source)], None),
        ("git fetch", ["git", "fetch", "-q", "--depth", "1", repo, commit], source),
        ("git checkout", ["git", "checkout", "-q", "FETCH_HEAD"], source),
    ]
    try:
        _run_steps(commit, fetch, env=git_environment(os.environ), log=log)
        yield source
    finally:
        _remove(source)


def install_runtime(
    layout: AppLayout,
    source: Path,
    commit: str,
    *,
    uv: str,
    log: Callable[[str], None],
) -> RuntimeRecord:
    """§4.4.3: a venv on uv's own Python, every workspace package of source synced into
    it from its uv.lock (no dev group, nothing editable), the import check, then the
    rename and the link. Raises SetupError(11, texts.install_failed(...)) on any
    non-zero step, leaving runtime/current as it was."""
    runtime = layout.runtime_dir
    building = runtime / f"{commit}.tmp-{os.getpid()}"
    lock_sha256 = hashlib.sha256((source / "uv.lock").read_bytes()).hexdigest()
    env = git_environment(os.environ) | {"UV_PROJECT_ENVIRONMENT": str(building)}
    sync = ["--frozen", "--no-dev", "--no-editable", "--all-packages"]
    steps: list[Step] = [
        # Relocatable: the venv is built under a temporary name, then renamed, and its
        # commands must find their python where they end up.
        (
            "uv venv",
            [uv, "venv", "--relocatable", "--managed-python"]
            + ["--python", PYTHON_VERSION, str(building)],
            None,
        ),
        ("uv sync", [uv, "sync", *sync, "--project", str(source)], None),
        (
            "the import check",
            [str(building / "bin" / "python"), "-c", IMPORT_CHECK],
            None,
        ),
    ]
    try:
        _run_steps(commit, steps, env=env, log=log)
    except SetupError:
        _remove(building)
        raise
    final = runtime / commit
    _remove(final)
    building.rename(final)
    link = runtime / "current.tmp"
    _remove(link)
    link.symlink_to(commit)
    link.replace(layout.current_runtime)
    for other in runtime.iterdir():
        if other.name not in (commit, layout.current_runtime.name, source.name):
            _remove(other)
    return RuntimeRecord(commit, lock_sha256, str(final))


def _run_steps(
    commit: str,
    steps: Sequence[Step],
    *,
    env: Mapping[str, str],
    log: Callable[[str], None],
) -> None:
    """Each step through run_logged. Raises SetupError(11, texts.install_failed(...))
    naming the first that exits non-zero."""
    for step, argv, cwd in steps:
        code = run_logged(argv, env=env, log=log, cwd=cwd)
        if code != 0:
            raise SetupError(
                EXIT_INSTALL, texts.install_failed(commit[:7], step, str(code))
            )


def run_logged(
    argv: Sequence[str],
    *,
    env: Mapping[str, str],
    log: Callable[[str], None],
    cwd: Path | None = None,
) -> int:
    """argv's exit code. stdout and stderr share one pipe; each line goes to log as it
    arrives. Returns at the process's exit, after at most PUMP_DRAIN_S more of reading: a
    grandchild that keeps the pipe never holds it. Never starts a new session."""
    process = subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(env),
        cwd=cwd,
    )
    pipe = process.stdout.fileno()
    pending = b""
    deadline: float | None = None
    try:
        while deadline is None or time.monotonic() < deadline:
            wait = 0.1 if deadline is None else max(0.0, deadline - time.monotonic())
            if select.select([pipe], [], [], wait)[0]:
                chunk = os.read(pipe, READ_CHUNK)
                if not chunk:
                    break
                *lines, pending = (pending + chunk).split(b"\n")
                for line in lines:
                    log(line.decode(errors="replace").rstrip("\r"))
            if deadline is None and process.poll() is not None:
                deadline = time.monotonic() + PUMP_DRAIN_S
    finally:
        process.stdout.close()
    if pending:
        log(pending.decode(errors="replace").rstrip("\r"))
    return process.wait()


def git_environment(base: Mapping[str, str]) -> dict[str, str]:
    """base plus GIT_TERMINAL_PROMPT=0 and, unless set, GIT_SSH_COMMAND='ssh -o
    BatchMode=yes'."""
    return {
        **base,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_SSH_COMMAND": base.get("GIT_SSH_COMMAND") or "ssh -o BatchMode=yes",
    }


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
