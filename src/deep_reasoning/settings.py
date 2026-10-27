"""Settings: the providers a chat's model runs on, their keys, the custom servers, and the
folder new chats work in.

Keys live in .env in the app's home, readable only by you: never in the app file, a chat,
a run's folder, an event, a log or a response. A key saved there wins over the same
variable in the shell. The custom servers, the model picked last and the default folder,
none of it secret, live in the app file's app_settings table, so a copy of the file
carries them.
"""

import asyncio
import json
import os
import re
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values, set_key, unset_key

from deep_reasoning.library import open_library

ENV_FILE = ".env"
UPSERT_APP_SETTING = (
    "INSERT INTO app_settings VALUES (?, ?)"
    " ON CONFLICT (key) DO UPDATE SET json = excluded.json"
)
OWNER_ONLY = 0o600
# One line of printable ASCII, no spaces: every key and base URL is, and nothing else
# can then break a line of .env.
PLAIN_TEXT = re.compile(r"[!-~]{1,4096}")
SERVER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}")
EXAMPLE_NAME = "vllm"
EXAMPLE_URL = "http://localhost:8000/v1"
WEB_SCHEMES = ("http", "https")
# A server without a key still needs one for the OpenAI client: the placeholder local
# servers document.
NO_KEY = "EMPTY"
LIST_TIMEOUT_S = 10.0
SET, SHELL, NONE = "set", "shell", "none"


class SettingsError(ValueError):
    """Something settings refused, in words for the person who asked."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    key_env: str
    custom: bool = False
    # what a new chat starts on when no chat has picked a model yet
    first_model: str | None = None
    # the models the menu shows before anything is typed, strongest first
    featured: tuple[str, ...] = ()


# Each vendor's current tiers, strongest first, from its own models page on 2026-10-27:
# refresh them when a vendor ships a new tier. OpenRouter serves the same under its own ids.
OPENAI_MODELS = ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna")
ANTHROPIC_MODELS = (
    "claude-fable-5-1",
    "claude-opus-5-5",
    "claude-sonnet-5-5",
    "claude-haiku-5-5",
)
GEMINI_MODELS = ("gemini-4-argon", "gemini-3.8-flash", "gemini-3.5-flash-lite")
OPENROUTER_MODELS = (
    "openai/gpt-6-astra",
    "openai/gpt-6.1-sol",
    "openai/gpt-6-luna",
    "anthropic/claude-fable-5.1",
    "anthropic/claude-opus-5.5",
    "anthropic/claude-sonnet-5.5",
    "anthropic/claude-haiku-5.5",
    "google/gemini-4-argon",
    "google/gemini-3.8-flash",
    "google/gemini-3.5-flash-lite",
)

# The app knows these vendors' addresses, each from the vendor's own docs: they take only a key.
VENDORS = (
    Provider(
        "OpenAI",
        "https://api.openai.com/v1",
        "OPENAI_API_KEY",
        first_model="gpt-6-luna",
        featured=OPENAI_MODELS,
    ),
    Provider(
        "OpenRouter",
        "https://openrouter.ai/api/v1",
        "OPENROUTER_API_KEY",
        featured=OPENROUTER_MODELS,
    ),
    # never ANTHROPIC_API_KEY: with it set, Claude Code bills that key instead of the subscription
    Provider(
        "Anthropic",
        "https://api.anthropic.com/v1/",
        "DEEP_REASONING_ANTHROPIC_KEY",
        featured=ANTHROPIC_MODELS,
    ),
    Provider(
        "Google Gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "GEMINI_API_KEY",
        featured=GEMINI_MODELS,
    ),
)


def saved_keys(home: Path) -> dict[str, str]:
    """The keys in the app's .env, by variable name."""
    path = home / ENV_FILE
    if not path.is_file():
        return {}
    values = dotenv_values(path, interpolate=False)
    return {name: value for name, value in values.items() if value}


def key_status(provider: Provider, saved: dict[str, str]) -> str:
    if saved.get(provider.key_env):
        return SET
    if os.environ.get(provider.key_env):
        return SHELL
    return NONE


def key_of(provider: Provider, saved: dict[str, str]) -> str | None:
    """The provider's key: the one saved in settings, else the shell's."""
    key = saved.get(provider.key_env) or os.environ.get(provider.key_env) or ""
    # A shell or hand-edited key may end in a stray newline or carriage return.
    return key.strip() or None


def checked_key(key: str, provider: Provider) -> str:
    key = key.strip()
    if not PLAIN_TEXT.fullmatch(key):
        raise SettingsError(
            f"That doesn't look like a key: paste the {provider.name} key as one line, "
            "without spaces."
        )
    return key


def optional_key(key: str | None, provider: Provider) -> str | None:
    """A key given with a custom server, checked; None when the field was left blank."""
    return checked_key(key, provider) if key and key.strip() else None


def write_key(home: Path, name: str, key: str) -> None:
    """Set *name* in .env, leaving its other lines as they are; the file is the user's alone."""
    path = home / ENV_FILE
    home.mkdir(parents=True, exist_ok=True)
    if path.is_file() and not path.is_symlink():
        # The rewrite keeps the file's mode, so it is narrowed before the key goes in.
        path.chmod(OWNER_ONLY)
    # A new file, or one replacing a symlink, is made from a temporary one, which
    # starts readable by its owner only.
    set_key(path, name, key)


def drop_key(home: Path, name: str) -> None:
    path = home / ENV_FILE
    if path.is_file() and name in dotenv_values(path, interpolate=False):
        unset_key(path, name)


def save_key(home: Path, provider: Provider, key: str) -> None:
    write_key(home, provider.key_env, checked_key(key, provider))


def read_settings(library: Path) -> dict[str, Any]:
    """The app's settings in the file at *library*, which may have come from elsewhere."""
    with closing(open_library(library)) as connection:
        rows = connection.execute("SELECT key, json FROM app_settings").fetchall()
    try:
        return {key: json.loads(text) for key, text in rows}
    except ValueError as error:
        raise SettingsError(
            f"{library} holds settings this app didn't write, so it can't read them."
        ) from error


def write_setting(library: Path, key: str, value: Any) -> None:
    """Set one of the app's settings: one statement, so it lands whole or not at all."""
    with closing(open_library(library)) as connection:
        connection.execute(UPSERT_APP_SETTING, (key, json.dumps(value)))


def server_key_env(name: str) -> str:
    """The variable a custom server's key is kept under: DEEP_REASONING_<NAME>_KEY."""
    return f"DEEP_REASONING_{re.sub(r'[^A-Z0-9]+', '_', name.upper()).strip('_')}_KEY"


def server_list(library: Path) -> list[dict[str, str]]:
    return read_settings(library).get("servers", [])


def servers(library: Path) -> list[Provider]:
    return [
        Provider(each["name"], each["base_url"], server_key_env(each["name"]), True)
        for each in server_list(library)
    ]


def providers(library: Path) -> list[Provider]:
    return [*VENDORS, *servers(library)]


def find_provider(library: Path, name: str) -> Provider | None:
    return next((each for each in providers(library) if each.name == name), None)


def usable(library: Path, saved: dict[str, str]) -> list[Provider]:
    """The providers a chat can run on: vendors with a key, and custom servers, which may need none."""
    return [
        each
        for each in providers(library)
        if each.custom or key_status(each, saved) != NONE
    ]


def provider_list(home: Path, library: Path) -> list[dict[str, Any]]:
    """Each provider as the page shows it: never its key, only whether one is saved here,
    comes from the shell, or is missing."""
    saved = saved_keys(home)
    return [
        {
            "name": each.name,
            "base_url": each.base_url,
            "key_env": each.key_env,
            "custom": each.custom,
            "key": key_status(each, saved),
        }
        for each in providers(library)
    ]


def checked_url(base_url: str) -> str:
    base_url = base_url.strip()
    problem = (
        f"The base URL should be an http:// or https:// address with no ?query or "
        f"#fragment, like {EXAMPLE_URL}."
    )
    try:
        parts = urlsplit(base_url)
        host = parts.hostname
    except ValueError as error:
        raise SettingsError(problem) from error
    if (
        not PLAIN_TEXT.fullmatch(base_url)
        or parts.scheme not in WEB_SCHEMES
        or not host
    ):
        raise SettingsError(problem)
    if parts.query or parts.fragment or base_url.endswith(("?", "#")):
        raise SettingsError(problem)
    if parts.username or parts.password:
        raise SettingsError("Put the key in the key field, not in the base URL.")
    return base_url


def checked_name(library: Path, name: str) -> str:
    name = name.strip()
    if not SERVER_NAME.fullmatch(name):
        raise SettingsError(
            "Name the server with letters, digits, spaces, dots, dashes or underscores, "
            f"up to 40, like {EXAMPLE_NAME}."
        )
    key_env = server_key_env(name)
    for other in providers(library):
        if other.name.lower() == name.lower() or other.key_env == key_env:
            raise SettingsError(f"There is a provider named {other.name} already.")
    return name


def add_server(
    home: Path, library: Path, name: str, base_url: str, key: str | None
) -> None:
    """Add a custom server to the app file, and its key, if it has one, to .env in *home*."""
    name, base_url = checked_name(library, name), checked_url(base_url)
    server = Provider(name, base_url, server_key_env(name), True)
    key = optional_key(key, server)
    added = {"name": name, "base_url": base_url}
    write_setting(library, "servers", [*server_list(library), added])
    if key:
        write_key(home, server.key_env, key)


def update_server(
    home: Path, library: Path, server: Provider, base_url: str, key: str | None
) -> None:
    """Change a custom server's base URL, and its key when a new one is given."""
    base_url = checked_url(base_url)
    key = optional_key(key, server)
    changed = [
        each | {"base_url": base_url} if each["name"] == server.name else each
        for each in server_list(library)
    ]
    write_setting(library, "servers", changed)
    if key:
        write_key(home, server.key_env, key)


def remove_server(home: Path, library: Path, server: Provider) -> None:
    kept = [each for each in server_list(library) if each["name"] != server.name]
    write_setting(library, "servers", kept)
    drop_key(home, server.key_env)


def remember_pick(library: Path, provider: str, model: str) -> None:
    """The model picked last, in any chat: where new chats start."""
    write_setting(library, "last_model", {"provider": provider, "name": model})


def starting_model(home: Path, library: Path) -> dict[str, str] | None:
    """What a new chat runs on: the model picked last, while its provider can still answer;
    else the first model of the first vendor with a key that the app knows one for."""
    can_answer = usable(library, saved_keys(home))
    last = read_settings(library).get("last_model")
    if last and any(each.name == last["provider"] for each in can_answer):
        return last
    first = next((each for each in can_answer if each.first_model), None)
    if first is None:
        return None
    return {"provider": first.name, "name": first.first_model}


def default_folder(library: Path) -> str | None:
    """The folder new chats work in; None: each in its own scratch folder."""
    return read_settings(library).get("default_folder")


def save_default_folder(library: Path, folder: str | None) -> None:
    write_setting(library, "default_folder", folder)


def run_key(home: Path, provider: Provider) -> str:
    """The key a run on *provider* authenticates with, or why it can't run."""
    key = key_of(provider, saved_keys(home))
    if key:
        return key
    if provider.custom:
        return NO_KEY
    raise SettingsError(f"{provider.name} has no key: add one in settings.")


async def list_models(provider: Provider, key: str | None) -> dict[str, Any]:
    """The provider's models from its own GET {base_url}/models, or why there are none, and
    the ones the menu shows before anything is typed: a vendor's current tiers, even with
    no list, or a custom server's whole list."""
    url = f"{provider.base_url.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    listing = {"provider": provider.name, "models": [], "problem": None}
    try:
        async with httpx.AsyncClient(timeout=LIST_TIMEOUT_S) as client:
            response = await client.get(url, headers=headers)
        response.raise_for_status()
        listing["models"] = sorted({each["id"] for each in response.json()["data"]})
    except httpx.HTTPStatusError as error:
        status = f"{error.response.status_code} {error.response.reason_phrase}".strip()
        listing["problem"] = f"No list: {url} answered {status}."
    except (httpx.LocalProtocolError, UnicodeEncodeError):
        # Raised for a key no header can carry; httpx's words would repeat the key.
        listing["problem"] = (
            f"No list: the {provider.name} key can't be sent; is it one line of "
            "plain text?"
        )
    except httpx.HTTPError as error:
        listing["problem"] = (
            f"No list: {url} didn't answer ({error or type(error).__name__})."
        )
    except (ValueError, KeyError, TypeError):
        listing["problem"] = f"No list: {url} didn't answer with a list of models."
    listing["featured"] = list(provider.featured or listing["models"])
    return listing


async def model_lists(home: Path, library: Path) -> list[dict[str, Any]]:
    """Each provider a chat can run on, with its models, fetched with its key here, so no
    key reaches the page."""
    saved = saved_keys(home)
    lists = [list_models(each, key_of(each, saved)) for each in usable(library, saved)]
    return list(await asyncio.gather(*lists))
