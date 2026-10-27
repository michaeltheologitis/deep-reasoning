"""Chats: each one's id, title, when it was made, and what its next message runs on and in,
in the app file beside the Library, so a copy of the file carries them.

A chat's turns are its runs, under runs/ in the app's home; the file holds none of their events.
"""

import re
import sqlite3
import time
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

import structlog
from coolname import generate_slug

from deep_reasoning.library import open_library

log = structlog.get_logger()

# A chat id: plain characters only, like the ids the app makes.
CHAT_ID = r"^[A-Za-z0-9_-]{1,100}$"
CHOICES = ("namespace", "provider", "model", "folder")
COLUMNS = "id, title, created, namespace, provider, model, folder"
# Adds no row when the id is taken.
ADD_CHAT = (
    "INSERT OR IGNORE INTO chats (id, title, created, folder)"
    " VALUES (:id, :title, :created, :folder)"
)
NEW_TITLE = "New chat"
# Three words, like "tunneling-easygoing-mosquito": over 300 million ids.
ID_WORDS = 3

Chat = dict[str, Any]


@contextmanager
def connect(path: Path) -> Iterator[sqlite3.Connection]:
    """The app file at *path*, laid out if new. Autocommit: every write here is one
    statement, which SQLite runs as a transaction of its own."""
    with closing(open_library(path)) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def has_plain_id(chat: sqlite3.Row) -> bool:
    """Whether the chat's id is one the app could have made: the file may have come from
    someone else, and an id names the chat's scratch folder."""
    if isinstance(chat["id"], str) and re.fullmatch(CHAT_ID, chat["id"]):
        return True
    log.warning("chats.left_out", id=repr(chat["id"]))
    return False


def list_chats(path: Path) -> list[Chat]:
    """Every chat with a plain id, newest first."""
    with connect(path) as connection:
        rows = connection.execute(
            f"SELECT {COLUMNS} FROM chats ORDER BY created DESC, rowid DESC"
        )
        return [dict(row) for row in rows if has_plain_id(row)]


def find_chat(path: Path, chat: str) -> Chat | None:
    with connect(path) as connection:
        row = connection.execute(
            f"SELECT {COLUMNS} FROM chats WHERE id = ?", (chat,)
        ).fetchone()
    return None if row is None else dict(row)


def create_chat(path: Path, folder: str | None = None) -> Chat:
    """A new chat titled "New chat", under a readable id no other chat has, working in
    *folder*, or in its scratch folder when None."""
    chat = {
        "id": generate_slug(ID_WORDS),
        "title": NEW_TITLE,
        "created": time.time(),
        "folder": folder,
    }
    with connect(path) as connection:
        while not connection.execute(ADD_CHAT, chat).rowcount:
            chat["id"] = generate_slug(ID_WORDS)
    return dict.fromkeys(CHOICES) | chat


def rename_chat(path: Path, chat: str, title: str) -> None:
    with connect(path) as connection:
        connection.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat))


def choose(
    path: Path,
    chat: str,
    namespace: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    """Set what the chat's next message runs on; a choice left None stays as it was."""
    with connect(path) as connection:
        connection.execute(
            "UPDATE chats SET namespace = coalesce(?, namespace),"
            " provider = coalesce(?, provider), model = coalesce(?, model) WHERE id = ?",
            (namespace, provider, model, chat),
        )


def choose_folder(path: Path, chat: str, folder: str | None) -> None:
    """Set the folder the chat's next message works in; None for its scratch folder."""
    with connect(path) as connection:
        connection.execute("UPDATE chats SET folder = ? WHERE id = ?", (folder, chat))


def title_new_chat(path: Path, chat: str, message: str) -> None:
    """Title a chat still called "New chat" after *message*'s first line that isn't
    blank."""
    title = message.strip().partition("\n")[0].strip()
    if not title:
        return
    with connect(path) as connection:
        connection.execute(
            "UPDATE chats SET title = ? WHERE id = ? AND title = ?",
            (title, chat, NEW_TITLE),
        )


def delete_chat(path: Path, chat: str) -> None:
    with connect(path) as connection:
        connection.execute("DELETE FROM chats WHERE id = ?", (chat,))
