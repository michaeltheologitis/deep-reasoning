"""What the browser command keeps under ~/.deep-reasoning/web, and how it gets it: Node,
installed once from its PyPI wheel; the release's tarball, downloaded once; and the
tarball unpacked once per content (TASK-48 §3.1, W2, W4, W5).

Every entry is written under <name>.tmp-<pid> and renamed into place, so two first
starts at once never see half of one. Nothing here deletes a finished entry.
"""

import hashlib
import json
import os
import shutil
import ssl
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dr_web import texts

ROOT_DIRNAME: Final = ".deep-reasoning"  # dr_app.layout.ROOT_DIRNAME, mirrored
WEB_DIRNAME: Final = "web"
RELEASES: Final = "https://github.com/michaeltheologitis/deep-reasoning/releases"
PACKAGE_NAME: Final = "deep-reasoning-web"  # build.WEB_PACKAGE_NAME
ENTRY: Final = "package/bin/deep-reasoning.mjs"
NODE_VERSION: Final = "22.12.0"  # the app's (the Canvas fork's download-node.mjs)
NODE_WHEEL: Final = "nodejs-wheel-binaries"
NODE_WHEEL_SHA256: Final = (  # PyPI, 2024-12-06
    "335176ffa5f753c4d447af83f70987f5f82becdf84fadf56d5c0036379826cff",  # Linux x86-64
    "8ed26eac5a96f3bfcd36f1eb9c397f07392e8b166895e0a65eb6033baefa0217",  # macOS arm64
)
# The wheel's bin/npm and bin/npx are copies of npm's scripts that cannot find npm
# beside them; Node's own distribution links them into npm's package instead.
NPM_LINKS: Final = {
    "npm": "../lib/node_modules/npm/bin/npm-cli.js",
    "npx": "../lib/node_modules/npm/bin/npx-cli.js",
}
FALLBACK_CA_FILES: Final = (
    "/etc/ssl/cert.pem",  # macOS
    "/etc/ssl/certs/ca-certificates.crt",  # Debian, Ubuntu
    "/etc/pki/tls/certs/ca-bundle.crt",  # Fedora, RHEL
)
DOWNLOAD_TIMEOUT_S: Final = 60.0
EXIT_FETCH: Final = 23
GZIP_MAGIC: Final = b"\x1f\x8b"
READ_CHUNK: Final = 1 << 20


class FetchError(Exception):
    """A failure dr-web explains: its message is printed and the command exits with
    exit_code (22 or 23)."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


@dataclass(frozen=True)
class WebLayout:
    root: Path  # ~/.deep-reasoning/web

    @classmethod
    def default(cls) -> "WebLayout":
        """Path.home() / ROOT_DIRNAME / WEB_DIRNAME."""
        return cls(Path.home() / ROOT_DIRNAME / WEB_DIRNAME)

    def downloaded(self, version: str) -> Path:
        return self.root / tarball_name(version)

    def tree(self, sha256: str) -> Path:
        """Where a tarball whose SHA-256 is sha256 is unpacked."""
        return self.root / f"tree-{sha256[:16]}"

    @property
    def node_dir(self) -> Path:
        return self.root / f"node-{NODE_VERSION}"

    @property
    def node(self) -> Path:
        return self.node_dir / "nodejs_wheel" / "bin" / "node"


def tarball_name(version: str) -> str:
    """build.web_tarball_name, mirrored."""
    return f"{PACKAGE_NAME}-{version}.tgz"


def release_url(version: str) -> str:
    return f"{RELEASES}/download/v{version}/{tarball_name(version)}"


def tls_context(*, fallbacks: Sequence[str] = FALLBACK_CA_FILES) -> ssl.SSLContext:
    """ssl.create_default_context(); when its store holds no CA certificate (a
    python.org interpreter before "Install Certificates" runs), the first fallback that
    exists is loaded into it as well. An OpenSSL that reads a hashed capath lazily also
    reports none; loading the bundle beside it then changes nothing."""
    context = ssl.create_default_context()
    if context.cert_store_stats()["x509_ca"] == 0:
        bundle = next((path for path in fallbacks if Path(path).is_file()), None)
        if bundle is not None:
            context.load_verify_locations(cafile=bundle)
    return context


def download(url: str, dest: Path, *, timeout_s: float = DOWNLOAD_TIMEOUT_S) -> None:
    """dest, written whole or not at all. Raises FetchError(23,
    texts.fetch_failed(dest.name, <the release page>, <reason>)) for an HTTP status, a
    refused or timed-out connection, or TLS."""
    temporary = _temporary(dest)
    try:
        with (
            urllib.request.urlopen(
                url, timeout=timeout_s, context=tls_context()
            ) as got,
            temporary.open("wb") as out,
        ):
            shutil.copyfileobj(got, out, READ_CHUNK)
    except OSError as error:  # ssl.SSLError and urllib's errors among them
        _remove(temporary)
        failed = texts.fetch_failed(dest.name, _release_page(url), _why(error))
        raise FetchError(EXIT_FETCH, failed) from None
    _place(temporary, dest)


def released_tarball(
    layout: WebLayout, version: str, *, log: Callable[[str], None]
) -> Path:
    """layout.downloaded(version) if present, asking no server; else
    texts.fetching(version), then download()."""
    tarball = layout.downloaded(version)
    if tarball.exists():
        return tarball
    log(texts.fetching(version))
    layout.root.mkdir(parents=True, exist_ok=True)
    download(release_url(version), tarball)
    return tarball


def unpacked(layout: WebLayout, tarball: Path, *, expect_version: str | None) -> Path:
    """The tree's package/ folder, unpacked once per content: gzip, every member under
    package/ and safe (tarfile's data filter), package.json naming PACKAGE_NAME (and
    expect_version, for a download; None for --tarball), and the entry there. Raises
    FetchError(23, texts.not_a_tarball(str(tarball), <reason>)), leaving no tree."""
    try:
        tree = layout.tree(_sha256(tarball))
    except OSError as error:
        unreadable = f"it cannot be read: {error.strerror}"
        raise FetchError(
            EXIT_FETCH, texts.not_a_tarball(str(tarball), unreadable)
        ) from None
    if (tree / ENTRY).exists():
        return tree / "package"
    temporary = _temporary(tree)
    try:
        _unpack(tarball, temporary, expect_version=expect_version)
    except _NotOurs as refused:
        _remove(temporary)
        raise FetchError(
            EXIT_FETCH, texts.not_a_tarball(str(tarball), str(refused))
        ) from None
    _place(temporary, tree)
    return tree / "package"


def ensure_node(
    layout: WebLayout, *, uv: str, python: str, log: Callable[[str], None]
) -> Path:
    """layout.node, installed once: the pinned wheel by uv pip install --target with
    both hashes, uv's output passed to log line by line; npm and npx relinked; node
    --version checked. Raises FetchError(23, texts.node_failed(<step>, <code>)),
    leaving no node_dir."""
    if layout.node.exists():
        return layout.node
    log(texts.installing_node(NODE_VERSION))
    layout.root.mkdir(parents=True, exist_ok=True)
    temporary = _temporary(layout.node_dir)
    try:
        _install_node(temporary, uv=uv, python=python, log=log)
    except FetchError:
        _remove(temporary)
        raise
    _place(temporary, layout.node_dir)
    return layout.node


def remove_leftovers(layout: WebLayout) -> None:
    """Every <name>.tmp-<pid> under root whose pid is not alive."""
    if not layout.root.is_dir():
        return
    for entry in layout.root.glob("*.tmp-*"):
        pid = entry.name.rpartition(".tmp-")[2]
        if pid.isdigit() and not _alive(int(pid)):
            _remove(entry)


class _NotOurs(Exception):
    """Why a file is not the browser tarball: the reason in texts.not_a_tarball."""


def _unpack(tarball: Path, into: Path, *, expect_version: str | None) -> None:
    """tarball's package/ into into/package. Raises _NotOurs."""
    with tarball.open("rb") as file:
        if file.read(len(GZIP_MAGIC)) != GZIP_MAGIC:
            raise _NotOurs("not gzip")
    try:
        with tarfile.open(tarball, "r:gz") as archive:
            members = archive.getmembers()
            for member in members:
                if member.name != "package" and not member.name.startswith("package/"):
                    raise _NotOurs("a member outside package/")
            for member in members:
                try:
                    archive.extract(member, into, filter="data")
                except tarfile.FilterError:
                    raise _NotOurs(f"unsafe member {member.name}") from None
    except (tarfile.ReadError, EOFError, OSError):
        raise _NotOurs("not a tar archive") from None
    package = into / "package"
    try:
        manifest = json.loads((package / "package.json").read_text())
    except (OSError, ValueError):
        raise _NotOurs("no package.json") from None
    name, version = manifest.get("name"), manifest.get("version")
    if name != PACKAGE_NAME or expect_version not in (None, version):
        raise _NotOurs(f"its package.json names {name} {version}")
    if not (into / ENTRY).is_file():
        raise _NotOurs("no bin/deep-reasoning.mjs")


def _install_node(
    target: Path, *, uv: str, python: str, log: Callable[[str], None]
) -> None:
    """The wheel into target, npm and npx relinked, node --version checked. Raises
    FetchError naming the step that failed."""
    hashes = [f"--hash=sha256:{sha}" for sha in NODE_WHEEL_SHA256]
    with tempfile.TemporaryDirectory() as scratch:
        requirements = Path(scratch) / "node.txt"
        requirements.write_text(f"{NODE_WHEEL}=={NODE_VERSION} {' '.join(hashes)}\n")
        install = [uv, "pip", "install", "--python", python, "--target", str(target)]
        install += ["--require-hashes", "--no-deps", "-r", str(requirements)]
        code = _run_logged(install, log=log)
    if code != 0:
        raise FetchError(EXIT_FETCH, texts.node_failed("uv pip install", str(code)))
    node_bin = target / "nodejs_wheel" / "bin"
    for name, script in NPM_LINKS.items():
        (node_bin / name).unlink(missing_ok=True)
        (node_bin / name).symlink_to(script)
    checked = subprocess.run(
        [str(node_bin / "node"), "--version"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    for line in (checked.stdout + checked.stderr).splitlines():
        log(line)
    if checked.returncode != 0 or checked.stdout.strip() != f"v{NODE_VERSION}":
        failed = texts.node_failed("node --version", str(checked.returncode))
        raise FetchError(EXIT_FETCH, failed)


def _run_logged(argv: Sequence[str], *, log: Callable[[str], None]) -> int:
    """argv's exit code; stdout and stderr, one pipe, to log line by line."""
    with subprocess.Popen(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    ) as process:
        for line in process.stdout:
            log(line.rstrip("\n"))
    return process.returncode


def _release_page(url: str) -> str:
    """Where a person can find a release's file: its release page, without the scheme
    (github.com/<repo>/releases/tag/v<version>)."""
    folder = url.split("://", 1)[-1].rsplit("/", 1)[0]
    return folder.replace("/releases/download/", "/releases/tag/")


def _why(error: OSError) -> str:
    """HTTP 404, connection refused, timed out, or TLS's own words."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}"
    reason = error.reason if isinstance(error, urllib.error.URLError) else error
    if isinstance(reason, ConnectionRefusedError):
        return "connection refused"
    if isinstance(reason, TimeoutError):
        return "timed out"
    if isinstance(reason, ssl.SSLError):
        return reason.reason or str(reason)
    return str(reason)


def _sha256(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def _temporary(final: Path) -> Path:
    return final.with_name(f"{final.name}.tmp-{os.getpid()}")


def _place(temporary: Path, final: Path) -> None:
    """temporary renamed to final; a final that another start placed first is kept."""
    try:
        temporary.rename(final)
    except OSError:
        if not final.exists():
            raise
        _remove(temporary)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
