from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.schemas.auth import AuthenticatedUser


def demo_user(user_id: str = "user-123") -> AuthenticatedUser:
    return AuthenticatedUser(user_id=user_id, email="demo@example.com")


def test_application_boots_with_finance_routes_only():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/health/check" in paths
    assert "/api/auth/me" in paths
    assert "/api/dashboard" in paths
    assert "/api/receipts/scan" in paths
    assert "/api/chat" in paths
    assert "/api/auth/dev-token" not in paths


def test_request_context_headers_are_returned():
    with TestClient(app) as client:
        response = client.get("/api/health/check", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request"
    assert response.headers["X-Response-Time"].endswith("ms")
    assert response.json()["request_id"] == "test-request"


def test_missing_cognito_token_uses_standard_error_contract():
    with TestClient(app) as client:
        response = client.get("/api/accounts")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_TOKEN_MISSING"
    assert response.json()["request_id"]


def test_authenticated_identity_and_finance_journey():
    app.dependency_overrides[get_current_user] = demo_user
    try:
        with TestClient(app) as client:
            assert client.get("/api/auth/me").json()["result"]["user_id"] == "user-123"
            seeded = client.post("/api/demo/seed")
            dashboard = client.get("/api/dashboard")
            advice = client.post("/api/chat", json={"message": "Can I afford $300?"})
        assert seeded.status_code == 200
        assert dashboard.status_code == 200
        assert dashboard.json()["result"]["balance"]["balance_minor"] == 240000
        assert advice.status_code == 200
        assert advice.json()["result"]["tool_results"][0]["tool"] == "get_cashflow_forecast"
    finally:
        app.dependency_overrides.clear()
