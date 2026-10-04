import os
import stat

import pytest

from deep_reasoning.library import store
from dr_app import texts
from dr_app.layout import (
    NETWORK_FILESYSTEMS,
    CanvasAppRecord,
    HomeChoice,
    ProfileRecord,
    RuntimeRecord,
    SetupError,
    SetupState,
    choose_home,
)

UID = os.getuid()


@pytest.fixture
def mounts(tmp_path):
    """A /proc/self/mounts: / on ext4; the test puts its home on whatever it likes."""

    def write(home_fstype: str):
        path = tmp_path / "mounts"
        home = tmp_path / "home"
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


def test_a_network_home_moves_the_data_to_var_tmp(tmp_path, layout, mounts):
    var_tmp = tmp_path / "var-tmp"
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
    chosen = tmp_path / "chosen"
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
    layout.setup_file.write_text('{"v": 2}')
    with pytest.raises(ValueError, match="unknown version"):
        SetupState.load(layout.setup_file)
