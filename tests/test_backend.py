def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_unknown_url_is_404(client):
    assert client.get("/api/does-not-exist").status_code == 404
