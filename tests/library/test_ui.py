import json
import re
from importlib import metadata, resources

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from deep_reasoning.library import texts
from deep_reasoning.library.api import create_app
from deep_reasoning.library.ui import UI_HEADERS, UI_ROOT, ui_routes

PORT = 8123
ORIGIN = f"http://127.0.0.1:{PORT}"
KEBAB = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
PACKAGE = resources.files("deep_reasoning.canvas_app")


@pytest.fixture
def built(tmp_path):
    """A build of our own: index.html and two assets, with a secret beside the root."""
    root = tmp_path / "ui"
    (root / "assets" / "nested").mkdir(parents=True)
    (root / "index.html").write_text('<script src="./assets/app.js"></script>\n')
    (root / "assets" / "app.js").write_text("export {};\n")
    (root / "assets" / "app.css").write_text("body {}\n")
    (root / "assets" / "nested" / "deep.js").write_text("nested\n")
    (tmp_path / "secret.txt").write_text("not for the browser\n")
    return root


def serving(root):
    return TestClient(Starlette(routes=ui_routes(root)), base_url=ORIGIN)


@pytest.fixture
def library_app(lib):
    return TestClient(create_app(lib, same_user=lambda c, s: True), base_url=ORIGIN)


def test_ui_serves_the_index_and_the_built_assets(library_app):
    index = library_app.get("/ui/?tab=create&namespace=router")
    script = library_app.get("/ui/assets/app.js")
    assert index.status_code == 200
    assert index.headers["content-type"].startswith("text/html")
    assert index.content == (UI_ROOT / "index.html").read_bytes()
    assert script.status_code == 200
    assert script.headers["content-type"].startswith("text/javascript")
    assert script.content == (UI_ROOT / "assets" / "app.js").read_bytes()


def test_a_file_not_in_the_build_is_404(built):
    client = serving(built)
    (built / "assets" / "late.js").write_text("written after start-up\n")
    for name in ("missing.js", "late.js", "nested"):
        response = client.get(f"/ui/assets/{name}")
        assert response.status_code == 404
        assert response.json() == {
            "error": "not_found",
            "message": texts.ui_file_missing(name),
        }


@pytest.mark.parametrize(
    "path",
    [
        "/ui/assets/..%2F..%2Fsecret.txt",
        "/ui/assets/%2e%2e/%2e%2e/secret.txt",
        "/ui/assets/nested/deep.js",
        "/ui/assets/nested%2Fdeep.js",
        "/ui/..%2Fsecret.txt",
        "/ui/index.html",
    ],
)
def test_no_path_outside_the_assets_is_served(built, path):
    response = serving(built).get(path, follow_redirects=False)
    assert response.status_code == 404
    assert b"not for the browser" not in response.content
    assert b"nested" not in response.content


@pytest.mark.parametrize(
    "path", ["/ui/", "/ui/assets/app.js", "/ui/assets/app.css", "/ui/assets/missing.js"]
)
def test_every_answer_carries_the_csp_and_no_cache(built, path):
    headers = serving(built).get(path).headers
    assert {name: headers[name] for name in UI_HEADERS} == UI_HEADERS


def test_an_unbuilt_ui_is_503_with_its_sentence(tmp_path):
    response = serving(tmp_path / "never-built").get("/ui/")
    assert response.status_code == 503
    assert response.json()["message"] == texts.UI_NOT_BUILT
    assert {name: response.headers[name] for name in UI_HEADERS} == UI_HEADERS


def test_the_ui_answers_only_its_own_host(library_app):
    response = library_app.get("/ui/", headers={"Host": f"evil.example:{PORT}"})
    assert response.status_code == 403
    assert response.json()["message"] == texts.forbidden_host(PORT)


def test_the_manifest_is_valid_and_its_version_is_the_packages():
    manifest = json.loads(PACKAGE.joinpath("canvas-extension.json").read_text())
    [panel] = manifest["contributes"]["conversation_panels"]
    assert manifest["name"] == "dr-library"
    assert manifest["version"] == metadata.version("deep-reasoning")
    assert PACKAGE.joinpath(manifest["entrypoint"]).is_file()
    assert PACKAGE.joinpath(panel["icon"]).is_file()
    assert panel["id"] == "decompositions"
    assert panel["title"] == "Decompositions"
    assert [(tab["id"], tab["path"]) for tab in panel["tabs"]] == [
        ("browse", "/"),
        ("create", "/create"),
        ("namespaces", "/namespaces"),
        ("tools", "/tools"),
    ]
    assert all(
        KEBAB.fullmatch(i) for i in [panel["id"], *(t["id"] for t in panel["tabs"])]
    )


def test_the_committed_build_is_complete():
    index = (UI_ROOT / "index.html").read_text()
    referenced = re.findall(r'(?:src|href)="([^"]+)"', index)
    assert PACKAGE.joinpath("dist", "index.js").is_file()
    assert "./assets/app.js" in referenced
    for reference in referenced:
        assert reference.startswith("./assets/"), reference
        assert (UI_ROOT / reference).is_file(), reference
    # D4: the tool editor's CodeMirror, loaded by app.js when the editor opens.
    assert "./editor.js" in (UI_ROOT / "assets" / "app.js").read_text()
    assert (UI_ROOT / "assets" / "editor.js").is_file()
