"""Where the app keeps everything, where the user's data lives, and what setup last did
(D5 §1, §4.4.1)."""

import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal

from dr_app import texts

ROOT_DIRNAME: Final = ".deep-reasoning"
CANVAS_DIRNAME: Final = "canvas"  # the agent-server's persistence root
STATE_DIRNAME: Final = "agent-canvas"  # C3's state directory, inside it
NETWORK_HOME_TEMPLATE: Final = "/var/tmp/deep-reasoning-{uid}"
# D2's store.NETWORK_FILESYSTEMS; tests/app/test_layout.py pins that they are equal.
NETWORK_FILESYSTEMS: Final = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)
MOUNTS: Final = Path("/proc/self/mounts")
# sun_path's size less its terminating NUL: the longest path a Unix socket can bind.
SOCKET_PATH_MAX: Final = {"Linux": 107, "Darwin": 103}
# The deepest socket setup makes room for under DR_HOME: a Claude-backed reasoner serves
# <run_dir>/repl.sock (deep_reasoner), D1 runs it in runs/<run id>, and each Claude
# sub-agent it spawns serves from children/<n> below it; room for one such level.
DEEPEST_SOCKET: Final = "runs/20261004-173501-a1b2c3/children/1000/repl.sock"
EXIT_HOME: Final = 13
EXIT_STATE: Final = 14  # setup.json unusable: a newer app's, or damaged
SETUP_STATE_VERSION: Final = 1


class SetupError(Exception):
    """A failure setup has explained; main() prints message and exits with exit_code.
    dr_app.runtime exports it too."""

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


@dataclass(frozen=True)
class AppLayout:
    root: Path

    @classmethod
    def default(cls) -> "AppLayout":
        """Path.home() / ROOT_DIRNAME."""
        return cls(Path.home() / ROOT_DIRNAME)

    @property
    def canvas(self) -> Path:
        return self.root / CANVAS_DIRNAME

    @property
    def state_dir(self) -> Path:
        return self.canvas / STATE_DIRNAME

    @property
    def runtime_dir(self) -> Path:
        return self.root / "runtime"

    @property
    def current_runtime(self) -> Path:
        return self.runtime_dir / "current"

    @property
    def bin_dir(self) -> Path:
        return self.root / "bin"

    @property
    def canvas_app_dir(self) -> Path:
        return self.root / "canvas-app"

    @property
    def setup_file(self) -> Path:
        return self.root / "setup.json"

    @property
    def lock_file(self) -> Path:
        return self.root / "setup.lock"


@dataclass(frozen=True)
class HomeChoice:
    path: Path
    reason: Literal["recorded", "default", "network-home"]
    filesystem: str | None  # Linux only


def filesystem_type(path: Path, *, mounts: Path = MOUNTS) -> str | None:
    """The type of the longest mount point prefixing path.resolve(); None off Linux."""
    if not mounts.exists():
        return None
    resolved = path.resolve()
    best: tuple[int, str] | None = None
    for line in mounts.read_text().splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        # The kernel escapes spaces, tabs, newlines and backslashes in mount points.
        point = Path(re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), fields[1]))
        if resolved.is_relative_to(point) and (
            best is None or len(point.parts) > best[0]
        ):
            best = (len(point.parts), fields[2])
    return best[1] if best else None


def deepest_socket(home: Path) -> int:
    """The length in bytes of the deepest socket path setup makes room for under home."""
    return len(os.fsencode(home / DEEPEST_SOCKET))


def check_socket_room(home: Path, *, system: str) -> None:
    """Raises SetupError(13, texts.home_too_long(...)) when a Claude run's socket under
    home would be longer than the system lets a socket bind."""
    limit = SOCKET_PATH_MAX.get(system)
    deepest = deepest_socket(home)
    if limit is not None and deepest > limit:
        raise SetupError(
            EXIT_HOME, texts.home_too_long(str(home), str(deepest), str(limit))
        )


def _is_private_dir_of(path: Path, uid: int) -> bool:
    """A real directory (not a link) owned by uid, with no group or other permission."""
    info = path.lstat()
    return (
        stat.S_ISDIR(info.st_mode)
        and info.st_uid == uid
        and stat.S_IMODE(info.st_mode) & 0o077 == 0
    )


def choose_home(
    layout: AppLayout,
    recorded: Path | None,
    *,
    system: str,
    uid: int,
    mounts: Path = MOUNTS,
    var_tmp: Path = Path(NETWORK_HOME_TEMPLATE).parent,
) -> HomeChoice:
    """§4.4.1: a recorded home that is still a local directory of ours; else the root,
    unless (Linux) it is on a network filesystem; else /var/tmp/deep-reasoning-<uid>.
    Raises SetupError(13, texts.home_unsafe(...)) for a /var/tmp directory that is not
    ours, and SetupError(13, texts.home_too_long(...)) for a home too long for a Claude
    run's socket."""
    choice = _choose_home(
        layout, recorded, system=system, uid=uid, mounts=mounts, var_tmp=var_tmp
    )
    check_socket_room(choice.path, system=system)
    return choice


def _choose_home(
    layout: AppLayout,
    recorded: Path | None,
    *,
    system: str,
    uid: int,
    mounts: Path,
    var_tmp: Path,
) -> HomeChoice:
    linux = system == "Linux"
    if recorded is not None and recorded.is_dir() and recorded.stat().st_uid == uid:
        fstype = filesystem_type(recorded, mounts=mounts) if linux else None
        if fstype not in NETWORK_FILESYSTEMS:
            return HomeChoice(recorded, "recorded", fstype)
    fstype = filesystem_type(layout.root, mounts=mounts) if linux else None
    if fstype not in NETWORK_FILESYSTEMS:
        return HomeChoice(layout.root, "default", fstype)
    home = var_tmp / Path(NETWORK_HOME_TEMPLATE.format(uid=uid)).name
    if not home.exists() and not home.is_symlink():
        home.mkdir(mode=0o700)
        home.chmod(0o700)
    elif not _is_private_dir_of(home, uid):
        info = home.lstat()
        raise SetupError(
            EXIT_HOME,
            texts.home_unsafe(
                str(home), str(info.st_uid), oct(stat.S_IMODE(info.st_mode))
            ),
        )
    return HomeChoice(home, "network-home", fstype)


@dataclass
class RuntimeRecord:
    commit: str
    lock_sha256: str
    path: str


@dataclass
class ProfileRecord:
    id: str
    activated_by_setup: bool


@dataclass
class CanvasAppRecord:
    digest: str
    version: str


@dataclass
class SetupState:
    v: int
    dr_home: str | None
    runtime: RuntimeRecord | None
    profile: ProfileRecord | None
    canvas_app: CanvasAppRecord | None

    @classmethod
    def load(cls, path: Path) -> "SetupState":
        """A fresh state when the file is absent. Raises SetupError(14, ...) with
        texts.state_from_a_newer_app for a version above 1, and texts.state_unusable,
        saying why, for a file no version of this app writes."""
        if not path.exists():
            return cls(SETUP_STATE_VERSION, None, None, None, None)

        def unusable(reason: str) -> SetupError:
            return SetupError(EXIT_STATE, texts.state_unusable(str(path), reason))

        try:
            raw = json.loads(path.read_text())
        except OSError as error:
            raise unusable(f"it cannot be read ({error.strerror})") from None
        except ValueError:  # JSONDecodeError, UnicodeDecodeError
            raise unusable("it is not JSON") from None
        if not isinstance(raw, dict):
            raise unusable("it is not a JSON object")
        version = raw.get("v")
        if isinstance(version, int) and version > SETUP_STATE_VERSION:
            raise SetupError(
                EXIT_STATE, texts.state_from_a_newer_app(str(path), str(version))
            )
        if version != SETUP_STATE_VERSION:
            shown = f"its version is {json.dumps(version)}"
            raise unusable(shown if "v" in raw else "it has no version")

        def record[T](kind: type[T], key: str) -> T | None:
            return kind(**raw[key]) if raw.get(key) else None

        try:
            return cls(
                SETUP_STATE_VERSION,
                raw.get("dr_home"),
                record(RuntimeRecord, "runtime"),
                record(ProfileRecord, "profile"),
                record(CanvasAppRecord, "canvas_app"),
            )
        except TypeError:
            raise unusable("it holds a record this app does not write") from None

    def save(self, path: Path) -> None:
        """Atomic: a temporary file, then rename."""
        temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
        temporary.write_text(json.dumps(asdict(self), indent=2) + "\n")
        temporary.replace(path)
