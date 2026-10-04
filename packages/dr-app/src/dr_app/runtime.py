"""The runtime: deep-reasoning and deep_reasoner installed from the committed lock into a
venv of their own, swapped in by a link (D5 §4.4.2, §4.4.3, decisions C and P)."""

import hashlib
import os
import re
import select
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Final

from dr_app import texts
from dr_app.layout import AppLayout, RuntimeRecord, SetupError

__all__ = [
    "LOCK_RESOURCE",
    "PUMP_DRAIN_S",
    "PYTHON_VERSION",
    "RuntimeSpec",
    "SetupError",
    "check_git",
    "check_readable",
    "git_environment",
    "install_runtime",
    "run_logged",
    "runtime_is_current",
]

PYTHON_VERSION: Final = "3.12"
LOCK_RESOURCE: Final = "runtime.lock.txt"
EXIT_CHECK: Final = 10
EXIT_INSTALL: Final = 11
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
DEEP_REASONER_LINE: Final = re.compile(
    r"^deep-reasoner @ git\+(?P<url>\S+)@(?P<commit>[0-9a-f]{40})", re.MULTILINE
)
# The import check of §4.4.3: what dr-acp, dr-library and dr need at their start.
IMPORT_CHECK: Final = (
    "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
)
# (decision P) How long the line pump may run on after its process has exited.
PUMP_DRAIN_S: Final = 1.0
READ_CHUNK: Final = 65536


@dataclass(frozen=True)
class RuntimeSpec:
    repo: str  # https URL of deep-reasoning
    commit: str  # 40 hex
    lock_sha256: str
    requirements: str  # runtime.lock.txt plus the two git lines of §4.4.3
    deep_reasoner_url: str  # parsed from the lock's deep-reasoner line
    deep_reasoner_commit: str

    @classmethod
    def for_commit(cls, repo: str, commit: str) -> "RuntimeSpec":
        """Reads the packaged lock. Raises ValueError for a commit that is not 40 hex."""
        if not COMMIT.fullmatch(commit):
            raise ValueError(f"not a full commit: {commit!r}")
        lock = files("dr_app").joinpath(LOCK_RESOURCE).read_text()
        found = DEEP_REASONER_LINE.search(lock)
        if found is None:
            raise ValueError(f"{LOCK_RESOURCE} has no deep-reasoner line")
        requirements = (
            lock.rstrip("\n")
            + f"\ndeep-reasoning @ git+{repo}@{commit}"
            + f"\ndeep-reasoning-app @ git+{repo}@{commit}#subdirectory=packages/dr-app\n"
        )
        return cls(
            repo=repo,
            commit=commit,
            lock_sha256=hashlib.sha256(lock.encode()).hexdigest(),
            requirements=requirements,
            deep_reasoner_url=found["url"],
            deep_reasoner_commit=found["commit"],
        )


def host_path(url: str) -> str:
    """https://github.com/a/b -> github.com/a/b, as the sentences name a repository."""
    return re.sub(r"^[a-z+]+://", "", url).removesuffix(".git")


def git_environment(base: Mapping[str, str]) -> dict[str, str]:
    """base plus GIT_TERMINAL_PROMPT=0 and, unless set, GIT_SSH_COMMAND='ssh -o
    BatchMode=yes'."""
    return {
        **base,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_SSH_COMMAND": base.get("GIT_SSH_COMMAND") or "ssh -o BatchMode=yes",
    }


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


def check_git(
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    """git's version string. Raises SetupError(10, texts.NO_GIT)."""
    try:
        done = run(
            ["git", "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
    except OSError:
        raise SetupError(EXIT_CHECK, texts.NO_GIT) from None
    if done.returncode != 0:
        raise SetupError(EXIT_CHECK, texts.NO_GIT)
    return done.stdout.strip().removeprefix("git version ")


def check_readable(
    url: str,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    """git ls-remote url HEAD. Raises SetupError(10, texts.no_access_dr(...)). Its output
    goes nowhere, so a credential helper that stays behind holds no pipe."""
    done = run(
        ["git", "ls-remote", url, "HEAD"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=git_environment(os.environ),
    )
    if done.returncode != 0:
        raise SetupError(EXIT_CHECK, texts.no_access_dr(host_path(url)))


def runtime_is_current(
    layout: AppLayout, record: RuntimeRecord | None, spec: RuntimeSpec
) -> bool:
    """The record's commit and lock are the spec's, runtime/current resolves to it, and
    its Python starts."""
    if record is None or (record.commit, record.lock_sha256) != (
        spec.commit,
        spec.lock_sha256,
    ):
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


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def install_runtime(
    layout: AppLayout,
    spec: RuntimeSpec,
    *,
    uv: str,
    log: Callable[[str], None],
) -> RuntimeRecord:
    """§4.4.3, every step through run_logged. Raises SetupError(11,
    texts.install_failed(...)) on any non-zero step."""
    runtime = layout.runtime_dir
    runtime.mkdir(parents=True, exist_ok=True)
    for leftover in runtime.glob("*.tmp-*"):
        _remove(leftover)
    building = runtime / f"{spec.commit}.tmp-{os.getpid()}"
    python = building / "bin" / "python"
    requirements = runtime / f"{spec.commit}.tmp-{os.getpid()}-requirements.txt"
    env = git_environment(os.environ)
    steps = [
        (
            "uv venv",
            [uv, "venv", "--managed-python", "--python", PYTHON_VERSION, str(building)],
        ),
        (
            "uv pip sync",
            [uv, "pip", "sync", "--python", str(python), str(requirements)],
        ),
        ("the import check", [str(python), "-c", IMPORT_CHECK]),
    ]
    requirements.write_text(spec.requirements)
    try:
        for step, argv in steps:
            code = run_logged(argv, env=env, log=log)
            if code != 0:
                _remove(building)
                raise SetupError(
                    EXIT_INSTALL, texts.install_failed(spec.commit[:7], step, str(code))
                )
    finally:
        requirements.unlink(missing_ok=True)
    final = runtime / spec.commit
    if final.exists():
        _remove(final)
    building.rename(final)
    link = runtime / "current.tmp"
    _remove(link)
    link.symlink_to(spec.commit)
    link.replace(layout.current_runtime)
    for other in runtime.iterdir():
        if other.name not in (spec.commit, layout.current_runtime.name):
            _remove(other)
    return RuntimeRecord(spec.commit, spec.lock_sha256, str(final))
