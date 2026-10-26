"""Working folders: where each chat's Python runs and reads and writes files.

A chat works in the folder its user chose, or else in its scratch folder, work/<chat>/ in
the app's home, made on its first run and deleted with the chat. A folder the user chose
is never deleted. Paths reach the page with your home folder written as ~.
"""

import os
import re
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import structlog

from deep_reasoning.chats import CHAT_ID

log = structlog.get_logger()

WORK = "work"
HOME = "~"
GONE = "That folder no longer exists — pick another."


class FolderError(ValueError):
    """A folder the app can't use, in words for the person who asked."""


def short_path(path: Path) -> str:
    """*path* with your home folder written as ~."""
    home = Path.home()
    if not path.is_relative_to(home):
        return str(path)
    rest = path.relative_to(home)
    return HOME if rest == Path() else f"{HOME}/{rest}"


def typed_path(typed: str) -> Path:
    """A typed path made absolute: ~ expanded, and a relative one taken from your home
    folder, where the folder browser starts."""
    return Path(os.path.normpath(Path.home() / os.path.expanduser(typed.strip())))


def existing_folder(typed: str) -> Path:
    """The folder at *typed*, or why there is none. os.path's checks answer False for any
    path the system can't take (too long, a NUL in it) instead of raising."""
    folder = typed_path(typed)
    if os.path.isdir(folder):
        return folder
    if os.path.exists(folder):
        raise FolderError(f"{short_path(folder)} is a file, not a folder.")
    raise FolderError(f"There is no folder {short_path(folder)}.")


def chosen_folder(typed: str | None) -> Path | None:
    """The folder a chat or the settings chose; None, for a scratch folder, when blank."""
    if typed is None or not typed.strip():
        return None
    return existing_folder(typed)


def list_folders(typed: str) -> dict[str, Any]:
    """The folder at *typed* and its subfolders, hidden ones last; its parent for "..",
    None at the root."""
    folder = existing_folder(typed)
    try:
        with os.scandir(folder) as entries:
            names = [entry.name for entry in entries if entry.is_dir()]
    except OSError as error:
        raise FolderError(
            f"Can't open {short_path(folder)}: {error.strerror or error}."
        ) from error
    names.sort(key=lambda name: (name.startswith("."), name.lower()))
    parent = None if folder.parent == folder else short_path(folder.parent)
    return {
        "path": short_path(folder),
        "parent": parent,
        "folders": [
            {"name": name, "path": short_path(folder / name)} for name in names
        ],
    }


def scratch_folder(home: Path, chat: str) -> Path:
    """work/<chat> in the app's home. Only a plain id names one, so no id reaches outside."""
    if not re.fullmatch(CHAT_ID, chat):
        raise ValueError(f"{chat!r} is not a chat id")
    return home / WORK / chat


def working_folder(home: Path, chat: dict[str, Any]) -> Path:
    """Where the chat's next run works: the folder it chose, which must still be there, or
    its scratch folder, made if new."""
    if chat["folder"] is not None:
        folder = Path(chat["folder"])
        if not os.path.isdir(folder):
            raise FolderError(GONE)
        return folder
    scratch = scratch_folder(home, chat["id"])
    scratch.mkdir(parents=True, exist_ok=True)
    return scratch


def remove_scratch(home: Path, chat: str, chosen: Iterable[str]) -> None:
    """Delete the chat's scratch folder and nothing else: never a folder in *chosen*, the
    folders chats chose, nor one holding such a folder; never through a symlink."""
    scratch = scratch_folder(home, chat)
    # realpath, as Path.resolve raises on a symlink loop
    real = Path(os.path.realpath(scratch))
    if any(Path(os.path.realpath(each)).is_relative_to(real) for each in chosen):
        log.warning("folders.scratch_kept_as_chosen", chat=chat, folder=str(scratch))
        return
    try:
        shutil.rmtree(scratch)
    except FileNotFoundError:
        return
    except OSError:
        # The chat is gone already: a folder left behind is logged, not raised.
        log.exception("folders.scratch_not_removed", chat=chat, folder=str(scratch))
