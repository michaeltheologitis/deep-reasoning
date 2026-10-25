import re

import pytest

from deep_reasoning import chats as chats_module
from deep_reasoning.app import CHAT_ID
from deep_reasoning.chats import (
    NEW_TITLE,
    create_chat,
    delete_chat,
    find_chat,
    list_chats,
    rename_chat,
    title_new_chat,
)

MANY = 200


@pytest.fixture
def chats(tmp_path):
    return tmp_path / "home" / ".deep-reasoning" / "chats.sqlite"


def test_new_chats_are_titled_new_chat_and_listed_newest_first(chats):
    first, second = create_chat(chats), create_chat(chats)
    assert first["title"] == second["title"] == NEW_TITLE
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
