"""The Library App: D3's built files staged with a backend this machine can run, then
installed, approved and started (D5 §4.6, decision G)."""

import gzip
import hashlib
import io
import json
import shlex
import shutil
import subprocess
import tarfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from dr_app import texts
from dr_app.agent_server import AgentServer, AgentServerError
from dr_app.layout import AppLayout, CanvasAppRecord, SetupState

# D3's deep_reasoning.canvas_app.APP_NAME, mirrored: this package imports nothing of
# deep-reasoning's.
APP_NAME: Final = "dr-library"
# D3's built files, in the runtime (§8.3)
APP_PACKAGE: Final = "deep_reasoning.canvas_app"
# The only files staged; ui/ is served by dr-library serve itself (D3 §8.4 item 1).
STAGED_FILES: Final = ("canvas-extension.json", "dist/index.js", "panel.svg")
MANIFEST: Final = STAGED_FILES[0]
ARTIFACT_PATH: Final = "backend/dr-library.tar.gz"
ARTIFACT_MEMBER: Final = "bin/dr-library"
# The agent-server passes a backend only these (backend.py:38–40).
INHERITED_ENVIRONMENT: Final = ("LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ")
PLATFORMS: Final = {"Linux": "linux", "Darwin": "darwin"}
INSTALLED: Final = f"/api/canvas-extensions/installed/{APP_NAME}"


@dataclass(frozen=True)
class StagedApp:
    path: Path
    digest: str
    version: str
    manifest: Mapping[str, Any]


def backend_artifact(dr_library: Path) -> bytes:
    """The deterministic .tar.gz of §4.6 step 2: equal inputs give equal bytes. One
    member, bin/dr-library, a /bin/sh script that execs dr_library."""
    script = f'#!/bin/sh\nexec {shlex.quote(str(dr_library))} "$@"\n'.encode()
    member = tarfile.TarInfo(ARTIFACT_MEMBER)
    member.size = len(script)
    member.mode = 0o755
    member.mtime = 0
    member.uid = member.gid = 0
    member.uname = member.gname = ""
    archive = io.BytesIO()
    with (
        gzip.GzipFile(fileobj=archive, mode="wb", mtime=0, filename="") as zipped,
        tarfile.open(fileobj=zipped, mode="w", format=tarfile.USTAR_FORMAT) as tar,
    ):
        tar.addfile(member, io.BytesIO(script))
    return archive.getvalue()


def backend_block(*, system: str, sha256: str, home: Path) -> dict[str, Any]:
    """The manifest's backend: both architectures name the same script, which runs on
    either; the home is a literal, since the backend gets no DR_HOME or HOME."""
    os_name = PLATFORMS[system]
    artifact = {"path": ARTIFACT_PATH, "sha256": sha256}
    return {
        "schema_version": 1,
        "artifacts": {f"{os_name}-amd64": artifact, f"{os_name}-arm64": artifact},
        "argv": [
            "{artifact_dir}/" + ARTIFACT_MEMBER,
            "serve",
            "--port",
            "{port}",
            "--home",
            str(home),
        ],
        "inherit_environment": list(INHERITED_ENVIRONMENT),
    }


def app_files(layout: AppLayout) -> Path:
    """Where D3's built files are in the runtime."""
    python = layout.current_runtime / "bin" / "python"
    found = subprocess.run(
        [
            str(python),
            "-c",
            f"import importlib.resources as r; print(r.files({APP_PACKAGE!r}))",
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(found.stdout.strip())


def stage_canvas_app(layout: AppLayout, *, home: Path, system: str) -> StagedApp:
    """§4.6 steps 1–4: the three files, the artifact and the manifest with its backend
    under canvas-app/<digest>/, reused when it is there."""
    source = app_files(layout)
    artifact = backend_artifact(layout.current_runtime / "bin" / "dr-library")
    manifest = json.loads((source / MANIFEST).read_text())
    manifest["backend"] = backend_block(
        system=system, sha256=hashlib.sha256(artifact).hexdigest(), home=home
    )
    contents = {
        MANIFEST: (json.dumps(manifest, indent=2) + "\n").encode(),
        **{name: (source / name).read_bytes() for name in STAGED_FILES[1:]},
        ARTIFACT_PATH: artifact,
    }
    digest = hashlib.sha256()
    for name, data in contents.items():
        digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
    staged = layout.canvas_app_dir / digest.hexdigest()
    if not staged.is_dir():
        building = staged.with_name(f"{staged.name}.tmp")
        shutil.rmtree(building, ignore_errors=True)
        for name, data in contents.items():
            (building / name).parent.mkdir(parents=True, exist_ok=True)
            (building / name).write_bytes(data)
        building.rename(staged)
    return StagedApp(staged, digest.hexdigest(), manifest["version"], manifest)


def ensure_canvas_app(
    server: AgentServer,
    staged: StagedApp,
    state: SetupState,
    *,
    log: Callable[[str], None],
) -> CanvasAppRecord | None:
    """§4.6 step 5. Never raises for the agent-server's refusals: they become
    texts.app_warning(...). The record is what is installed now."""
    record = state.canvas_app
    try:
        info = server.request("GET", INSTALLED)
        fresh = info is None or record is None or record.digest != staged.digest
        if fresh:
            if info is not None:
                server.request("POST", f"{INSTALLED}/backend/stop")
            server.request(
                "POST",
                "/api/canvas-extensions/install",
                {"source": str(staged.path), "force": info is not None},
            )
            if info is None:
                server.request("PATCH", INSTALLED, {"enabled": True})
            record = CanvasAppRecord(staged.digest, staged.version)
        if info is not None and not info["enabled"]:
            log(texts.APP_DISABLED)
            return record
        status = server.request("GET", f"{INSTALLED}/backend")
        if status["state"] == "unsupported":
            log(texts.APP_UNSUPPORTED)
            return record
        revision = {"revision": status["revision"]}
        if status["prepared_revision"] != status["revision"]:
            status = server.request("POST", f"{INSTALLED}/backend/prepare", revision)
        if status["state"] != "ready":
            status = server.request("POST", f"{INSTALLED}/backend/start", revision)
    except AgentServerError as error:
        log(texts.app_warning(f"{error.method} {error.path}: {error.detail}"))
        return record
    if status["state"] == "ready":
        log(texts.app_ready(staged.version, "installed" if fresh else "current"))
    else:
        log(texts.app_warning(status.get("detail") or status["state"]))
    return record
