"""Chats: each one's id, title, when it was made, and what its next message runs on and in,
in chats.sqlite in the app's home.

A chat's turns are its runs, under runs/ beside it; this file holds none of their events.
"""

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from coolname import generate_slug

CHATS_FILE = "chats.sqlite"
# A chat id: plain characters only, like the ids the app makes.
CHAT_ID = r"^[A-Za-z0-9_-]{1,100}$"
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS chats"
    " (id TEXT PRIMARY KEY, title TEXT NOT NULL, created REAL NOT NULL)"
)
# Null until picked or run, and a null folder is the scratch folder. A file made before
# they were added gets them when next opened.
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
    """The chats file at *path*, made if new. Autocommit: every write here is one
    statement, which SQLite runs as a transaction of its own."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(SCHEMA)
        add_choices(connection)
        yield connection
    finally:
        connection.close()


def add_choices(connection: sqlite3.Connection) -> None:
    present = {row["name"] for row in connection.execute("PRAGMA table_info(chats)")}
    for column in [each for each in CHOICES if each not in present]:
        connection.execute(f"ALTER TABLE chats ADD COLUMN {column} TEXT")


def list_chats(path: Path) -> list[Chat]:
    """Every chat, newest first."""
    with connect(path) as connection:
        rows = connection.execute(
            f"SELECT {COLUMNS} FROM chats ORDER BY created DESC, rowid DESC"
        )
        return [dict(row) for row in rows]


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
