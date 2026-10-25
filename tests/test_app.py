import json
import threading
from contextlib import closing

import httpx
import pytest
from fake_model import FakeOpenAI, repl, scripted
from fastapi.testclient import TestClient

from deep_reasoning.app import WEB, create_app
from deep_reasoning.library import (
    UPSERT_SETTING,
    dump,
    import_config,
    open_library,
    writing,
)

LOCAL = "http://127.0.0.1"
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


@pytest.mark.parametrize("path", ["app.js", "style.css", "library.js"])
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
    assert settings["model"] == {"value": "gpt-6-luna", "source": "set in the Library"}
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
            run = await send(api, "a-chat", "Count to two.")
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
async def test_a_follow_up_runs_with_the_chat_so_far(library_on, connect):
    with FakeOpenAI(scripted(PLAN)) as fake:
        async with connect(library_on(fake)) as api:
            await run_events(api, await send(api, "a-chat", "Count to two."))
            await run_events(api, await send(api, "a-chat", "What did I ask?"))
            await run_events(api, await send(api, "another-chat", "What did I ask?"))
    follow_up, fresh = fake.calls[-2].messages, fake.calls[-1].messages
    assert "Message 1: Count to two.\nAnswer 1: 2\n" in follow_up[-2]["content"]
    assert all("Count to two." not in message["content"] for message in fresh)


@pytest.mark.anyio
async def test_a_chat_keeps_the_namespace_it_started_in(imported, library_on, connect):
    plan = {"Hi.": [repl("FinalAnswer('hello')")]}
    with FakeOpenAI(scripted(plan)) as fake:
        async with connect(library_on(fake)) as api:
            first = await run_events(api, await send(api, "a-chat", "Hi."))
            with closing(open_library(imported)) as connection, writing(connection):
                default = ("entry_namespace", dump("course_advisor"))
                connection.execute(UPSERT_SETTING, default)
            again = await run_events(api, await send(api, "a-chat", "Hi."))
            new = await run_events(api, await send(api, "another-chat", "Hi."))
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
            run = await send(api, "a-chat", "Join.")
            events = await run_events(api, run)
    assert events[-1]["outcome"] == "answered", events[-1]
    assert events[-1]["answer"] == "enrolled"
    assert (home / "runs" / run / "tools" / "waitlist.py").is_file()


@pytest.mark.anyio
async def test_a_second_message_while_a_run_is_going_is_refused(library_on, connect):
    release = threading.Event()
    follow = scripted(PLAN)

    def held(messages):
        release.wait(HELD_S)
        return follow(messages)

    with FakeOpenAI(held) as fake:
        async with connect(library_on(fake)) as api:
            run = await send(api, "a-chat", "Count to two.")
            refused = await api.post(
                "/api/chats/a-chat/runs", json={"prompt": "What did I ask?"}
            )
            stopped = await api.post(f"/api/runs/{run}/stop")
            events = await run_events(api, run)
            release.set()
            again = await api.post(f"/api/runs/{run}/stop")
    assert refused.status_code == 409
    assert refused.json() == {"detail": "Chat a-chat has a run going."}
    assert stopped.status_code == 200
    assert events[-1]["outcome"] == "stopped"
    assert again.status_code == 409


@pytest.mark.parametrize(
    ("chat", "prompt"), [("a chat!", "Hi."), ("x" * 101, "Hi."), ("a-chat", "")]
)
def test_a_bad_chat_id_or_an_empty_message_is_refused(client, chat, prompt):
    response = client.post(f"/api/chats/{chat}/runs", json={"prompt": prompt})
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("run", "status"), [("20261025-120000-000000", 404), ("not-a-run", 422)]
)
def test_a_run_that_is_not_there_is_refused(client, run, status):
    assert client.get(f"/api/runs/{run}/events").status_code == status
    assert client.post(f"/api/runs/{run}/stop").status_code == status
