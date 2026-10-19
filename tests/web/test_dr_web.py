"""dr-web, the browser command uvx runs (TASK-48 §3.1, §7.1): a local HTTP server stands
for the release, and a stub uv on PATH for Node's install."""

import gzip
import http.server
import io
import json
import os
import shutil
import ssl
import subprocess
import sys
import tarfile
import threading
import tomllib
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from desktop import build
from dr_app import layout as app_layout
from dr_web import cache, cli, texts
from dr_web.cache import FetchError, WebLayout

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "9e8109e8" * 5
ENTRY_SOURCE = b"// the entry\n"
# The stub uv: records its argv and the requirements it was given, then lays out what
# the wheel's install leaves under --target: npm's scripts copied into bin/, npm itself
# under lib/, and a node that answers --version. $STUB_UV_EXIT fails it after that.
STUB_UV = """#!{python}
import json, os, pathlib, sys
argv = sys.argv[1:]
requirements = argv[argv.index("-r") + 1]
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps({{"argv": argv, "requirements": open(requirements).read()}}) + "\\n")
print("Resolved 1 package")
wheel = pathlib.Path(argv[argv.index("--target") + 1]) / "nodejs_wheel"
(wheel / "bin").mkdir(parents=True)
for name in ("npm", "npx"):
    (wheel / "bin" / name).write_text("require('../lib/cli.js')\\n")
    (wheel / "lib/node_modules/npm/bin").mkdir(parents=True, exist_ok=True)
    (wheel / "lib/node_modules/npm/bin" / (name + "-cli.js")).write_text("")
(wheel / "bin" / "node").write_text("#!/bin/sh\\necho " + os.environ.get("STUB_NODE_VERSION", "v22.12.0") + "\\n")
(wheel / "bin" / "node").chmod(0o755)
print("Installed 1 package")
sys.exit(int(os.environ.get("STUB_UV_EXIT", "0")))
"""


@dataclass
class StubUv:
    path: Path
    log: Path

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]


@pytest.fixture
def web(tmp_path: Path) -> WebLayout:
    return WebLayout(tmp_path / "home" / ".deep-reasoning" / "web")


@pytest.fixture
def uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> StubUv:
    stub = tmp_path / "stub-bin" / "uv"
    stub.parent.mkdir()
    stub.write_text(STUB_UV.format(python=sys.executable))
    stub.chmod(0o755)
    log = tmp_path / "uv-calls.jsonl"
    monkeypatch.setenv("STUB_LOG", str(log))
    return StubUv(stub, log)


def web_tarball(
    path: Path,
    *,
    name: str = cache.PACKAGE_NAME,
    version: str = cli.RELEASE,
    extra: tarfile.TarInfo | None = None,
) -> Path:
    """A tarball as build.py web packs it, as far as dr-web reads it."""
    members = {
        "package/package.json": json.dumps({"name": name, "version": version}).encode(),
        "package/bin/deep-reasoning.mjs": ENTRY_SOURCE,
    }
    with tarfile.open(path, "w:gz") as archive:
        for member, data in members.items():
            info = tarfile.TarInfo(member)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        if extra is not None:
            archive.addfile(extra, io.BytesIO(b"x" * extra.size))
    return path


class Release:
    """A directory served on 127.0.0.1 as RELEASES/download/v<version>/<file>."""

    def __init__(self, root: Path) -> None:
        self.root = root
        handler = lambda *a: http.server.SimpleHTTPRequestHandler(
            *a, directory=str(root)
        )
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/releases"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def publish(self, version: str) -> Path:
        folder = self.root / "releases" / "download" / f"v{version}"
        folder.mkdir(parents=True, exist_ok=True)
        return web_tarball(folder / cache.tarball_name(version), version=version)

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Release]:
    served = Release(tmp_path / "served")
    monkeypatch.setattr(cache, "RELEASES", served.url)
    try:
        yield served
    finally:
        served.stop()


def test_the_command_is_dr_webs_at_a_commit_and_its_constants_are_the_builds():
    assert cli.command_for(COMMIT) == (
        "uvx --from git+https://github.com/michaeltheologitis/deep-reasoning"
        f"@{COMMIT}#subdirectory=packages/dr-web deep-reasoning"
    )
    for not_a_commit in ("v1.0.0", COMMIT[:7], COMMIT.upper()):
        with pytest.raises(ValueError):
            cli.command_for(not_a_commit)
    pins = build.load_pins(build.PINS)
    assert cli.REPOSITORY == build.DEEP_REASONING
    assert cli.RELEASE == pins.app.version
    assert cache.PACKAGE_NAME == build.WEB_PACKAGE_NAME
    assert cache.tarball_name("1.2.3") == build.web_tarball_name("1.2.3")
    assert cache.ROOT_DIRNAME == app_layout.ROOT_DIRNAME
    dev = tomllib.loads((ROOT / "pyproject.toml").read_text())["dependency-groups"]
    assert f"{cache.NODE_WHEEL}=={cache.NODE_VERSION}" in dev["dev"]


def test_a_release_tarball_downloads_once_and_a_restart_needs_no_server(web, release):
    published = release.publish(cli.RELEASE)
    said: list[str] = []
    first = cache.unpacked(
        web,
        cache.released_tarball(web, cli.RELEASE, log=said.append),
        expect_version=cli.RELEASE,
    )
    release.stop()
    again = cache.unpacked(
        web,
        cache.released_tarball(web, cli.RELEASE, log=said.append),
        expect_version=cli.RELEASE,
    )
    assert said == [texts.fetching(cli.RELEASE)]
    assert first == again
    assert (first / "bin" / "deep-reasoning.mjs").read_bytes() == ENTRY_SOURCE
    assert web.downloaded(cli.RELEASE).read_bytes() == published.read_bytes()


def symlink(name: str, target: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    return info


def member(name: str) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = 1
    return info


@pytest.mark.parametrize(
    ("make", "expect_version", "reason"),
    [
        (lambda p: None, None, "it cannot be read: No such file or directory"),
        (lambda p: p.write_bytes(b"not a tarball"), None, "not gzip"),
        (
            lambda p: p.write_bytes(gzip.compress(b"not a tar archive")),
            None,
            "not a tar archive",
        ),
        (
            lambda p: web_tarball(p, extra=member("../x")),
            None,
            "a member outside package/",
        ),
        (
            lambda p: web_tarball(p, extra=member("/etc/x")),
            None,
            "a member outside package/",
        ),
        (
            lambda p: web_tarball(p, extra=symlink("package/out", "../../../etc")),
            None,
            "unsafe member package/out",
        ),
        (
            lambda p: web_tarball(p, name="left-pad", version="1.3.0"),
            None,
            "its package.json names left-pad 1.3.0",
        ),
        (
            lambda p: web_tarball(p, version="0.9.0"),
            cli.RELEASE,
            f"its package.json names {cache.PACKAGE_NAME} 0.9.0",
        ),
    ],
    ids=[
        "missing",
        "not-gzip",
        "not-tar",
        "dot-dot",
        "absolute",
        "symlink-out",
        "another-package",
        "another-version",
    ],
)
def test_a_file_that_is_not_the_tarball_is_refused_and_leaves_nothing(
    web, tmp_path, make, expect_version, reason
):
    tarball = tmp_path / "given.tgz"
    make(tarball)
    with pytest.raises(FetchError) as refused:
        cache.unpacked(web, tarball, expect_version=expect_version)
    assert refused.value.exit_code == 23
    assert refused.value.message == texts.not_a_tarball(str(tarball), reason)
    assert list(web.root.glob("tree-*")) == []


def test_a_failed_download_names_the_file_and_keeps_nothing(web, release):
    with pytest.raises(FetchError) as missing:
        cache.released_tarball(web, cli.RELEASE, log=lambda line: None)
    release.stop()
    with pytest.raises(FetchError) as refused:
        cache.released_tarball(web, cli.RELEASE, log=lambda line: None)
    page = release.url.removeprefix("http://") + f"/tag/v{cli.RELEASE}"
    name = cache.tarball_name(cli.RELEASE)
    assert (missing.value.exit_code, missing.value.message) == (
        23,
        texts.fetch_failed(name, page, "HTTP 404"),
    )
    assert refused.value.message == texts.fetch_failed(name, page, "connection refused")
    assert list(web.root.iterdir()) == []


def test_node_installs_once_with_both_hashes_and_working_npm_links(web, uv):
    said: list[str] = []
    node = cache.ensure_node(
        web, uv=str(uv.path), python=sys.executable, log=said.append
    )
    again = cache.ensure_node(
        web, uv=str(uv.path), python=sys.executable, log=said.append
    )
    [call] = uv.calls()
    argv = call["argv"]
    assert argv[:2] == ["pip", "install"]
    assert argv[argv.index("--python") + 1] == sys.executable
    assert {"--target", "--require-hashes", "--no-deps"} <= set(argv)
    assert call["requirements"].split() == [
        f"{cache.NODE_WHEEL}=={cache.NODE_VERSION}",
        *(f"--hash=sha256:{sha}" for sha in cache.NODE_WHEEL_SHA256),
    ]
    assert node == again == web.node
    for name, target in cache.NPM_LINKS.items():
        link = node.parent / name
        assert link.readlink() == Path(target)
        assert link.resolve().is_file()
    assert said == [
        texts.installing_node(cache.NODE_VERSION),
        "Resolved 1 package",
        "Installed 1 package",
        "v22.12.0",
    ]
    assert list(web.root.iterdir()) == [web.node_dir]


@pytest.mark.parametrize(
    ("failing", "step", "code"),
    [
        ({"STUB_UV_EXIT": "2"}, "uv pip install", "2"),
        ({"STUB_NODE_VERSION": "v20.11.1"}, "node --version", "0"),
    ],
    ids=["install", "another-node"],
)
def test_a_failed_node_install_leaves_no_folder(
    web, uv, monkeypatch, failing, step, code
):
    for name, value in failing.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(FetchError) as failed:
        cache.ensure_node(web, uv=str(uv.path), python=sys.executable, log=print)
    assert (failed.value.exit_code, failed.value.message) == (
        23,
        texts.node_failed(step, code),
    )
    assert list(web.root.iterdir()) == []


def test_leftovers_of_a_start_that_died_are_removed_and_a_running_ones_kept(web):
    running = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    dead = subprocess.Popen([sys.executable, "-c", ""])
    dead.wait()
    try:
        for pid in (running.pid, dead.pid):
            (web.root / f"tree-0123456789abcdef.tmp-{pid}" / "package").mkdir(
                parents=True
            )
            (web.root / f"{cache.tarball_name('1.0.0')}.tmp-{pid}").write_text("")
        cache.remove_leftovers(web)
    finally:
        running.kill()
        running.wait()
    assert sorted(p.name for p in web.root.iterdir()) == [
        f"{cache.tarball_name('1.0.0')}.tmp-{running.pid}",
        f"tree-0123456789abcdef.tmp-{running.pid}",
    ]


@pytest.mark.parametrize("uvx_elsewhere", [True, False])
def test_the_stack_path_puts_node_first_and_drops_uvxs_environment(
    tmp_path, uvx_elsewhere
):
    node_bin, tool_bin, user_bin, uv_bin = (
        tmp_path / name for name in ("node", "tool", "user", "uv")
    )
    for folder in (user_bin, uv_bin):
        folder.mkdir()
    if uvx_elsewhere:
        (user_bin / "uvx").write_text("")
        (user_bin / "uvx").chmod(0o755)
    path = os.pathsep.join(map(str, [tool_bin, user_bin, "/usr/bin"]))
    stacked = cli.stack_path(
        path, node_bin=node_bin, tool_bin=tool_bin, uv=str(uv_bin / "uv")
    )
    expected = [node_bin, user_bin, "/usr/bin", *([] if uvx_elsewhere else [uv_bin])]
    assert stacked == os.pathsep.join(map(str, expected))


class Execed(Exception):
    pass


def test_main_execs_the_entry_with_the_flags_given(tmp_path, uv, monkeypatch, capsys):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("UV", str(uv.path))
    execed: list = []

    def execve(path, argv, env):
        execed.append((path, argv, env))
        raise Execed

    monkeypatch.setattr(os, "execve", execve)
    tarball = web_tarball(tmp_path / "built.tgz", version="0.0.0-local")
    with pytest.raises(Execed):
        cli.main(["--tarball", str(tarball), "--port", "8765", "--no-open"])
    [(path, argv, env)] = execed
    web = WebLayout.default()
    [tree] = web.root.glob("tree-*")
    entry = tree / "package" / "bin" / "deep-reasoning.mjs"
    assert path == str(web.node) == argv[0]
    assert argv[1:] == [str(entry), "--port", "8765", "--no-open"]
    assert env["PATH"] == cli.stack_path(
        os.environ["PATH"],
        node_bin=web.node.parent,
        tool_bin=Path(sys.executable).parent,
        uv=str(uv.path),
    )
    assert (home / ".deep-reasoning").stat().st_mode & 0o777 == 0o700
    assert capsys.readouterr().out.splitlines()[0] == texts.installing_node(
        cache.NODE_VERSION
    )


def test_main_without_uv_says_how_to_run_it_and_exits_22(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("UV", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "nothing"))
    assert cli.main(["--no-open"]) == 22
    assert capsys.readouterr().out == texts.NO_UV + "\n"


def test_a_bad_option_exits_2(capsys):
    with pytest.raises(SystemExit) as refused:
        cli.main(["--port", "eighty"])
    assert refused.value.code == 2


@pytest.fixture
def ca(tmp_path: Path) -> Path:
    """A self-signed certificate for 127.0.0.1 that is also its own CA, as PEM; its key
    beside it in key.pem."""
    pem = tmp_path / "ca.pem"
    subprocess.run(
        [
            *("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes"),
            *("-keyout", str(tmp_path / "key.pem"), "-out", str(pem), "-days", "1"),
            *("-subj", "/CN=127.0.0.1", "-addext", "subjectAltName=IP:127.0.0.1"),
            *("-addext", "basicConstraints=critical,CA:TRUE"),
        ],
        check=True,
        capture_output=True,
    )
    return pem


@pytest.fixture
def https(ca: Path) -> Iterator[str]:
    handler = lambda *a: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(ca.parent)
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    served = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    served.load_cert_chain(ca, ca.parent / "key.pem")
    server.socket = served.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"https://127.0.0.1:{server.server_address[1]}/ca.pem"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.skipif(shutil.which("openssl") is None, reason="makes a CA with openssl")
def test_tls_falls_back_to_a_system_bundle_when_the_default_store_is_empty(
    tmp_path, ca, https, monkeypatch
):
    """As on a python.org interpreter whose "Install Certificates" never ran."""
    empty = tmp_path / "no-certificates"
    empty.mkdir()
    monkeypatch.setenv("SSL_CERT_FILE", str(empty / "none.pem"))
    monkeypatch.setenv("SSL_CERT_DIR", str(empty))
    with pytest.raises(urllib.error.URLError, match="CERTIFICATE_VERIFY_FAILED"):
        urllib.request.urlopen(https, context=cache.tls_context(fallbacks=()))
    fallback = cache.tls_context(fallbacks=(str(tmp_path / "missing.pem"), str(ca)))
    with urllib.request.urlopen(https, context=fallback) as response:
        assert response.status == 200
