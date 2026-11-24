def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "database": "ok"}


def test_unknown_url_is_404(client):
    assert client.get("/api/does-not-exist").status_code == 404


def test_cors_allows_the_react_dev_server_only(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    other = client.get("/api/health", headers={"Origin": "https://evil.example.com"})
    assert "Access-Control-Allow-Origin" not in other.headers
