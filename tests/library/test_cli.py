import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest

from deep_reasoning.library.cli import main
from tests.library.conftest import example, text

# The agent-server starts an App backend with only these variables from its environment.
APP_BACKEND_ENV = ("LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ")
# What the console script dr-library runs.
DR_LIBRARY = [
    sys.executable,
    "-c",
    "from deep_reasoning.library.cli import main; raise SystemExit(main())",
]
READY_S = 30


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def get(url: str, host: str | None = None) -> tuple[int, dict]:
    request = urllib.request.Request(url, headers={"Host": host} if host else {})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def test_serve_answers_health_on_loopback(tmp_path):
    port, home = free_port(), tmp_path / "home"
    env = {name: os.environ[name] for name in APP_BACKEND_ENV if name in os.environ}
    server = subprocess.Popen(
        [*DR_LIBRARY, "serve", "--port", str(port), "--home", str(home)],
        env=env,
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + READY_S
        while True:
            try:
                status, health = get(f"http://127.0.0.1:{port}/health")
                break
            except OSError:
                assert server.poll() is None, server.stderr.read().decode()
                assert time.monotonic() < deadline, "no answer on /health"
                time.sleep(0.2)
        assert status == 200
        assert (health["ok"], health["rev"], health["default_namespace"]) == (
            True,
            1,
            "root",
        )
        assert health["path"] == str(home / "library.sqlite")
        forbidden, _ = get(
            f"http://127.0.0.1:{port}/health", host=f"rebound.example:{port}"
        )
        assert forbidden == 403
    finally:
        server.terminate()
        _, stderr = server.communicate(timeout=10)
    # uvicorn shuts down cleanly on SIGTERM, then re-raises it.
    assert server.returncode in (0, -signal.SIGTERM), stderr.decode()
    assert "Application shutdown complete." in stderr.decode()


def test_import_and_export_print_their_lines(router, tmp_path, capsys):
    home = tmp_path / "home"
    assert main(["import", str(router), "--home", str(home)]) == 0
    assert (
        capsys.readouterr().out
        == f"imported {router} as revision 2: 5 new, 2 changed, 0 unchanged\n"
    )
    assert main(["import", str(router), "--home", str(home)]) == 0
    assert (
        capsys.readouterr().out
        == f"nothing changed: the library already holds {router}\n"
    )
    out = tmp_path / "export"
    assert (
        main(["export", str(out), "--home", str(home), "--namespace", "courses"]) == 0
    )
    assert capsys.readouterr().out == (
        f"wrote {out / 'main.yaml'}: 3 namespaces, 3 decompositions, 0 tools\n"
    )
    assert (out / "main.yaml").is_file()


def test_export_at_an_old_revision(router, tmp_path, capsys):
    home = tmp_path / "home"
    main(["import", str(router), "--home", str(home)])
    assert (
        main(["export", str(tmp_path / "first"), "--home", str(home), "--rev", "1"])
        == 0
    )
    assert capsys.readouterr().out.endswith(
        ": 1 namespace, 0 decompositions, 0 tools\n"
    )


def test_a_library_error_exits_1_with_its_message_on_stderr(tmp_path, capsys):
    (tmp_path / "taken").mkdir()
    (tmp_path / "taken" / "keep").write_text(text(example("x")))
    assert (
        main(["export", str(tmp_path / "taken"), "--home", str(tmp_path / "home")]) == 1
    )
    assert capsys.readouterr().err == (
        f"{tmp_path / 'taken'} is not empty; the library writes a config directory only into "
        "a new or empty folder.\n"
    )


def test_usage_errors_exit_2():
    with pytest.raises(SystemExit) as raised:
        main(["serve"])
    assert raised.value.code == 2
