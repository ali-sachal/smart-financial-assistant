from fastapi.testclient import TestClient

from app.main import app


def test_application_boots_and_exposes_generic_routes():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health/check" in paths
    assert "/api/auth/dev-token" in paths
    assert "/api/example/ping" in paths
    assert not any("resume" in path or "coverletter" in path for path in paths)


def test_request_context_headers_are_returned():
    with TestClient(app) as client:
        response = client.get("/api/example/ping", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.headers["X-Response-Time"].endswith("ms")


def test_local_development_token_round_trip():
    with TestClient(app) as client:
        token_response = client.post("/api/auth/dev-token", json={"user_id": "user-123"})
        token = token_response.json()["result"]["access_token"]
        response = client.get(
            "/api/example/whoami",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["result"]["user_id"] == "user-123"
