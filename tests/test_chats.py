import re
import time
from contextlib import closing

import pytest
from deep_reasoner.namespaces import ROOT

from deep_reasoning import chats as chats_module
from deep_reasoning.chats import (
    CHAT_ID,
    NEW_TITLE,
    choose,
    choose_folder,
    create_chat,
    delete_chat,
    find_chat,
    list_chats,
    rename_chat,
    title_new_chat,
)
from deep_reasoning.library import (
    LIBRARY_ONLY,
    SCHEMA_VERSION,
    default_namespace,
    open_library,
    schema_version,
    stored_config,
)

MANY = 200
NOW = 1_800_000_000.0
ADVISORS_NAMESPACES = {"root", "router", "course_advisor", "health_advisor"}


@pytest.fixture
def chats(library):
    """The app file, which holds the chats beside the Library."""
    return library


def as_made_by_version_1(library):
    """The file as version 1 made it: the Library alone."""
    with closing(open_library(library)) as connection:
        connection.execute("DROP TABLE chats")
        connection.execute("DROP TABLE app_settings")
        connection.execute(f"PRAGMA user_version = {LIBRARY_ONLY}")


def test_a_chat_made_first_in_a_new_file_leaves_a_whole_library_beside_it(chats):
    chat = create_chat(chats)
    assert list_chats(chats) == [chat]
    assert default_namespace(chats) == ROOT


def test_a_version_1_library_opens_with_its_library_kept_and_gains_chats(imported):
    with closing(open_library(imported)) as connection:
        before = stored_config(connection)
    as_made_by_version_1(imported)
    chat = create_chat(imported)
    with closing(open_library(imported)) as connection:
        after = stored_config(connection)
        version = schema_version(connection)
    assert after == before and set(after["namespaces"]) == ADVISORS_NAMESPACES
    assert list_chats(imported) == [chat]
    assert version == SCHEMA_VERSION


def test_new_chats_are_titled_new_chat_and_listed_newest_first(chats):
    first, second = create_chat(chats), create_chat(chats)
    assert first["title"] == second["title"] == NEW_TITLE
    assert list_chats(chats) == [second, first]


def test_chats_made_in_the_same_clock_tick_are_listed_newest_first(chats, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: NOW)
    first, second = create_chat(chats), create_chat(chats)
    assert list_chats(chats) == [second, first]


def test_ids_are_readable_url_safe_and_unique(chats):
    ids = [create_chat(chats)["id"] for _ in range(MANY)]
    assert len(set(ids)) == MANY
    assert all(re.fullmatch(CHAT_ID, chat) for chat in ids)
    assert all(re.fullmatch(r"[a-z]+(-[a-z]+)+", chat) for chat in ids)


def test_an_id_already_taken_is_drawn_again(chats, monkeypatch):
    drawn = iter(["quiet-blue-heron", "quiet-blue-heron", "brave-red-fox"])
    monkeypatch.setattr(chats_module, "generate_slug", lambda words: next(drawn))
    first, second = create_chat(chats), create_chat(chats)
    assert (first["id"], second["id"]) == ("quiet-blue-heron", "brave-red-fox")
    assert list_chats(chats) == [second, first]


def test_rename_changes_only_that_chats_title(chats):
    kept, renamed = create_chat(chats), create_chat(chats)
    rename_chat(chats, renamed["id"], "Trip to Rome")
    assert find_chat(chats, renamed["id"]) == renamed | {"title": "Trip to Rome"}
    assert find_chat(chats, kept["id"]) == kept


@pytest.mark.parametrize(
    ("message", "title"),
    [
        ("Plan a trip.\nTo Rome, in May.", "Plan a trip."),
        ("\n\n  Plan a trip.  \r\nTo Rome.", "Plan a trip."),
        (" \n\t\n", NEW_TITLE),
    ],
)
def test_a_new_chat_is_titled_after_its_first_messages_first_line(
    chats, message, title
):
    chat = create_chat(chats)
    title_new_chat(chats, chat["id"], message)
    assert find_chat(chats, chat["id"])["title"] == title


def test_a_renamed_chat_is_not_retitled(chats):
    chat = create_chat(chats)
    rename_chat(chats, chat["id"], "Trip to Rome")
    title_new_chat(chats, chat["id"], "Plan a trip.")
    assert find_chat(chats, chat["id"])["title"] == "Trip to Rome"


def test_a_deleted_chat_is_gone_and_the_others_stay(chats):
    gone, kept = create_chat(chats), create_chat(chats)
    delete_chat(chats, gone["id"])
    assert find_chat(chats, gone["id"]) is None
    assert list_chats(chats) == [kept]


def test_a_new_chat_has_picked_nothing_yet(chats):
    chat = create_chat(chats)
    picks = (chat["namespace"], chat["provider"], chat["model"], chat["folder"])
    assert picks == (None, None, None, None)
    assert find_chat(chats, chat["id"]) == chat


def test_a_new_chat_starts_in_the_folder_it_is_given(chats):
    chat = create_chat(chats, "/home/me/code/thesis")
    assert chat["folder"] == find_chat(chats, chat["id"])["folder"]
    assert chat["folder"] == "/home/me/code/thesis"


def test_a_folder_choice_changes_only_that_chat_and_can_go_back_to_scratch(chats):
    chat, other = create_chat(chats), create_chat(chats)
    choose_folder(chats, chat["id"], "/home/me/code/thesis")
    choose(chats, chat["id"], namespace="router")
    chosen = find_chat(chats, chat["id"])["folder"]
    choose_folder(chats, chat["id"], None)
    assert chosen == "/home/me/code/thesis"
    assert find_chat(chats, chat["id"])["folder"] is None
    assert find_chat(chats, other["id"]) == other


def test_a_choice_changes_only_what_it_names_and_only_that_chat(chats):
    chat, other = create_chat(chats), create_chat(chats)
    choose(chats, chat["id"], "router", "OpenAI", "gpt-6-luna")
    choose(chats, chat["id"], namespace="course_advisor")
    choose(chats, chat["id"], provider="vllm", model="qwen3")
    found = find_chat(chats, chat["id"])
    assert (found["namespace"], found["provider"], found["model"]) == (
        "course_advisor",
        "vllm",
        "qwen3",
    )
    assert find_chat(chats, other["id"]) == other
