import json
import stat

import pytest

from deep_reasoning import settings as settings_module
from deep_reasoning.settings import (
    ENV_FILE,
    NO_KEY,
    SETTINGS_FILE,
    VENDORS,
    SettingsError,
    add_server,
    default_folder,
    drop_key,
    find_provider,
    key_of,
    key_status,
    provider_list,
    remember_pick,
    remove_server,
    run_key,
    save_default_folder,
    save_key,
    saved_keys,
    server_key_env,
    starting_model,
    update_server,
)

pytestmark = pytest.mark.usefixtures("no_vendor_keys")

OPENAI = VENDORS[0]
KEY = "sk-saved-in-settings"
SHELL_KEY = "sk-from-the-shell"
LOCAL_URL = "http://127.0.0.1:8000/v1"
THEIRS = """\
# my own settings
export EDITOR=vim
OPENAI_API_KEY='sk-older'
QUOTED="two words"
"""


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_a_key_saved_in_a_new_env_file_is_readable_by_its_owner_alone(app_home):
    save_key(app_home, OPENAI, f"  {KEY}\n")
    assert mode(app_home / ENV_FILE) == 0o600
    assert (app_home / ENV_FILE).read_text() == f"OPENAI_API_KEY='{KEY}'\n"
    assert saved_keys(app_home) == {"OPENAI_API_KEY": KEY}


def test_saving_a_key_keeps_the_files_other_lines_and_narrows_who_can_read_it(
    app_home,
):
    app_home.mkdir(parents=True)
    env = app_home / ENV_FILE
    env.write_text(THEIRS)
    env.chmod(0o644)
    save_key(app_home, OPENAI, KEY)
    assert env.read_text() == THEIRS.replace("sk-older", KEY)
    assert mode(env) == 0o600
    assert list(app_home.iterdir()) == [env]


def test_a_saved_key_beats_the_shells(app_home, monkeypatch):
    monkeypatch.setenv(OPENAI.key_env, SHELL_KEY)
    assert key_status(OPENAI, saved_keys(app_home)) == "shell"
    save_key(app_home, OPENAI, KEY)
    saved = saved_keys(app_home)
    assert key_status(OPENAI, saved) == "set"
    assert key_of(OPENAI, saved) == KEY == run_key(app_home, OPENAI)


def test_a_shell_key_with_a_stray_line_ending_runs_without_it(app_home, monkeypatch):
    monkeypatch.setenv(OPENAI.key_env, f"{SHELL_KEY}\r\n")
    assert run_key(app_home, OPENAI) == SHELL_KEY


def test_saving_a_key_through_a_symlinked_env_file_leaves_its_target_alone(
    app_home, tmp_path
):
    app_home.mkdir(parents=True)
    target = tmp_path / "dotfiles.env"
    target.write_text(THEIRS)
    target.chmod(0o644)
    (app_home / ENV_FILE).symlink_to(target)
    save_key(app_home, OPENAI, KEY)
    env = app_home / ENV_FILE
    assert not env.is_symlink() and mode(env) == 0o600
    assert env.read_text() == THEIRS.replace("sk-older", KEY)
    assert target.read_text() == THEIRS and mode(target) == 0o644


def test_dropping_a_key_keeps_the_other_lines_and_lets_the_shells_show_again(
    app_home, monkeypatch
):
    app_home.mkdir(parents=True)
    (app_home / ENV_FILE).write_text(THEIRS)
    monkeypatch.setenv(OPENAI.key_env, SHELL_KEY)
    drop_key(app_home, OPENAI.key_env)
    assert (app_home / ENV_FILE).read_text() == THEIRS.replace(
        "OPENAI_API_KEY='sk-older'\n", ""
    )
    assert key_status(OPENAI, saved_keys(app_home)) == "shell"
    drop_key(app_home, OPENAI.key_env)


def test_the_provider_list_says_where_each_key_is_and_never_what_it_is(
    app_home, monkeypatch
):
    monkeypatch.setenv("OPENROUTER_API_KEY", SHELL_KEY)
    save_key(app_home, OPENAI, KEY)
    listed = provider_list(app_home)
    assert {each["name"]: each["key"] for each in listed} == {
        "OpenAI": "set",
        "OpenRouter": "shell",
        "Anthropic": "none",
        "Google Gemini": "none",
    }
    assert KEY not in json.dumps(listed) and SHELL_KEY not in json.dumps(listed)


def test_anthropics_key_is_kept_apart_from_the_one_claude_code_bills():
    anthropic = next(each for each in VENDORS if each.name == "Anthropic")
    assert anthropic.key_env == "DEEP_REASONING_ANTHROPIC_KEY"
    assert "ANTHROPIC_API_KEY" not in {each.key_env for each in VENDORS}


@pytest.mark.parametrize("key", ["sk two words", "sk-one\nOTHER=line", "", "  "])
def test_a_key_that_is_not_one_plain_line_is_refused_and_nothing_is_written(
    app_home, key
):
    with pytest.raises(SettingsError, match="paste the OpenAI key as one line"):
        save_key(app_home, OPENAI, key)
    assert not (app_home / ENV_FILE).exists()


def test_a_custom_server_is_added_changed_and_removed_with_its_key(app_home):
    add_server(app_home, " LM Studio ", f"{LOCAL_URL} ", "sk-local")
    server = find_provider(app_home, "LM Studio")
    assert (server.base_url, server.key_env, server.custom) == (
        LOCAL_URL,
        "DEEP_REASONING_LM_STUDIO_KEY",
        True,
    )
    assert saved_keys(app_home) == {server.key_env: "sk-local"}
    update_server(app_home, server, "http://127.0.0.1:9000/v1", None)
    assert find_provider(app_home, "LM Studio").base_url == "http://127.0.0.1:9000/v1"
    assert saved_keys(app_home) == {server.key_env: "sk-local"}
    update_server(app_home, server, "http://127.0.0.1:9000/v1", "sk-newer")
    assert saved_keys(app_home) == {server.key_env: "sk-newer"}
    remove_server(app_home, server)
    assert find_provider(app_home, "LM Studio") is None
    assert saved_keys(app_home) == {}


def test_a_custom_server_with_no_key_runs_on_a_placeholder(app_home):
    add_server(app_home, "vllm", LOCAL_URL, None)
    assert run_key(app_home, find_provider(app_home, "vllm")) == NO_KEY
    assert not (app_home / ENV_FILE).exists()


def test_a_vendor_with_no_key_cannot_run(app_home):
    with pytest.raises(SettingsError, match="OpenAI has no key: add one in settings"):
        run_key(app_home, OPENAI)


@pytest.mark.parametrize(
    ("name", "problem"),
    [
        ("", "Name the server with letters"),
        ("vllm/../x", "Name the server with letters"),
        ("x" * 41, "Name the server with letters"),
        ("openai", "There is a provider named OpenAI already"),
        # its key would be kept under Anthropic's variable
        ("anthropic.", "There is a provider named Anthropic already"),
        ("lm-studio", "There is a provider named lm studio already"),
    ],
)
def test_a_server_name_that_is_bad_or_taken_is_refused(app_home, name, problem):
    add_server(app_home, "lm studio", LOCAL_URL, None)
    with pytest.raises(SettingsError, match=problem):
        add_server(app_home, name, LOCAL_URL, None)
    assert [each.name for each in settings_module.servers(app_home)] == ["lm studio"]


@pytest.mark.parametrize(
    "url",
    [
        "localhost:8000/v1",
        "ftp://example.com/v1",
        "http:///v1",
        "http://example.com/v1?x=1",
        "http://example.com/v1#top",
        "http://exa mple.com/v1",
        "http://[::1/v1",
    ],
)
def test_a_base_url_that_is_not_a_plain_web_address_is_refused(app_home, url):
    with pytest.raises(SettingsError, match="should be an http:// or https:// address"):
        add_server(app_home, "vllm", url, None)
    assert not (app_home / SETTINGS_FILE).exists()


def test_a_base_url_carrying_a_password_is_refused(app_home):
    with pytest.raises(SettingsError, match="Put the key in the key field"):
        add_server(app_home, "vllm", "http://me:sk-secret@example.com/v1", None)
    assert not (app_home / SETTINGS_FILE).exists()


def test_server_key_variables_are_derived_from_their_names():
    assert server_key_env("vllm") == "DEEP_REASONING_VLLM_KEY"
    assert server_key_env("LM Studio 2.0") == "DEEP_REASONING_LM_STUDIO_2_0_KEY"


def test_settings_are_replaced_whole_so_a_failed_write_keeps_the_old_file(
    app_home, monkeypatch
):
    add_server(app_home, "vllm", LOCAL_URL, None)
    before = (app_home / SETTINGS_FILE).read_text()

    def disk_full(*args, **kwargs):
        raise OSError("No space left on device")

    monkeypatch.setattr(json, "dump", disk_full)
    with pytest.raises(OSError, match="No space left"):
        add_server(app_home, "sglang", LOCAL_URL, None)
    assert (app_home / SETTINGS_FILE).read_text() == before
    assert sorted(path.name for path in app_home.iterdir()) == [SETTINGS_FILE]


@pytest.mark.parametrize("text", ["[1, 2]", "{not json"])
def test_settings_this_app_did_not_write_are_refused_plainly(app_home, text):
    app_home.mkdir(parents=True)
    (app_home / SETTINGS_FILE).write_text(text)
    with pytest.raises(SettingsError, match="fix it or delete it"):
        settings_module.servers(app_home)


def test_new_chats_start_on_gpt_6_luna_when_openai_has_a_key_and_nothing_was_picked(
    app_home, monkeypatch
):
    assert starting_model(app_home) is None
    monkeypatch.setenv(OPENAI.key_env, SHELL_KEY)
    assert starting_model(app_home) == {"provider": "OpenAI", "name": "gpt-6-luna"}


def test_new_chats_start_on_the_model_picked_last_while_its_provider_can_answer(
    app_home, monkeypatch
):
    monkeypatch.setenv(OPENAI.key_env, SHELL_KEY)
    add_server(app_home, "vllm", LOCAL_URL, None)
    remember_pick(app_home, "vllm", "qwen3")
    assert starting_model(app_home) == {"provider": "vllm", "name": "qwen3"}
    remove_server(app_home, find_provider(app_home, "vllm"))
    assert starting_model(app_home) == {"provider": "OpenAI", "name": "gpt-6-luna"}


def test_the_default_folder_is_kept_beside_the_other_settings(app_home, tmp_path):
    assert default_folder(app_home) is None
    add_server(app_home, "vllm", LOCAL_URL, None)
    save_default_folder(app_home, str(tmp_path / "code"))
    assert default_folder(app_home) == str(tmp_path / "code")
    save_default_folder(app_home, None)
    assert default_folder(app_home) is None
    assert find_provider(app_home, "vllm") is not None
