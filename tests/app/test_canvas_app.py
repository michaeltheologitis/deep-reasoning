import hashlib
import io
import json
import platform
import sys
import tarfile
from pathlib import Path

import pytest

import deep_reasoning.canvas_app
from dr_app import texts
from dr_app.agent_server import AgentServer
from dr_app.canvas_app import (
    APP_NAME,
    ARTIFACT_PATH,
    STAGED_FILES,
    backend_artifact,
    backend_block,
    ensure_canvas_app,
    stage_canvas_app,
)
from dr_app.cli import after_ready
from dr_app.layout import CanvasAppRecord, SetupState
from tests.app.conftest import COMMIT, D3_APP, DEV_BIN
from tests.crossrepo.agent_server import OPENER, agent_server, sdk_checkout

SYSTEM = platform.system()
HOME = Path("/Users/Jane Doe/.deep-reasoning")
INSTALLED = f"/api/canvas-extensions/installed/{APP_NAME}"
INSTALL = "/api/canvas-extensions/install"


def members(artifact: bytes) -> dict[str, tarfile.TarInfo]:
    with tarfile.open(fileobj=io.BytesIO(artifact), mode="r:gz") as tar:
        return {m.name: m for m in tar.getmembers()}


def test_the_backend_artifact_is_byte_for_byte_stable():
    dr_library = Path("/Users/Jane Doe/.deep-reasoning/runtime/current/bin/dr-library")
    artifact = backend_artifact(dr_library)
    assert backend_artifact(dr_library) == artifact
    assert backend_artifact(Path("/elsewhere/dr-library")) != artifact
    [member] = members(artifact).values()
    assert (member.name, member.mode, member.uid, member.mtime) == (
        "bin/dr-library",
        0o755,
        0,
        0,
    )
    with tarfile.open(fileobj=io.BytesIO(artifact), mode="r:gz") as tar:
        script = tar.extractfile(member).read().decode()
    assert script == (
        "#!/bin/sh\n"
        "exec '/Users/Jane Doe/.deep-reasoning/runtime/current/bin/dr-library' \"$@\"\n"
    )


@pytest.mark.parametrize(
    ("system", "os_name"), [("Linux", "linux"), ("Darwin", "darwin")]
)
def test_the_manifest_names_both_architectures_and_the_home(system, os_name):
    block = backend_block(system=system, sha256="ab" * 32, home=HOME)
    artifact = {"path": ARTIFACT_PATH, "sha256": "ab" * 32}
    assert block == {
        "schema_version": 1,
        "artifacts": {f"{os_name}-amd64": artifact, f"{os_name}-arm64": artifact},
        "argv": [
            "{artifact_dir}/bin/dr-library",
            "serve",
            "--port",
            "{port}",
            "--home",
            str(HOME),
        ],
        "inherit_environment": ["LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ"],
    }


def test_only_the_apps_own_files_are_staged(runtime, app_files):
    staged = stage_canvas_app(runtime, home=HOME, system=SYSTEM)
    files = sorted(
        str(p.relative_to(staged.path)) for p in staged.path.rglob("*") if p.is_file()
    )
    assert files == sorted([*STAGED_FILES, ARTIFACT_PATH])
    manifest = json.loads((staged.path / "canvas-extension.json").read_text())
    d3 = json.loads((D3_APP / "canvas-extension.json").read_text())
    assert manifest == {**d3, "backend": manifest["backend"]}
    artifact = (staged.path / ARTIFACT_PATH).read_bytes()
    sha = hashlib.sha256(artifact).hexdigest()
    assert manifest["backend"] == backend_block(system=SYSTEM, sha256=sha, home=HOME)
    assert (staged.version, staged.manifest) == (d3["version"], manifest)

    (app_files / "ui" / "index.html").write_text("<p>a UI-only change</p>")
    assert stage_canvas_app(runtime, home=HOME, system=SYSTEM).digest == staged.digest
    (app_files / "dist" / "index.js").write_text("export {};")
    changed = stage_canvas_app(runtime, home=HOME, system=SYSTEM)
    assert changed.digest != staged.digest
    assert changed.path.parent == staged.path.parent


def test_our_app_name_is_d3s():
    assert APP_NAME == deep_reasoning.canvas_app.APP_NAME
    for name in STAGED_FILES:
        assert (D3_APP / name).is_file(), name


@pytest.fixture
def setup_app(runtime, agent_server):
    """ensure_canvas_app as setup runs it: the record and what it printed."""

    def run(state: SetupState, home: Path = HOME):
        staged = stage_canvas_app(runtime, home=home, system=SYSTEM)
        server = AgentServer(agent_server.url, agent_server.session_key)
        said: list[str] = []
        record = ensure_canvas_app(server, staged, state, log=said.append)
        state = SetupState(state.v, state.dr_home, state.runtime, state.profile, record)
        return state, record, said, staged

    return run


FRESH = SetupState(1, str(HOME), None, None, None)


def test_a_first_install_enables_approves_and_starts(setup_app, agent_server):
    _, record, said, staged = setup_app(FRESH)
    assert agent_server.requests() == [
        ("GET", INSTALLED),
        ("POST", INSTALL),
        ("PATCH", INSTALLED),
        ("GET", f"{INSTALLED}/backend"),
        ("POST", f"{INSTALLED}/backend/prepare"),
        ("POST", f"{INSTALLED}/backend/start"),
    ]
    assert agent_server.calls[1].body == {"source": str(staged.path), "force": False}
    app = agent_server.apps[APP_NAME]
    assert (app.enabled, app.state, app.prepared) == (True, "ready", app.revision)
    assert record == CanvasAppRecord(staged.digest, "0.1.0")
    assert said == [texts.app_ready("0.1.0", "installed")]


def test_a_relaunch_only_starts_the_backend(setup_app, agent_server):
    state, record, _, _ = setup_app(FRESH)
    agent_server.restart()
    agent_server.calls.clear()
    _, again, said, _ = setup_app(state)
    assert agent_server.requests() == [
        ("GET", INSTALLED),
        ("GET", f"{INSTALLED}/backend"),
        ("POST", f"{INSTALLED}/backend/start"),
    ]
    assert again == record
    assert said == [texts.app_ready("0.1.0", "current")]


def test_an_upgrade_stops_reinstalls_and_reapproves(setup_app, agent_server):
    state, record, _, _ = setup_app(FRESH)
    agent_server.calls.clear()
    moved = Path("/var/tmp/deep-reasoning-501")
    _, upgraded, said, staged = setup_app(state, home=moved)
    assert agent_server.requests() == [
        ("GET", INSTALLED),
        ("POST", f"{INSTALLED}/backend/stop"),
        ("POST", INSTALL),
        ("GET", f"{INSTALLED}/backend"),
        ("POST", f"{INSTALLED}/backend/prepare"),
        ("POST", f"{INSTALLED}/backend/start"),
    ]
    assert agent_server.calls[2].body == {"source": str(staged.path), "force": True}
    assert agent_server.apps[APP_NAME].manifest["backend"]["argv"][-1] == str(moved)
    assert upgraded.digest != record.digest
    assert said == [texts.app_ready("0.1.0", "installed")]


def test_a_disabled_app_is_left_alone(setup_app, agent_server):
    state, record, _, _ = setup_app(FRESH)
    agent_server.restart()
    agent_server.apps[APP_NAME].enabled = False
    agent_server.calls.clear()
    _, again, said, _ = setup_app(state)
    assert agent_server.requests() == [("GET", INSTALLED)]
    assert again == record
    assert said == [texts.APP_DISABLED]


def test_an_unsupported_platform_says_so(setup_app, agent_server, monkeypatch):
    monkeypatch.setattr("tests.app.fake_agent_server.PLATFORM", "windows-amd64")
    _, _, said, _ = setup_app(FRESH)
    assert said == [texts.APP_UNSUPPORTED]


def test_an_agent_server_refusal_warns_and_setup_succeeds(
    runtime, agent_server, capsys
):
    agent_server.refuse[("POST", INSTALL)] = (422, "Invalid canvas extension.")
    env = {
        "AGENT_SERVER_URL": agent_server.url,
        "SESSION_API_KEY": agent_server.session_key,
    }
    after_ready(runtime, env=env)
    said = capsys.readouterr().out.splitlines()
    assert said[-1] == texts.app_warning(f"POST {INSTALL}: Invalid canvas extension.")
    state = SetupState.load(runtime.setup_file)
    assert state.profile is not None
    assert state.canvas_app is None, (
        "nothing installed is recorded: the next launch retries"
    )


@pytest.mark.crossrepo
def test_the_staged_app_passes_prepare_and_its_backend_answers_health(tmp_path, layout):
    """Against a real agent-server from the SDK fork's pinned commit, with a runtime that
    is this environment: its python finds D3's files, its dr-library is D2's."""
    bin_ = layout.runtime_dir / COMMIT / "bin"
    bin_.mkdir(parents=True)
    (bin_ / "python").write_text(f'#!/bin/sh\nexec {sys.executable} "$@"\n')
    (bin_ / "python").chmod(0o755)
    (bin_ / "dr-library").symlink_to(DEV_BIN / "dr-library")
    layout.current_runtime.symlink_to(COMMIT)
    home = tmp_path / "dr-home"
    staged = stage_canvas_app(layout, home=home, system=SYSTEM)
    with agent_server(sdk_checkout(), tmp_path / "agent-server") as running:
        server = AgentServer(running.url, running.session_key)
        said: list[str] = []
        ensure_canvas_app(server, staged, FRESH, log=said.append)
        status = server.request("GET", f"{INSTALLED}/backend")
        with OPENER.open(f"http://127.0.0.1:{status['port']}/health") as answer:
            health = json.loads(answer.read())
        server.request("POST", f"{INSTALLED}/backend/stop")
    assert said == [texts.app_ready("0.1.0", "installed")]
    assert status["state"] == "ready"
    assert status["prepared_revision"] == status["revision"]
    assert (health["ok"], health["path"]) == (True, str(home / "library.sqlite"))
