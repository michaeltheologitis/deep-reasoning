import pytest
from fastapi.testclient import TestClient

from deep_reasoning.app import WEB, create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_root_serves_the_ui(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Deep Reasoning</title>" in response.text


@pytest.mark.parametrize("path", ["app.js", "style.css", "data/library.json"])
def test_static_assets_are_served(client, path):
    response = client.get(f"/{path}")
    assert response.status_code == 200
    assert response.content == (WEB / path).read_bytes()
