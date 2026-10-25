import pytest
from fastapi.testclient import TestClient

from deep_reasoning.app import WEB, create_app

LOCAL = "http://127.0.0.1"
VALID = """name: next course
messages:
- role: user
  content: What comes after CS201?
- role: assistant
  content: <repl>FinalAnswer("CS310")</repl>
"""


@pytest.fixture
def client(imported):
    return TestClient(create_app(imported), base_url=LOCAL)


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
        "yaml": VALID.rstrip(),
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
