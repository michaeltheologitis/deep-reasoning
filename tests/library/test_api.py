import io
import json
import os
import zipfile

import pytest
import yaml
from starlette.testclient import TestClient

from deep_reasoning.library import shapes
from deep_reasoning.library.api import create_app, same_user_peer
from tests.library.conftest import example, text

PORT = 8123
ORIGIN = f"http://127.0.0.1:{PORT}"
SUMMARIZE = {
    "name": "summarize then rank",
    "messages": [
        {
            "role": "user",
            "content": "Summarize each CS course, then rank them by workload.",
        },
        {"role": "assistant", "content": "<think>…</think>\n<repl>\n…\n</repl>\n"},
    ],
}


@pytest.fixture
def client(lib, router):
    lib.import_config(router)
    app = create_app(lib, same_user=lambda client, server: True)
    return TestClient(app, base_url=ORIGIN)


def put(client, path, **body):
    return client.put(path, json=body)


def test_health_reports_the_revision_and_default_namespace(client, lib):
    assert client.get("/health").json() == {
        "ok": True,
        "rev": 2,
        "path": str(lib.path),
        "deep_reasoner": shapes.deep_reasoner_build(),
        "default_namespace": "router",
    }


@pytest.mark.parametrize(
    ("path", "shape"),
    [
        ("/problems", []),
        (
            "/profile",
            {"version": 2, "decompositions": [], "default_namespace": "router"},
        ),
        ("/namespaces", ["root", "router", "courses"]),
        (
            "/namespaces/courses",
            {"name": "courses", "decompositions": ["catalog lookup"]},
        ),
        (
            "/namespaces/courses/effective",
            {"namespace": "courses", "chain": ["root", "courses"]},
        ),
        ("/effective", ["root", "router", "courses"]),
        ("/decompositions", ["catalog lookup", "decline", "route a course question"]),
        (
            "/decompositions/catalog-lookup",
            {"name": "catalog lookup", "namespaces": ["courses"]},
        ),
        ("/tools", []),
        ("/profile/versions", [2, 1]),
        ("/profile/versions/1", {"version": 1, "yaml": "{}\n", "action": "create"}),
        ("/namespaces/router/versions", [1]),
        ("/decompositions/catalog-lookup/versions", [1]),
    ],
)
def test_every_read_answers_its_records(client, path, shape):
    response = client.get(path)
    assert response.status_code == 200
    found = response.json()
    if isinstance(shape, list) and shape and isinstance(shape[0], int):
        assert [entry["version"] for entry in found] == shape
    elif isinstance(shape, list):
        assert [entry.get("name", entry.get("namespace")) for entry in found] == shape
    else:
        assert {key: found[key] for key in shape} == shape


def test_records_carry_yaml_and_parsed_data(client):
    record = client.get("/namespaces/router").json()
    assert record["yaml"] == "name: router\nspawn:\n- courses\n"
    assert record["data"] == {"name": "router", "spawn": ["courses"]}
    assert set(record) == {
        "version",
        "rev",
        "saved_at",
        "name",
        "yaml",
        "decompositions",
        "data",
    }


def test_creating_a_decomposition_answers_201_and_updating_200(client):
    body = {
        "yaml": json.dumps(SUMMARIZE),
        "use_when": "comparing many courses",
        "hint": "what to compare",
        "namespaces": ["router"],
        "base_version": 0,
    }
    created = put(client, "/decompositions/summarize-then-rank", **body)
    assert created.status_code == 201
    record = created.json()
    assert {k: v for k, v in record.items() if k != "saved_at"} == {
        "version": 1,
        "rev": 3,
        "name": "summarize then rank",
        "slug": "summarize-then-rank",
        "yaml": "name: summarize then rank\nmessages:\n- role: user\n  content: Summarize each CS "
        "course, then rank them by workload.\n- role: assistant\n  content: |\n    "
        "<think>…</think>\n    <repl>\n    …\n    </repl>\n",
        "use_when": "comparing many courses",
        "hint": "what to compare",
        "namespaces": ["router"],
        "top_level": False,
        "data": SUMMARIZE,
    }
    assert record["saved_at"].endswith("Z")
    updated = put(
        client,
        "/decompositions/summarize-then-rank",
        **{**body, "base_version": 1, "hint": None},
    )
    assert (updated.status_code, updated.json()["version"], updated.json()["hint"]) == (
        200,
        2,
        None,
    )


def test_every_write_route(client):
    assert put(client, "/namespaces/math", yaml="name: math").status_code == 201
    assert (
        put(client, "/namespaces/math", yaml="name: math\ntools: [llm]").status_code
        == 200
    )
    tool = put(client, "/tools/search", yaml="factory: llm", granted_in=["math"])
    assert (tool.status_code, tool.json()["granted_in"]) == (201, ["math"])
    profile = put(
        client, "/profile", yaml="model: m\nentry_namespace: math", base_version=2
    )
    assert (profile.status_code, profile.json()["default_namespace"]) == (200, "math")
    assert client.get("/tools/search/versions/1").json()["yaml"] == "factory: llm\n"
    gone = client.delete("/tools/search", params={"base_version": 1})
    assert (gone.status_code, gone.json()["deleted"], gone.json()["kind"]) == (
        200,
        True,
        "tool",
    )
    gone = client.delete("/decompositions/decline")
    assert (gone.json()["name"], gone.json()["slug"]) == ("decline", "decline")
    assert client.delete("/namespaces/courses").json()["version"] == 2


def test_validate_answers_200_even_when_invalid(client):
    response = client.post(
        "/validate", json={"kind": "decomposition", "yaml": "name: x\nmessages: []"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "ok": False,
        "message": "'x' is not a valid deep_reasoner Decomposition:\n"
        "  messages: List should have at least 1 item after validation, not 0",
        "errors": [
            {
                "loc": "messages",
                "msg": "List should have at least 1 item after validation, not 0",
            }
        ],
        "warnings": [],
        "name": "x",
        "slug": "x",
        "yaml": None,
    }


def test_errors_carry_code_message_and_details(client):
    invalid = put(
        client,
        "/decompositions/x",
        yaml="name: x\nuse_when: one course\nmessages: [{role: user, content: hi}]",
    )
    assert (invalid.status_code, invalid.json()) == (
        422,
        {
            "error": "invalid",
            "message": "'x' is not a valid deep_reasoner Decomposition:\n"
            "  use_when: Extra inputs are not permitted\n"
            "Use-when text is stored beside the YAML: pass use_when=... instead.",
            "errors": [{"loc": "use_when", "msg": "Extra inputs are not permitted"}],
        },
    )
    put(client, "/decompositions/decline", yaml=text(example("decline", "Edited?")))
    conflict = put(
        client, "/decompositions/decline", yaml=text(example("decline")), base_version=0
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "conflict"
    assert (
        conflict.json()["message"]
        == "Decomposition 'decline' already exists, at version 2."
    )
    assert (
        conflict.json()["head"]["version"],
        conflict.json()["head"]["namespaces"],
    ) == (2, ["router"])
    missing = client.get("/namespaces/nowhere")
    assert (missing.status_code, missing.json()) == (
        404,
        {
            "error": "not_found",
            "message": "There is no namespace 'nowhere' in the library.",
        },
    )
    refused = client.delete("/namespaces/root")
    assert (refused.status_code, refused.json()["error"]) == (409, "refused")
    for body in ({"yml": "name: a"}, {"yaml": "name: a", "base_version": "two"}):
        bad = put(client, "/namespaces/a", **body)
        assert (bad.status_code, bad.json()["error"]) == (400, "bad_request")
    stale = client.delete("/namespaces/router", params={"base_version": "x"})
    assert (stale.status_code, stale.json()["error"]) == (400, "bad_request")


def test_a_slug_with_spaces_in_the_name_round_trips(client):
    put(
        client,
        "/decompositions/rank-by-prerequisites",
        yaml=text(example("Rank by prerequisites")),
    )
    got = client.get("/decompositions/rank-by-prerequisites").json()
    assert (got["name"], got["slug"]) == (
        "Rank by prerequisites",
        "rank-by-prerequisites",
    )
    assert (
        client.get("/decompositions/rank-by-prerequisites/versions").json()[0][
            "version"
        ]
        == 1
    )


@pytest.mark.parametrize(
    ("path", "yaml_text", "kind"),
    [
        ("/namespaces/other", "name: math", "namespace"),
        ("/decompositions/other", text(example("decline")), "decomposition"),
    ],
)
def test_the_path_key_must_match_the_yaml(client, path, yaml_text, kind):
    response = put(client, path, yaml=yaml_text)
    assert response.status_code == 400
    assert response.json()["message"].startswith("The YAML names ")
    assert response.json()["message"].endswith(
        f"A new name is a new {kind}: save it at its own address."
    )


def test_export_is_a_zip_of_a_materialized_directory(client):
    response = client.get("/export", params={"namespace": "courses"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="library-rev2.zip"'
    )
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    assert sorted(archive.namelist()) == [
        "library/library.yaml",
        "library/main.yaml",
        "library/namespaces/courses.yaml",
        "library/namespaces/root.yaml",
        "library/namespaces/router.yaml",
    ]
    assert (
        yaml.safe_load(archive.read("library/main.yaml"))["entry_namespace"]
        == "courses"
    )


@pytest.mark.parametrize(
    "host", ["evil.example:8123", "127.0.0.1:9", "127.0.0.1", "[::1]:8123"]
)
def test_a_request_addressed_to_another_host_is_refused(client, host):
    response = client.get("/health", headers={"Host": host})
    assert (response.status_code, response.json()) == (
        403,
        {
            "error": "forbidden",
            "message": "This library answers only requests addressed to 127.0.0.1:8123 or "
            "localhost:8123.",
        },
    )
    assert client.get("/health", headers={"Host": "localhost:8123"}).status_code == 200


@pytest.mark.parametrize(
    "content_type", ["text/plain", "application/x-www-form-urlencoded", None]
)
@pytest.mark.parametrize(
    ("method", "path", "sent"),
    [
        ("PUT", "/namespaces/a", {"yaml": "name: a"}),
        ("POST", "/validate", {"kind": "namespace", "yaml": "name: a"}),
    ],
)
def test_a_body_that_is_not_sent_as_json_is_refused(
    client, lib, method, path, sent, content_type
):
    body = json.dumps(sent)
    headers = {"Content-Type": content_type} if content_type else {}
    response = client.request(method, path, content=body, headers=headers)
    assert (response.status_code, response.json()["error"]) == (
        415,
        "unsupported_media_type",
    )
    assert lib.rev() == 2
    as_json = {"Content-Type": "application/json; charset=utf-8"}
    assert client.request(method, path, content=body, headers=as_json).status_code in (
        200,
        201,
    )


def test_another_users_connection_is_refused(lib):
    app = create_app(lib, same_user=lambda client, server: False)
    response = TestClient(app, base_url=ORIGIN).get("/health")
    assert (response.status_code, response.json()) == (
        403,
        {
            "error": "forbidden",
            "message": "This library belongs to another user on this computer.",
        },
    )


def proc_net(tmp_path, rows: list[tuple[str, str, int]]):
    """A /proc/net with a tcp table holding (local, remote, uid) rows and an empty tcp6."""
    header = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"
    lines = [
        f"   {i}: {local} {remote} 01 00000000:00000000 00:00000000 00000000  {uid}        0 {1000 + i} 1"
        for i, (local, remote, uid) in enumerate(rows)
    ]
    (tmp_path / "tcp").write_text(header + "\n".join(lines) + "\n")
    (tmp_path / "tcp6").write_text(header)
    return tmp_path


CLIENT, SERVER = ("127.0.0.1", 51000), ("127.0.0.1", 8123)
# 127.0.0.1:51000 and 127.0.0.1:8123 as a little-endian kernel prints them.
CLIENT_HEX, SERVER_HEX = "0100007F:C738", "0100007F:1FBB"


@pytest.mark.parametrize(
    ("rows", "same"),
    [
        ([(CLIENT_HEX, SERVER_HEX, os.getuid())], True),
        ([(CLIENT_HEX, SERVER_HEX, os.getuid() + 1)], False),
        ([(SERVER_HEX, CLIENT_HEX, os.getuid())], False),
        ([], False),
    ],
    ids=["mine", "another-user", "server-side-row-only", "no-row"],
)
def test_same_user_peer_reads_the_client_sockets_owner(tmp_path, rows, same):
    assert same_user_peer(CLIENT, SERVER, proc_net=proc_net(tmp_path, rows)) is same
