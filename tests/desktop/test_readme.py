"""The README's install section names what the build and setup really use (D5 §2.3,
§4.2.6, §4.8.3, §3 item 12): the app, its packages, the key, the commands, the paths;
and its browser section, what the browser command does (TASK-48 §3.5)."""

import os
import re
import shlex
from importlib import resources
from pathlib import Path

import pytest
import yaml

from deep_reasoning.acp import texts as acp_texts
from desktop import build
from dr_app import cli, layout, profile
from dr_app.runtime import deep_reasoner_pin, git_environment
from dr_web.cache import WEB_DIRNAME
from dr_web.cli import command_for
from tests.desktop.app import evaluate_web

ROOT = Path(__file__).resolve().parents[2]

PINS = build.load_pins(build.PINS)
README = (ROOT / "README.md").read_text()


def plain(text: str) -> str:
    """The words, without Markdown's marks or its line breaks."""
    return " ".join(text.replace("`", "").replace("**", "").split())


PLAIN = plain(README)


def test_the_mac_steps_name_the_package_and_the_app_the_build_produces():
    app = PINS.app
    assert f"{app.executable_name}-<version>-{build.MAC_ARCH}.dmg" in PLAIN
    assert f"macOS {build.MAC_MINIMUM.removesuffix('.0')} or later" in PLAIN
    command = f'xattr -dr com.apple.quarantine "/Applications/{app.product_name}.app"'
    assert command in README


def test_the_key_is_the_one_dr_acp_asks_for_where_it_says():
    starter = resources.files("deep_reasoning.library").joinpath("starter.yaml")
    key = yaml.safe_load(starter.read_text())["client"]["api_key_env"]
    place = re.search(r"add it under (.+), then", acp_texts.missing_model_key([key]))
    assert place is not None
    assert f"add {key} under {place[1]}" in PLAIN


def test_the_access_check_is_the_one_setup_runs():
    url = deep_reasoner_pin(ROOT).url
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


def section(heading: str) -> str:
    """The README's text from a heading to the next heading."""
    return README.split(f"\n{heading}\n", 1)[1].split("\n#", 1)[0]


def test_the_cap_section_names_the_default_cap_and_the_field_the_refusal_names():
    field = re.search(r"under (.+)\.$", acp_texts.cap_reached(5.01, 5))
    assert field is not None
    cap_section = plain(section("## What the app protects, and what it does not"))
    assert (
        f"The cap is ${profile.DEFAULT_SPEND_CAP_USD} per conversation unless you change "
        f"it under {field[1]}."
    ) in cap_section


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


# The browser version (TASK-48 §3.5).
BROWSER = "## Run it in your browser"
COMMAND_AT = re.compile(
    re.escape(command_for("0" * 40)).replace("0" * 40, "(?P<commit>[0-9a-f]{40})")
)


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    words = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return words.replace(" ", "-")


def test_the_browser_command_is_dr_webs_at_a_commit_or_the_checkout_form():
    """One command per release, at its commit (W1); before the first, the form for a
    tarball built from a checkout."""
    commands = COMMAND_AT.findall(README)
    if commands:
        assert len(commands) == 1
        return
    checkout_form = command_for("0" * 40).replace("0" * 40, "<commit>")
    tarball = build.web_tarball_name("<version>")
    assert f"{checkout_form} --tarball dist/{tarball}" in section(BROWSER)
    assert "uv run desktop/build.py web" in section(BROWSER)


def test_the_browser_section_names_its_flags_ports_cache_and_uv():
    words = plain(section(BROWSER))
    for named in (
        "--port",
        "--no-open",
        "18000",
        "Ctrl+C",
        "~/.deep-reasoning/web",
        "ten minutes",
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
        f"uv {evaluate_web('web.MINIMUM.uv')} or later",
    ):
        assert named in words, named


def test_the_browser_sections_links_to_other_headings_resolve():
    anchors = {slug(h) for h in re.findall(r"^#+ (.+)$", README, re.MULTILINE)}
    linked = re.findall(r"\]\(#([^)]+)\)", section(BROWSER))
    assert linked
    assert [anchor for anchor in linked if anchor not in anchors] == []


def test_the_data_table_names_the_browser_cache():
    table = section("### Where your data lives")
    assert f"`~/{layout.ROOT_DIRNAME}/{WEB_DIRNAME}/`" in table


@pytest.mark.crossrepo
def test_the_readmes_browser_command_is_the_newest_releases():
    """W14: the tagged commit cannot name itself, so the README is updated after each
    tag; until it is, the nightly check fails. None before the first tag."""
    tags = build.git("tag", "-l", "v*", "--sort=-v:refname", cwd=ROOT).split()
    commands = COMMAND_AT.findall(README)
    if not tags:
        assert commands == []
        return
    newest = build.git("rev-list", "-n", "1", tags[0], cwd=ROOT).strip()
    assert commands == [newest], f"the README's command is not {tags[0]}'s ({newest})"


def test_no_section_promises_an_offline_restart_past_ten_minutes():
    """The agent-server's start asks PyPI again once uv's answers expire (TASK-48 F4),
    for the app as for the browser, until TASK-66."""
    window = "Within about ten minutes of the last start that had the network"
    first_launch = " ".join(section("### The first launch").split())
    browser = " ".join(section(BROWSER).split())
    assert window in first_launch and window in browser
    assert "needs no network" not in PLAIN
