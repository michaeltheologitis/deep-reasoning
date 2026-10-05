"""The README's install section names what the build and setup really use (D5 §2.3,
§4.2.6, §4.8.3, §3 item 12): the app, its packages, the key, the commands, the paths."""

import importlib.util
import os
import re
import shlex
from pathlib import Path

from dr_app import cli, layout, profile, texts
from dr_app.runtime import RuntimeSpec, git_environment

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("build", ROOT / "desktop" / "build.py")
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

PINS = build.load_pins(build.PINS)
README = (ROOT / "README.md").read_text()
# The words, without Markdown's marks or its line breaks.
PLAIN = " ".join(README.replace("`", "").replace("**", "").split())


def test_the_mac_steps_name_the_package_and_the_app_the_build_produces():
    app = PINS.app
    assert f"{app.executable_name}-<version>-{build.MAC_ARCH}.dmg" in PLAIN
    assert f"macOS {build.MAC_MINIMUM.removesuffix('.0')} or later" in PLAIN
    command = f'xattr -dr com.apple.quarantine "/Applications/{app.product_name}.app"'
    assert command in README


def test_the_key_is_the_one_setup_asks_for_where_setup_says():
    asked = re.fullmatch(
        r".*: (add (\S+) under (.+)) before your first question\.", texts.NO_MODEL_KEY
    )
    assert asked is not None and asked[2] == cli.MODEL_KEY
    assert asked[1] in PLAIN


def test_the_access_check_is_the_one_setup_runs():
    url = RuntimeSpec.for_commit(build.DEEP_REASONING, "0" * 40).deep_reasoner_url
    env = [
        f"{name}={shlex.quote(value)}" for name, value in git_environment({}).items()
    ]
    assert " ".join([*env, "git", "ls-remote", url, "HEAD"]) in README


def test_the_terminal_commands_are_the_ones_setup_links():
    bin_dir = f"$HOME/{layout.ROOT_DIRNAME}/bin"
    assert f'export PATH="{bin_dir}:$PATH"' in README
    for name in cli.LINKED:
        assert f"`{name}`" in README
    assert "dr-app export DIR" in PLAIN and "dr-app home" in PLAIN


def test_uninstall_removes_what_the_app_writes():
    assert f"rm -rf ~/{layout.ROOT_DIRNAME}" in README
    assert layout.NETWORK_HOME_TEMPLATE.format(uid="<uid>") in PLAIN
    assert f"sudo apt remove {PINS.app.executable_name}" in README


def test_the_safety_section_quotes_setup_with_the_cap_setup_sets():
    cap = profile.DEFAULT_SPEND_CAP_USD
    assert texts.safety(cap) in PLAIN
    assert f"{profile.SPEND_CAP_FLAG} {cap}" in PLAIN


def section(heading: str) -> str:
    """The README's text from a heading to the next heading."""
    return README.split(f"\n{heading}\n", 1)[1].split("\n#", 1)[0]


def test_the_data_table_names_everything_setup_keeps_in_the_root():
    root = layout.AppLayout(Path("~") / layout.ROOT_DIRNAME)
    kept = {
        path.name
        for name, member in vars(layout.AppLayout).items()
        if isinstance(member, property)
        and (path := getattr(root, name)).parent == root.root
    }
    named = {
        Path(code.rstrip("/")).name
        for code in re.findall(r"`([^`]+)`", section("### Where your data lives"))
    }
    assert kept <= named


def test_dr_app_home_says_how_long_a_folder_may_be():
    below = len(os.fsencode(f"/{layout.DEEPEST_SOCKET}"))
    linux, mac = (layout.SOCKET_PATH_MAX[s] - below for s in ("Linux", "Darwin"))
    assert f"at most {linux} bytes on Linux and {mac} on macOS" in PLAIN
