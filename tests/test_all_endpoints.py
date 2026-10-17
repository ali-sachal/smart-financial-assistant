import time
from datetime import date, timedelta
from types import SimpleNamespace

import jwt
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import rsa

from ai.agents.finance_agent import finance_agent
from app.core.config import settings
from app.core.security import token_verifier
from app.main import app
from app.schemas.finance import ReceiptExtraction
from app.services.receipt_service import receipt_service


class ReviewReceiptGateway:
    def extract_receipt(self, data: bytes, mime_type: str) -> ReceiptExtraction:
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert mime_type == "image/png"
        return ReceiptExtraction(
            merchant="Endpoint Test Market",
            transaction_date=date.today(),
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=1080,
            currency="USD",
            category="groceries",
            confidence=0.50,
        )


class UnavailableAgentGateway:
    available = False


class FakeJwksClient:
    def __init__(self, public_key):
        self.public_key = public_key

    def get_signing_key_from_jwt(self, _: str):
        return SimpleNamespace(key=self.public_key)


def access_token(private_key, user_id: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": user_id,
            "iss": (
                f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
                f"{settings.COGNITO_USER_POOL_ID}"
            ),
            "client_id": settings.COGNITO_APP_CLIENT_ID,
            "token_use": "access",
            "iat": now,
            "exp": now + 300,
            "scope": "openid profile",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "endpoint-test-key"},
    )


def test_every_documented_api_operation(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(token_verifier, "_client", lambda: FakeJwksClient(private_key.public_key()))
    monkeypatch.setattr(receipt_service, "gateway", ReviewReceiptGateway())
    monkeypatch.setattr(finance_agent, "gateway", UnavailableAgentGateway())
    primary_headers = {"Authorization": f"Bearer {access_token(private_key, 'all-endpoints-user')}"}
    other_headers = {"Authorization": f"Bearer {access_token(private_key, 'other-endpoints-user')}"}
    covered: set[tuple[str, str]] = set()

    def call(client: TestClient, method: str, path: str, **kwargs):
        kwargs.setdefault("headers", primary_headers)
        response = client.request(method, path, **kwargs)
        covered.add((method.upper(), path.split("?", maxsplit=1)[0]))
        assert response.status_code < 400, (
            f"{method.upper()} {path} failed with {response.status_code}: {response.text}"
        )
        assert response.json()["success"] is True
        assert response.json()["request_id"]
        return response

    today = date.today()
    month = today.strftime("%Y-%m")

    try:
        with TestClient(app) as client:
            missing_token = client.get("/api/accounts")
            assert missing_token.status_code == 401
            assert missing_token.json()["code"] == "AUTH_TOKEN_MISSING"

            call(client, "GET", "/api/health/check")
            call(client, "GET", "/api/auth/me")
            call(client, "POST", "/api/demo/seed")
            call(client, "GET", "/api/profile")
            call(
                client,
                "PUT",
                "/api/profile",
                json={
                    "currency": "USD",
                    "timezone": "UTC",
                    "monthly_income_minor": 500000,
                    "opening_balance_minor": 240000,
                    "safety_buffer_minor": 75000,
                },
            )
            call(client, "GET", "/api/accounts")
            call(client, "GET", "/api/transactions?limit=10")
            transaction = call(
                client,
                "POST",
                "/api/transactions",
                json={
                    "account_id": "checking",
                    "amount_minor": 3250,
                    "currency": "USD",
                    "transaction_type": "expense",
                    "category": "dining",
                    "merchant": "Endpoint Cafe",
                    "posted_at": today.isoformat(),
                    "source": "manual",
                    "notes": "Endpoint coverage",
                },
            ).json()["result"]

            isolated_list = client.get("/api/transactions?limit=200", headers=other_headers)
            assert isolated_list.status_code == 200
            assert transaction["transaction_id"] not in {
                item["transaction_id"] for item in isolated_list.json()["result"]["items"]
            }
            cross_user_update = client.patch(
                f"/api/transactions/{transaction['transaction_id']}",
                headers=other_headers,
                json={"category": "unauthorized-change"},
            )
            assert cross_user_update.status_code == 404
            assert cross_user_update.json()["code"] == "FIN_TRANSACTION_NOT_FOUND"

            call(
                client,
                "PATCH",
                f"/api/transactions/{transaction['transaction_id']}",
                json={"category": "food", "notes": "Updated by endpoint test"},
            )
            call(client, "GET", f"/api/budgets/{month}/dining")
            call(
                client,
                "PUT",
                f"/api/budgets/{month}/dining",
                json={"limit_minor": 30000, "currency": "USD"},
            )
            call(client, "GET", "/api/bills?days=30")
            bill = call(
                client,
                "POST",
                "/api/bills",
                json={
                    "name": "Endpoint Test Bill",
                    "amount_minor": 12500,
                    "currency": "USD",
                    "category": "utilities",
                    "kind": "expense",
                    "next_due_date": (today + timedelta(days=7)).isoformat(),
                    "frequency": "monthly",
                    "active": True,
                },
            ).json()["result"]
            call(
                client,
                "PATCH",
                f"/api/bills/{bill['bill_id']}",
                json={"amount_minor": 13000, "active": True},
            )
            call(client, "GET", f"/api/dashboard?month={month}")
            call(client, "GET", "/api/forecast?days=30")

            png = b"\x89PNG\r\n\x1a\n" + b"endpoint-receipt"
            receipt = call(
                client,
                "POST",
                "/api/receipts/scan",
                files={"file": ("endpoint.png", png, "image/png")},
            ).json()["result"]
            assert receipt["status"] == "needs_review"
            call(client, "GET", f"/api/receipts/{receipt['receipt_id']}")
            corrected_receipt = call(
                client,
                "PATCH",
                f"/api/receipts/{receipt['receipt_id']}",
                json={
                    "merchant": "Corrected Market",
                    "transaction_date": today.isoformat(),
                    "total_minor": 1080,
                    "currency": "USD",
                    "category": "groceries",
                    "confirm": True,
                },
            ).json()["result"]
            assert corrected_receipt["status"] == "parsed"
            assert corrected_receipt["transaction_id"]

            conversation_id = call(
                client,
                "POST",
                "/api/chat",
                json={"message": "Can I afford $300?"},
            ).json()["result"]["conversation_id"]
            call(client, "GET", f"/api/conversations/{conversation_id}")

            assert client.get("/").status_code == 200
            assert client.get("/docs").status_code == 200
            assert client.get("/openapi.json").status_code == 200

        route_templates = {
            (method.upper(), path)
            for path, operations in app.openapi()["paths"].items()
            for method in operations
            if method.lower() in {"get", "post", "put", "patch", "delete"}
        }
        covered_templates = {
            (method, "/api/transactions/{transaction_id}")
            if path.startswith("/api/transactions/")
            else (method, "/api/budgets/{month}/{category}")
            if path.startswith("/api/budgets/")
            else (method, "/api/bills/{bill_id}")
            if path.startswith("/api/bills/")
            else (method, "/api/receipts/{receipt_id}")
            if path.startswith("/api/receipts/") and path != "/api/receipts/scan"
            else (method, "/api/conversations/{conversation_id}")
            if path.startswith("/api/conversations/")
            else (method, path)
            for method, path in covered
        }
        assert covered_templates == route_templates
    finally:
        app.dependency_overrides.clear()
