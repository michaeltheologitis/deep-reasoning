import os
import socket
import stat
import sys
from pathlib import Path

import pytest

from deep_reasoning.library import store
from dr_app import texts
from dr_app.layout import (
    NETWORK_FILESYSTEMS,
    SOCKET_PATH_MAX,
    AppLayout,
    CanvasAppRecord,
    HomeChoice,
    ProfileRecord,
    RuntimeRecord,
    SetupError,
    SetupState,
    check_socket_room,
    choose_home,
    deepest_socket,
)

UID = os.getuid()


@pytest.fixture
def mounts(tmp_path, layout):
    """A /proc/self/mounts: / on ext4; the test puts its home on whatever it likes."""

    def write(home_fstype: str):
        path = tmp_path / "mounts"
        home = layout.root.parent
        path.write_text(
            "/dev/sda1 / ext4 rw 0 0\n"
            f"server:/export {str(home).replace(' ', '\\040')} {home_fstype} rw 0 0\n"
        )
        return path

    return write


def test_the_default_home_is_the_root_when_it_is_local(layout, mounts):
    linux = choose_home(layout, None, system="Linux", uid=UID, mounts=mounts("ext4"))
    assert linux == HomeChoice(layout.root, "default", "ext4")
    macos = choose_home(layout, None, system="Darwin", uid=UID, mounts=mounts("nfs4"))
    assert macos == HomeChoice(layout.root, "default", None)


def test_a_network_home_moves_the_data_to_var_tmp(layout, mounts):
    var_tmp = layout.root.parents[1] / "var-tmp"
    var_tmp.mkdir()
    choice = choose_home(
        layout, None, system="Linux", uid=UID, mounts=mounts("nfs4"), var_tmp=var_tmp
    )
    assert choice == HomeChoice(
        var_tmp / f"deep-reasoning-{UID}", "network-home", "nfs4"
    )
    assert stat.S_IMODE(choice.path.stat().st_mode) == 0o700
    again = choose_home(
        layout, None, system="Linux", uid=UID, mounts=mounts("nfs4"), var_tmp=var_tmp
    )
    assert again == choice


@pytest.mark.parametrize("unsafe", ["link", "other-owner", "mode-0755"])
def test_a_var_tmp_directory_not_ours_is_refused(tmp_path, layout, mounts, unsafe):
    var_tmp = tmp_path / "var-tmp"
    var_tmp.mkdir()
    uid = UID + 1 if unsafe == "other-owner" else UID
    shared = var_tmp / f"deep-reasoning-{uid}"
    if unsafe == "link":
        (tmp_path / "theirs").mkdir(mode=0o700)
        shared.symlink_to(tmp_path / "theirs")
    else:
        shared.mkdir()
        shared.chmod(0o755 if unsafe == "mode-0755" else 0o700)
    with pytest.raises(SetupError) as refused:
        choose_home(
            layout, None, system="Linux", uid=uid, mounts=mounts("nfs"), var_tmp=var_tmp
        )
    info = shared.lstat()
    assert refused.value.exit_code == 13
    assert refused.value.message == texts.home_unsafe(
        str(shared), str(info.st_uid), oct(stat.S_IMODE(info.st_mode))
    )


def test_a_recorded_home_is_kept(tmp_path, layout, mounts):
    chosen = layout.root.parents[1] / "chosen"
    chosen.mkdir()
    kept = choose_home(layout, chosen, system="Linux", uid=UID, mounts=mounts("ext4"))
    assert kept == HomeChoice(chosen, "recorded", "ext4")
    gone = choose_home(
        layout, tmp_path / "deleted", system="Linux", uid=UID, mounts=mounts("ext4")
    )
    assert gone.reason == "default"


def test_our_network_filesystems_are_d2s():
    assert NETWORK_FILESYSTEMS == store.NETWORK_FILESYSTEMS


def test_setup_state_round_trips_and_writes_atomically(layout):
    layout.root.mkdir(parents=True)
    assert SetupState.load(layout.setup_file) == SetupState(1, None, None, None, None)
    state = SetupState(
        1,
        "/data",
        RuntimeRecord("c" * 40, "d" * 64, "/r/c"),
        ProfileRecord("p-1", True),
        CanvasAppRecord("e" * 64, "0.1.0"),
    )
    state.save(layout.setup_file)
    assert SetupState.load(layout.setup_file) == state
    assert sorted(p.name for p in layout.root.iterdir()) == ["setup.json"]


# The run directory's socket for the default homes: Linux's longest user name (32), the
# network home's largest uid, a macOS user name at the limit and one past it, and a HOME
# under macOS's $TMPDIR (a test's or a CI runner's).
SOCKET_ROOM = [
    ("Linux", "/home/" + "u" * 32 + "/.deep-reasoning", 106),
    ("Linux", "/var/tmp/deep-reasoning-4294967294", 86),
    ("Darwin", "/Users/" + "u" * 28 + "/.deep-reasoning", 103),
    ("Darwin", "/Users/" + "u" * 29 + "/.deep-reasoning", 104),
    (
        "Darwin",
        "/var/folders/7c/k_q9qkjn0zv_l1z_pdshdn9h0000gn/T/tmp.k3j2/home/.deep-reasoning",
        130,
    ),
]


@pytest.mark.parametrize(("system", "home", "deepest"), SOCKET_ROOM)
def test_a_home_too_long_for_a_claude_runs_socket_is_refused(system, home, deepest):
    assert deepest_socket(Path(home)) == deepest
    limit = SOCKET_PATH_MAX[system]
    if deepest <= limit:
        check_socket_room(Path(home), system=system)
        return
    with pytest.raises(SetupError) as refused:
        check_socket_room(Path(home), system=system)
    assert refused.value.exit_code == 13
    assert refused.value.message == texts.home_too_long(home, str(deepest), str(limit))


def test_setup_refuses_a_default_home_too_long_for_a_claude_runs_socket():
    home = Path("/Users/" + "u" * 29 + "/.deep-reasoning")
    with pytest.raises(SetupError) as refused:
        choose_home(AppLayout(home), None, system="Darwin", uid=UID)
    assert refused.value.message == texts.home_too_long(str(home), "104", "103")


def home_whose_deepest_socket_is(base: Path, length: int) -> Path:
    return base / ("h" * (length - deepest_socket(base / "h") + 1))


@pytest.mark.skipif(
    sys.platform != "linux", reason="binds a socket under Linux's limit"
)
@pytest.mark.parametrize("length", [107, 108])
def test_linuxs_limit_is_where_a_socket_stops_binding(layout, length):
    home = home_whose_deepest_socket_is(layout.root.parent, length)
    socket_path = home / "runs" / "20261004-173501-a1b2c3" / "children" / "1000"
    socket_path.mkdir(parents=True)
    with socket.socket(socket.AF_UNIX) as server:
        if length <= SOCKET_PATH_MAX["Linux"]:
            check_socket_room(home, system="Linux")
            server.bind(str(socket_path / "repl.sock"))
            return
        with pytest.raises(SetupError):
            check_socket_room(home, system="Linux")
        with pytest.raises(OSError, match="AF_UNIX path too long"):
            server.bind(str(socket_path / "repl.sock"))
