import json
import socket
import sqlite3
import stat
import threading
from contextlib import closing

import httpx
import pytest
from fake_model import (
    SERVER_KEY,
    SERVER_NAME,
    FakeOpenAI,
    repl,
    scripted,
    task_and_turn,
)
from fastapi.testclient import TestClient

from deep_reasoning.app import WEB, create_app
from deep_reasoning.chats import CHATS_FILE, create_chat
from deep_reasoning.library import (
    UPSERT_SETTING,
    dump,
    import_config,
    open_library,
    writing,
)
from deep_reasoning.runs import append_event
from deep_reasoning.settings import ENV_FILE, add_server, server_key_env

pytestmark = pytest.mark.usefixtures("no_vendor_keys")

LOCAL = "http://127.0.0.1"
SAVED_KEY = "sk-saved-in-settings"
SHELL_KEY = "sk-from-the-shell"
VLLM = "http://127.0.0.1:8001/v1"
VALID = """name: next course
messages:
- role: user
  content: What comes after CS201?
- role: assistant
  content: <repl>FinalAnswer("CS310")</repl>
"""


HELD_S = 30
PLAN = {
    "Count to two.": [repl("print(1)"), repl("FinalAnswer(2)")],
    "What did I ask?": [repl("FinalAnswer('to count')")],
}


@pytest.fixture
def client(imported, home):
    return TestClient(create_app(imported, home), base_url=LOCAL)


@pytest.fixture
def connect(home):
    """An HTTP client of the app over a Library: call it with the Library."""

    def to(library):
        transport = httpx.ASGITransport(app=create_app(library, home))
        return httpx.AsyncClient(transport=transport, base_url=LOCAL)

    return to


def server_sent(text):
    """(id, data) of each event in an event stream; keep-alive comments skipped."""
    events = []
    for block in text.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        if "data" in fields:
            events.append((int(fields["id"]), json.loads(fields["data"])))
    return events


async def new_chat(api):
    """A new chat's id."""
    response = await api.post("/api/chats")
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def send(api, chat, prompt):
    """Start a run of *prompt* in *chat*; its id."""
    response = await api.post(f"/api/chats/{chat}/runs", json={"prompt": prompt})
    assert response.status_code == 201, response.text
    return response.json()["run"]


async def run_events(api, run):
    """Every event of the run, once it has ended."""
    response = await api.get(f"/api/runs/{run}/events")
    return [event for _, event in server_sent(response.text)]


def namespaces(client):
    return {
        each["name"]: each for each in client.get("/api/library").json()["namespaces"]
    }


def field(namespace, label):
    return next(each["items"] for each in namespace["fields"] if each["label"] == label)


def test_root_serves_the_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Deep Reasoning</title>" in response.text


@pytest.mark.parametrize(
    "path", ["app.js", "fold.js", "style.css", "library.js", "settings.js"]
)
def test_static_assets_are_served(client, path):
    response = client.get(f"/{path}")
    assert response.status_code == 200
    assert response.content == (WEB / path).read_bytes()


def test_the_api_returns_the_library_as_the_engine_resolves_it(client):
    library = client.get("/api/library").json()
    by_name = {each["name"]: each for each in library["namespaces"]}
    settings = {row["label"]: row["items"][0] for row in library["run_settings"]}
    assert library["file"] == "library.sqlite"
    assert library["default_namespace"] == "router"
    assert list(by_name) == ["root", "course_advisor", "health_advisor", "router"]
    assert [each["name"] for each in by_name["router"]["decompositions"]] == [
        "route a course question",
        "route a wellbeing question",
        "decline anything else",
    ]
    assert field(by_name["root"], "Tools") == [
        {"value": "llm", "source": "granted here", "here": True}
    ]
    assert field(by_name["router"], "Tools")[0]["source"] == "inherited from root"
    assert "model" not in settings and "client" not in settings
    assert settings["max_depth"] == {"value": "8", "source": "the engine's default"}
    assert [(tool["name"], tool["granted_in"]) for tool in library["tools"]] == [
        ("llm", ["root"])
    ]
    [catalog] = library["variables"]
    assert (catalog["name"], catalog["where"], len(catalog["rows"])) == (
        "catalog",
        "course_advisor",
        6,
    )


def test_a_valid_decomposition_is_stored_and_listed_under_its_namespace(client):
    response = client.post(
        "/api/decompositions", json={"namespace": "course_advisor", "yaml": VALID}
    )
    assert response.status_code == 201
    assert response.json() == {
        "namespace": "course_advisor",
        "name": "next course",
        "yaml": VALID,
    }
    stored = namespaces(client)["course_advisor"]["decompositions"]
    assert [each["name"] for each in stored] == ["catalog lookup", "next course"]


@pytest.mark.parametrize(
    ("namespace", "text", "problem"),
    [
        ("router", "name: x\nmessages: [\n", "The YAML doesn't parse (line 3:"),
        (
            "router",
            VALID + "namespace: router\n",
            'Remove "namespace": only name and messages',
        ),
        (
            "router",
            VALID.replace("role: user", "role: robot"),
            'Message 1: role should be user, assistant or system, not "robot".',
        ),
        ("router", "name: x\n", "Add messages: a list of turns"),
        ("nowhere", VALID, 'The Library has no namespace "nowhere"'),
        (
            "course_advisor",
            VALID.replace("next course", "catalog lookup"),
            'course_advisor already has "catalog lookup"; rename it',
        ),
    ],
)
def test_an_invalid_decomposition_is_refused_with_a_plain_message(
    client, namespace, text, problem
):
    before = namespaces(client)
    response = client.post(
        "/api/decompositions", json={"namespace": namespace, "yaml": text}
    )
    assert response.status_code == 400
    assert problem in response.json()["detail"]
    assert namespaces(client) == before


def test_a_request_naming_another_host_is_refused(client):
    response = client.get("/api/library", headers={"Host": "rebound.example"})
    assert response.status_code == 400


@pytest.mark.anyio
async def test_a_message_runs_and_its_events_stream_with_ids(library_on, connect):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            run = await send(api, await new_chat(api), "Count to two.")
            response = await api.get(f"/api/runs/{run}/events")
            resumed = await api.get(
                f"/api/runs/{run}/events", headers={"Last-Event-ID": "3"}
            )
    assert response.headers["content-type"].startswith("text/event-stream")
    events = server_sent(response.text)
    assert [seq for seq, _ in events] == list(range(1, len(events) + 1))
    assert all(event["seq"] == seq for seq, event in events)
    assert events[0][1]["kind"] == "turn.start" and events[0][1]["namespace"] == "root"
    assert events[-1][1]["outcome"] == "answered" and events[-1][1]["answer"] == "2"
    assert server_sent(resumed.text) == events[3:]


@pytest.mark.anyio
async def test_a_stream_resumes_after_its_query_or_its_header_whichever_is_later(
    library_on, connect
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            run = await send(api, await new_chat(api), "Count to two.")
            url = f"/api/runs/{run}/events"
            events = server_sent((await api.get(url)).text)
            after = await api.get(url, params={"after": 3})
            reconnected = await api.get(
                url, params={"after": 3}, headers={"Last-Event-ID": "5"}
            )
    assert server_sent(after.text) == events[3:]
    assert server_sent(reconnected.text) == events[5:]


@pytest.mark.anyio
async def test_a_follow_up_runs_with_the_chat_so_far(library_on, connect):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            chat, another = await new_chat(api), await new_chat(api)
            await run_events(api, await send(api, chat, "Count to two."))
            await run_events(api, await send(api, chat, "What did I ask?"))
            await run_events(api, await send(api, another, "What did I ask?"))
    follow_up, fresh = fake.calls[-2].messages, fake.calls[-1].messages
    assert "Message 1: Count to two.\nAnswer 1: 2\n" in follow_up[-2]["content"]
    assert all("Count to two." not in message["content"] for message in fresh)


@pytest.mark.anyio
async def test_a_chat_keeps_the_namespace_it_started_in(imported, library_on, connect):
    plan = {"Hi.": [repl("FinalAnswer('hello')")]}
    with FakeOpenAI(scripted(plan)) as fake:
        async with connect(library_on(fake)) as api:
            chat, another = await new_chat(api), await new_chat(api)
            first = await run_events(api, await send(api, chat, "Hi."))
            with closing(open_library(imported)) as connection, writing(connection):
                default = ("entry_namespace", dump("course_advisor"))
                connection.execute(UPSERT_SETTING, default)
            again = await run_events(api, await send(api, chat, "Hi."))
            new = await run_events(api, await send(api, another, "Hi."))
    namespaces = [events[0]["namespace"] for events in (first, again, new)]
    assert namespaces == ["router", "router", "course_advisor"]
    assert [events[-1]["outcome"] for events in (first, again, new)] == ["answered"] * 3


@pytest.mark.anyio
async def test_a_run_gets_the_librarys_tools_in_a_folder_of_its_own(
    waitlist, library, library_on, connect, home
):
    with closing(open_library(library)) as connection:
        import_config(connection, waitlist)
    plan = {"Join.": [repl("FinalAnswer(waitlist.join('ada', 'CS101'))")]}
    with FakeOpenAI(scripted(plan)) as fake:
        async with connect(library_on(fake)) as api:
            run = await send(api, await new_chat(api), "Join.")
            events = await run_events(api, run)
    assert events[-1]["outcome"] == "answered", events[-1]
    assert events[-1]["answer"] == "enrolled"
    assert (home / "runs" / run / "tools" / "waitlist.py").is_file()


def held_on(prompt, plan):
    """A responder that follows *plan*, holding *prompt*'s first call until released;
    and the release."""
    release = threading.Event()
    follow = scripted(plan)

    def held(messages):
        if task_and_turn(messages) == (prompt, 0):
            release.wait(HELD_S)
        return follow(messages)

    return held, release


@pytest.mark.anyio
async def test_a_second_message_while_a_run_is_going_is_refused(library_on, connect):
    held, release = held_on("Count to two.", PLAN)
    with FakeOpenAI(held) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            run = await send(api, chat, "Count to two.")
            refused = await api.post(
                f"/api/chats/{chat}/runs", json={"prompt": "What did I ask?"}
            )
            stopped = await api.post(f"/api/runs/{run}/stop")
            events = await run_events(api, run)
            release.set()
            again = await api.post(f"/api/runs/{run}/stop")
    assert refused.status_code == 409
    assert refused.json() == {"detail": f"Chat {chat} has a run going."}
    assert stopped.status_code == 200
    assert events[-1]["outcome"] == "stopped"
    assert again.status_code == 409


@pytest.mark.parametrize("chat", ["a chat!", "x" * 101])
def test_a_bad_chat_id_is_refused(client, chat):
    assert client.get(f"/api/chats/{chat}").status_code == 422
    assert client.patch(f"/api/chats/{chat}", json={"title": "Hi"}).status_code == 422
    assert client.delete(f"/api/chats/{chat}").status_code == 422
    response = client.post(f"/api/chats/{chat}/runs", json={"prompt": "Hi."})
    assert response.status_code == 422


def test_an_empty_message_is_refused(client):
    chat = client.post("/api/chats").json()["id"]
    response = client.post(f"/api/chats/{chat}/runs", json={"prompt": ""})
    assert response.status_code == 422


def test_a_chat_that_is_not_there_is_refused(client):
    chat = "no-such-chat"
    assert client.get(f"/api/chats/{chat}").status_code == 404
    assert client.patch(f"/api/chats/{chat}", json={"title": "Hi"}).status_code == 404
    assert client.delete(f"/api/chats/{chat}").status_code == 404
    response = client.post(f"/api/chats/{chat}/runs", json={"prompt": "Hi."})
    assert response.status_code == 404
    assert response.json() == {"detail": "There is no chat no-such-chat."}


@pytest.mark.parametrize(
    ("run", "status"), [("20261025-120000-000000", 404), ("not-a-run", 422)]
)
def test_a_run_that_is_not_there_is_refused(client, run, status):
    assert client.get(f"/api/runs/{run}/events").status_code == status
    assert client.post(f"/api/runs/{run}/stop").status_code == status


def test_new_chats_are_listed_newest_first(client):
    first, second = client.post("/api/chats"), client.post("/api/chats")
    assert first.status_code == second.status_code == 201
    assert first.json()["title"] == "New chat" and first.json()["live"] is None
    assert first.json()["id"] != second.json()["id"]
    assert client.get("/api/chats").json() == [second.json(), first.json()]


def test_a_chat_is_renamed_with_its_title_trimmed(client):
    chat = client.post("/api/chats").json()
    response = client.patch(
        f"/api/chats/{chat['id']}", json={"title": "  Trip to Rome \n"}
    )
    assert response.status_code == 200
    assert response.json() == chat | {"title": "Trip to Rome"}
    assert client.get("/api/chats").json() == [response.json()]


@pytest.mark.parametrize("title", ["", " \n "])
def test_a_blank_title_is_refused(client, title):
    chat = client.post("/api/chats").json()
    response = client.patch(f"/api/chats/{chat['id']}", json={"title": title})
    assert response.status_code == 422
    assert client.get("/api/chats").json() == [chat]


async def title_of(api, chat):
    return (await api.get(f"/api/chats/{chat}")).json()["title"]


@pytest.mark.anyio
async def test_the_first_message_titles_a_new_chat_and_a_later_one_does_not(
    library_on, connect
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            await run_events(api, await send(api, chat, "Count to two.\nSlowly."))
            titled = await title_of(api, chat)
            await run_events(api, await send(api, chat, "What did I ask?"))
            later = await title_of(api, chat)
    assert titled == later == "Count to two."


@pytest.mark.anyio
async def test_a_renamed_chat_keeps_its_name_when_its_first_message_runs(
    library_on, connect
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            await api.patch(f"/api/chats/{chat}", json={"title": "Counting"})
            await run_events(api, await send(api, chat, "Count to two."))
            title = await title_of(api, chat)
    assert title == "Counting"


@pytest.mark.anyio
async def test_a_chat_reads_back_with_its_turns_in_order(library_on, connect):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            chat, another = await new_chat(api), await new_chat(api)
            first = await send(api, chat, "Count to two.")
            first_events = await run_events(api, first)
            await run_events(api, await send(api, another, "Count to two."))
            second = await send(api, chat, "What did I ask?")
            second_events = await run_events(api, second)
            response = await api.get(f"/api/chats/{chat}")
    read = response.json()
    assert (read["id"], read["title"], read["live"]) == (chat, "Count to two.", None)
    assert read["turns"] == [
        {"run": first, "events": first_events},
        {"run": second, "events": second_events},
    ]


@pytest.mark.anyio
async def test_a_run_that_is_going_shows_in_the_list_and_in_its_chat(
    library_on, connect
):
    held, release = held_on("Count to two.", PLAN)
    with FakeOpenAI(held) as fake:
        async with connect(library_on(fake)) as api:
            chat, idle = await new_chat(api), await new_chat(api)
            run = await send(api, chat, "Count to two.")
            listed = (await api.get("/api/chats")).json()
            read = (await api.get(f"/api/chats/{chat}")).json()
            release.set()
            await run_events(api, run)
            after = (await api.get("/api/chats")).json()
    assert {each["id"]: each["live"] for each in listed} == {chat: run, idle: None}
    assert read["live"] == run and [turn["run"] for turn in read["turns"]] == [run]
    assert read["turns"][0]["events"][0]["kind"] == "turn.start"
    assert {each["id"]: each["live"] for each in after} == {chat: None, idle: None}


@pytest.mark.anyio
async def test_deleting_a_chat_stops_its_run_and_removes_its_run_folders(
    library_on, home
):
    held, release = held_on("What did I ask?", PLAN)
    with FakeOpenAI(held) as fake:
        app = create_app(library_on(fake), home)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=LOCAL) as api:
            chat, kept = await new_chat(api), await new_chat(api)
            ended = await send(api, chat, "Count to two.")
            await run_events(api, ended)
            other = await send(api, kept, "Count to two.")
            await run_events(api, other)
            going = await send(api, chat, "What did I ask?")
            deleted = await api.delete(f"/api/chats/{chat}")
            release.set()
            listed = (await api.get("/api/chats")).json()
            read = await api.get(f"/api/chats/{chat}")
    assert deleted.status_code == 204
    assert app.state.runs.live(chat) is None
    assert [each["id"] for each in listed] == [kept]
    assert read.status_code == 404
    runs = home / "runs"
    assert not (runs / ended).exists() and not (runs / going).exists()
    assert (runs / other / "events.jsonl").is_file()


@pytest.mark.anyio
async def test_chats_survive_a_restart(library_on, connect):
    with FakeOpenAI(scripted(PLAN)) as fake:
        library = library_on(fake)
        async with connect(library) as api:
            chat = await new_chat(api)
            run = await send(api, chat, "Count to two.")
            events = await run_events(api, run)
            renamed = await api.patch(f"/api/chats/{chat}", json={"title": "Counting"})
        async with connect(library) as restarted:
            listed = (await restarted.get("/api/chats")).json()
            read = (await restarted.get(f"/api/chats/{chat}")).json()
    assert listed == [renamed.json()]
    assert read == renamed.json() | {"turns": [{"run": run, "events": events}]}


def by_name(rows, field="name"):
    return {each[field]: each for each in rows}


def closed_port():
    with socket.create_server(("127.0.0.1", 0)) as probe:
        return probe.getsockname()[1]


def test_a_saved_key_comes_back_as_a_status_never_as_itself(client, home):
    saved = client.put("/api/providers/OpenAI/key", json={"key": SAVED_KEY})
    listed = client.get("/api/providers")
    assert saved.status_code == listed.status_code == 200
    assert by_name(listed.json())["OpenAI"] == {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "custom": False,
        "key": "set",
    }
    assert SAVED_KEY not in saved.text and SAVED_KEY not in listed.text
    env = home / ENV_FILE
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert env.read_text() == f"OPENAI_API_KEY='{SAVED_KEY}'\n"


def test_removing_a_saved_key_leaves_the_shells_in_use(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", SHELL_KEY)
    shell = client.get("/api/providers")
    client.put("/api/providers/OpenAI/key", json={"key": SAVED_KEY})
    removed = client.delete("/api/providers/OpenAI/key")
    assert by_name(shell.json())["OpenAI"]["key"] == "shell"
    assert by_name(removed.json())["OpenAI"]["key"] == "shell"
    assert SHELL_KEY not in shell.text and SHELL_KEY not in removed.text


@pytest.mark.parametrize(
    ("body", "sent", "status"),
    [
        ({"key": "sk two words"}, "sk two words", 400),
        ({"key": ["sk-in-a-list"]}, "sk-in-a-list", 422),
        ({"key": 31415926535}, "31415926535", 422),
    ],
)
def test_a_malformed_key_is_refused_without_being_repeated(
    client, home, body, sent, status
):
    response = client.put("/api/providers/OpenAI/key", json=body)
    assert response.status_code == status
    assert sent not in response.text
    assert not (home / ENV_FILE).exists()


def test_a_provider_or_server_that_is_not_there_is_refused(client):
    assert (
        client.put("/api/providers/Nobody/key", json={"key": "sk-x"}).status_code == 404
    )
    assert client.delete("/api/providers/Nobody/key").status_code == 404
    # a vendor is not a custom server: its address is the app's
    assert client.put("/api/servers/OpenAI", json={"base_url": VLLM}).status_code == 404
    assert client.delete("/api/servers/OpenAI").status_code == 404


def test_a_custom_server_is_added_changed_and_removed_with_its_key(client, home):
    server = {"name": "vllm", "base_url": VLLM, "key": "sk-vllm"}
    added = client.post("/api/servers", json=server)
    again = client.post("/api/servers", json=server)
    changed = client.put(
        "/api/servers/vllm", json={"base_url": "http://127.0.0.1:9/v1"}
    )
    refused = client.put("/api/servers/vllm", json={"base_url": "ftp://127.0.0.1/v1"})
    assert added.status_code == 201
    assert by_name(added.json())["vllm"] == {
        "name": "vllm",
        "base_url": VLLM,
        "key_env": "DEEP_REASONING_VLLM_KEY",
        "custom": True,
        "key": "set",
    }
    assert "sk-vllm" not in added.text
    assert again.status_code == 400
    assert again.json()["detail"] == "There is a provider named vllm already."
    assert by_name(changed.json())["vllm"]["base_url"] == "http://127.0.0.1:9/v1"
    assert by_name(changed.json())["vllm"]["key"] == "set"
    assert refused.status_code == 400
    removed = client.delete("/api/servers/vllm")
    assert "vllm" not in by_name(removed.json())
    assert "DEEP_REASONING_VLLM_KEY" not in (home / ENV_FILE).read_text()


@pytest.mark.anyio
async def test_models_are_listed_through_the_app_with_each_providers_key(
    library_on, connect
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            response = await api.get("/api/models")
    assert response.json() == [
        {
            "provider": SERVER_NAME,
            "models": ["fake-large", "fake-small"],
            "problem": None,
        }
    ]
    assert fake.listed == [SERVER_KEY]
    assert SERVER_KEY not in response.text


def test_a_listing_that_fails_says_why_in_plain_words(client, home):
    gone = f"http://127.0.0.1:{closed_port()}/v1"
    with FakeOpenAI(scripted(PLAN), models=None) as fake:
        add_server(home, "unlisted", fake.base_url, None)
        add_server(home, "gone", gone, None)
        listings = by_name(client.get("/api/models").json(), "provider")
    assert listings["unlisted"] == {
        "provider": "unlisted",
        "models": [],
        "problem": f"No list: {fake.base_url}/models answered 404 Not Found.",
    }
    assert listings["gone"]["models"] == []
    assert listings["gone"]["problem"].startswith(
        f"No list: {gone}/models didn't answer ("
    )


@pytest.mark.parametrize("key", ["sk-in\nhalves", "sk-in\rhalves", "sk-ünïcode"])
def test_a_key_no_header_can_carry_is_never_repeated_in_a_listing(
    client, home, monkeypatch, key
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        add_server(home, "vllm", fake.base_url, None)
        monkeypatch.setenv(server_key_env("vllm"), key)
        response = client.get("/api/models")
    assert response.json() == [
        {
            "provider": "vllm",
            "models": [],
            "problem": "No list: the vllm key can't be sent; is it one line of "
            "plain text?",
        }
    ]
    assert "sk-" not in response.text


def test_a_shell_key_ending_in_a_carriage_return_lists_without_it(
    client, home, monkeypatch
):
    with FakeOpenAI(scripted(PLAN)) as fake:
        add_server(home, "vllm", fake.base_url, None)
        monkeypatch.setenv(server_key_env("vllm"), f"{SHELL_KEY}\r")
        listing = client.get("/api/models").json()[0]
    assert (listing["models"], fake.listed) == (
        ["fake-large", "fake-small"],
        [SHELL_KEY],
    )


def test_a_chat_from_before_namespaces_were_kept_stays_in_the_one_its_runs_used(
    imported, home
):
    chat = create_chat(home / CHATS_FILE)["id"]
    run = "20261025-120000-000000"
    (home / "runs" / run).mkdir(parents=True)
    start = {"kind": "turn.start", "run": run, "chat": chat, "prompt": "Hi."}
    end = {"kind": "turn.end", "outcome": "answered", "answer": "hello", "detail": None}
    append_event(home, run, {"seq": 1, "t": 1.0, "namespace": "course_advisor"} | start)
    append_event(home, run, {"seq": 2, "t": 2.0, "cost": None, "seconds": 1.0} | end)
    with TestClient(create_app(imported, home), base_url=LOCAL) as client:
        read = client.get(f"/api/chats/{chat}").json()
    assert read["namespace"] == "course_advisor"


@pytest.mark.anyio
async def test_a_run_uses_the_chats_model_and_its_providers_key_kept_out_of_the_run(
    library_on, connect, home, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-not-for-runs")
    look = repl("import os", "print('ANTHROPIC_API_KEY' in os.environ)")
    plan = {"Look.": [look, repl("FinalAnswer('looked')")]}
    with FakeOpenAI(scripted(plan)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            model = {"provider": SERVER_NAME, "name": "fake-large"}
            picked = await api.patch(f"/api/chats/{chat}", json={"model": model})
            run = await send(api, chat, "Look.")
            events = await run_events(api, run)
    assert picked.json()["model"] == model
    assert {(call.model, call.key) for call in fake.calls} == {
        ("fake-large", SERVER_KEY)
    }
    assert (events[0]["model"], events[0]["provider"]) == ("fake-large", SERVER_NAME)
    cells = [event for event in events if event["kind"] == "cell.end"]
    assert cells[0]["output"] == "False"
    assert events[-1]["outcome"] == "answered"
    for file in (home / "runs" / run).rglob("*"):
        assert not file.is_file() or SERVER_KEY.encode() not in file.read_bytes(), file


@pytest.mark.anyio
async def test_switching_namespace_mid_chat_runs_the_next_message_there_and_says_so(
    imported, library_on, connect
):
    plan = {"Hi.": [repl("FinalAnswer('hello')")]}
    with FakeOpenAI(scripted(plan)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            first = await run_events(api, await send(api, chat, "Hi."))
            switched = await api.patch(
                f"/api/chats/{chat}", json={"namespace": "course_advisor"}
            )
            again = await run_events(api, await send(api, chat, "Hi."))
            read = (await api.get(f"/api/chats/{chat}")).json()
    assert [first[0]["namespace"], again[0]["namespace"]] == [
        "router",
        "course_advisor",
    ]
    assert switched.json()["namespace"] == read["namespace"] == "course_advisor"
    texts = [message["content"] for message in fake.calls[-1].messages]
    assert any(
        "Message 1 (in namespace router): Hi.\nAnswer 1: hello" in text
        for text in texts
    )


def test_a_namespace_or_model_the_app_does_not_have_is_refused(client):
    chat = client.post("/api/chats").json()["id"]
    nowhere = client.patch(f"/api/chats/{chat}", json={"namespace": "nowhere"})
    model = {"provider": "Nobody", "name": "x"}
    nobody = client.patch(f"/api/chats/{chat}", json={"model": model})
    blank = {"provider": "OpenAI", "name": " "}
    unnamed = client.patch(f"/api/chats/{chat}", json={"model": blank})
    assert (nowhere.status_code, nobody.status_code, unnamed.status_code) == (
        400,
        400,
        422,
    )
    assert nowhere.json()["detail"].startswith('The Library has no namespace "nowhere"')
    assert nobody.json()["detail"] == "There is no provider Nobody."
    read = client.get(f"/api/chats/{chat}").json()
    assert (read["namespace"], read["model"]) == ("router", None)


def test_a_new_chat_starts_on_the_model_picked_last_in_any_chat(
    client, home, monkeypatch
):
    first = client.post("/api/chats").json()
    assert (first["namespace"], first["model"]) == ("router", None)
    monkeypatch.setenv("OPENAI_API_KEY", SHELL_KEY)
    luna = {"provider": "OpenAI", "name": "gpt-6-luna"}
    assert client.post("/api/chats").json()["model"] == luna
    add_server(home, "vllm", VLLM, None)
    qwen = {"provider": "vllm", "name": "qwen3"}
    client.patch(f"/api/chats/{first['id']}", json={"model": qwen})
    later = client.post("/api/chats").json()
    assert later["model"] == qwen
    gpt = {"provider": "OpenAI", "name": "gpt-5.5"}
    client.patch(f"/api/chats/{later['id']}", json={"model": gpt})
    models = {chat["id"]: chat["model"] for chat in client.get("/api/chats").json()}
    assert models[first["id"]] == qwen and models[later["id"]] == gpt


def test_a_message_is_refused_until_the_chat_has_a_model_that_can_run(client):
    chat = client.post("/api/chats").json()["id"]
    unpicked = client.post(f"/api/chats/{chat}/runs", json={"prompt": "Hi."})
    luna = {"provider": "OpenAI", "name": "gpt-6-luna"}
    client.patch(f"/api/chats/{chat}", json={"model": luna})
    keyless = client.post(f"/api/chats/{chat}/runs", json={"prompt": "Hi."})
    assert (unpicked.status_code, keyless.status_code) == (400, 400)
    assert (
        unpicked.json()["detail"]
        == "Pick a model for this chat, under the message box."
    )
    assert keyless.json()["detail"] == "OpenAI has no key: add one in settings."
    assert client.get(f"/api/chats/{chat}").json()["turns"] == []


def test_a_request_from_another_sites_page_is_refused(client):
    refused = client.post("/api/chats", headers={"Origin": "https://evil.example"})
    own = client.post("/api/chats", headers={"Origin": LOCAL})
    assert (refused.status_code, own.status_code) == (403, 201)
    assert len(client.get("/api/chats").json()) == 1


WRITE_THEN_READ = {
    "Write a note.": [
        repl("import pathlib", "pathlib.Path('note.txt').write_text('from message 1')"),
        repl("FinalAnswer('noted')"),
    ],
    "Read the note.": [
        repl("print(open('note.txt').read())"),
        repl("FinalAnswer('read')"),
    ],
}


def cell_outputs(events):
    return [event["output"] for event in events if event["kind"] == "cell.end"]


def folder_of(read):
    """The folder a chat's next message works in, as the page shows it."""
    return read["folder"] or read["scratch_folder"]


@pytest.mark.anyio
async def test_a_chat_without_a_folder_works_in_its_scratch_folder_across_messages(
    library_on, connect, home
):
    with FakeOpenAI(scripted(WRITE_THEN_READ)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            before = (home / "work" / chat).exists()
            first = await run_events(api, await send(api, chat, "Write a note."))
            second = await run_events(api, await send(api, chat, "Read the note."))
            read = (await api.get(f"/api/chats/{chat}")).json()
    scratch = home / "work" / chat
    assert not before
    assert (read["folder"], read["scratch_folder"]) == (None, f"~/work/{chat}")
    assert first[0]["folder"] == second[0]["folder"] == str(scratch)
    assert (scratch / "note.txt").read_text() == "from message 1"
    assert cell_outputs(second)[0] == "from message 1"
    assert second[-1]["outcome"] == "answered", second[-1]


@pytest.mark.anyio
async def test_a_folder_changed_mid_chat_applies_from_the_next_message(
    library_on, connect, home
):
    thesis, data = home / "code" / "thesis", home / "data"
    thesis.mkdir(parents=True)
    data.mkdir()
    with FakeOpenAI(scripted(WRITE_THEN_READ)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            picked = await api.patch(
                f"/api/chats/{chat}", json={"folder": "~/code/thesis/"}
            )
            first = await run_events(api, await send(api, chat, "Write a note."))
            moved = await api.patch(f"/api/chats/{chat}", json={"folder": str(data)})
            second = await run_events(api, await send(api, chat, "Read the note."))
            back = await api.patch(f"/api/chats/{chat}", json={"folder": None})
    assert picked.json()["folder"] == "~/code/thesis"
    assert moved.json()["folder"] == "~/data" and back.json()["folder"] is None
    assert (first[0]["folder"], second[0]["folder"]) == (str(thesis), str(data))
    assert (thesis / "note.txt").read_text() == "from message 1"
    assert "FileNotFoundError" in cell_outputs(second)[0]
    assert not (home / "work" / chat).exists()


@pytest.mark.anyio
async def test_a_run_in_a_folder_that_is_gone_is_refused_and_nothing_starts(
    library_on, connect, home
):
    thesis = home / "thesis"
    thesis.mkdir()
    with FakeOpenAI(scripted(WRITE_THEN_READ)) as fake:
        async with connect(library_on(fake)) as api:
            chat = await new_chat(api)
            await api.patch(f"/api/chats/{chat}", json={"folder": str(thesis)})
            thesis.rmdir()
            refused = await api.post(
                f"/api/chats/{chat}/runs", json={"prompt": "Write a note."}
            )
            read = (await api.get(f"/api/chats/{chat}")).json()
    assert refused.status_code == 400
    assert refused.json() == {"detail": "That folder no longer exists — pick another."}
    assert read["turns"] == [] and read["title"] == "New chat"
    assert fake.calls == [] and not (home / "runs").exists()


@pytest.mark.parametrize(
    ("folder", "problem"),
    [
        ("/no/such/folder", "There is no folder /no/such/folder."),
        ("~/notes.txt", "~/notes.txt is a file, not a folder."),
    ],
)
def test_a_folder_that_is_not_there_is_refused_and_the_chat_keeps_its_own(
    client, home, folder, problem
):
    (home / "notes.txt").write_text("not a folder")
    chat = client.post("/api/chats").json()
    refused = client.patch(f"/api/chats/{chat['id']}", json={"folder": folder})
    assert refused.status_code == 400
    assert refused.json() == {"detail": problem}
    assert client.get("/api/chats").json() == [chat]


def test_folders_are_listed_for_the_picker_and_a_missing_one_is_refused(client, home):
    (home / "code" / "thesis").mkdir(parents=True)
    (home / ".cache").mkdir()
    (home / "notes.txt").write_text("not a folder")
    listed = client.get("/api/folders")
    code = client.get("/api/folders", params={"path": "~/code"})
    missing = client.get("/api/folders", params={"path": "~/gone"})
    assert listed.json() == {
        "path": "~",
        "parent": str(home.parent),
        "folders": [
            {"name": "code", "path": "~/code"},
            {"name": ".cache", "path": "~/.cache"},
        ],
    }
    assert code.json()["folders"] == [{"name": "thesis", "path": "~/code/thesis"}]
    assert (missing.status_code, missing.json()) == (
        400,
        {"detail": "There is no folder ~/gone."},
    )


def test_new_chats_start_in_the_default_folder_and_older_chats_keep_theirs(
    client, home
):
    (home / "code").mkdir()
    before = client.post("/api/chats").json()
    unset = client.get("/api/default-folder").json()
    saved = client.put("/api/default-folder", json={"folder": "~/code"})
    refused = client.put("/api/default-folder", json={"folder": "~/gone"})
    after = client.post("/api/chats").json()
    cleared = client.put("/api/default-folder", json={"folder": ""})
    last = client.post("/api/chats").json()
    assert unset == {"folder": None} and saved.json() == {"folder": "~/code"}
    assert refused.status_code == 400
    assert json.loads((home / "settings.json").read_text())["default_folder"] is None
    assert cleared.json() == {"folder": None}
    assert [each["folder"] for each in (before, after, last)] == [None, "~/code", None]
    listed = {each["id"]: each["folder"] for each in client.get("/api/chats").json()}
    assert listed[before["id"]] is None and listed[after["id"]] == "~/code"


@pytest.mark.anyio
async def test_deleting_a_chat_removes_its_scratch_folder_and_never_a_chosen_one(
    library_on, connect, home
):
    chosen = home / "thesis"
    chosen.mkdir()
    (chosen / "keep.txt").write_text("mine")
    with FakeOpenAI(scripted(WRITE_THEN_READ)) as fake:
        async with connect(library_on(fake)) as api:
            scratch, kept = await new_chat(api), await new_chat(api)
            await api.patch(f"/api/chats/{kept}", json={"folder": str(chosen)})
            await run_events(api, await send(api, scratch, "Write a note."))
            await run_events(api, await send(api, kept, "Write a note."))
            written = (home / "work" / scratch / "note.txt").is_file()
            gone = await api.delete(f"/api/chats/{scratch}")
            also = await api.delete(f"/api/chats/{kept}")
    assert written and (gone.status_code, also.status_code) == (204, 204)
    assert not (home / "work" / scratch).exists()
    assert (chosen / "keep.txt").read_text() == "mine"
    assert (chosen / "note.txt").read_text() == "from message 1"


@pytest.mark.parametrize("tampered", ["precious", "work/{chat}"])
def test_a_folder_in_a_tampered_chats_file_is_treated_as_chosen_and_kept(
    client, home, tampered
):
    chat = client.post("/api/chats").json()["id"]
    folder = home / tampered.format(chat=chat)
    folder.mkdir(parents=True)
    (folder / "keep.txt").write_text("mine")
    with closing(sqlite3.connect(home / "chats.sqlite")) as connection, connection:
        connection.execute("UPDATE chats SET folder = ?", (str(folder),))
    deleted = client.delete(f"/api/chats/{chat}")
    assert deleted.status_code == 204
    assert (folder / "keep.txt").read_text() == "mine"
