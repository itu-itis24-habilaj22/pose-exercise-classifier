import pytest

from backend.app import create_app
from backend.config import TestConfig


@pytest.fixture
def client():
    """A fake browser that sends requests to the app without starting a server."""
    return create_app(TestConfig).test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_unknown_url_is_404(client):
    assert client.get("/api/does-not-exist").status_code == 404
