"""Chats: each one's id, title and when it was made, in chats.sqlite in the app's home.

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
SCHEMA = (
    "CREATE TABLE IF NOT EXISTS chats"
    " (id TEXT PRIMARY KEY, title TEXT NOT NULL, created REAL NOT NULL)"
)
# Adds no row when the id is taken.
ADD_CHAT = (
    "INSERT OR IGNORE INTO chats (id, title, created) VALUES (:id, :title, :created)"
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
        yield connection
    finally:
        connection.close()


def list_chats(path: Path) -> list[Chat]:
    """Every chat, newest first."""
    with connect(path) as connection:
        rows = connection.execute(
            "SELECT id, title, created FROM chats ORDER BY created DESC"
        )
        return [dict(row) for row in rows]


def find_chat(path: Path, chat: str) -> Chat | None:
    with connect(path) as connection:
        row = connection.execute(
            "SELECT id, title, created FROM chats WHERE id = ?", (chat,)
        ).fetchone()
    return None if row is None else dict(row)


def create_chat(path: Path) -> Chat:
    """A new chat titled "New chat", under a readable id no other chat has."""
    chat = {"id": generate_slug(ID_WORDS), "title": NEW_TITLE, "created": time.time()}
    with connect(path) as connection:
        while not connection.execute(ADD_CHAT, chat).rowcount:
            chat["id"] = generate_slug(ID_WORDS)
    return chat


def rename_chat(path: Path, chat: str, title: str) -> None:
    with connect(path) as connection:
        connection.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat))


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
