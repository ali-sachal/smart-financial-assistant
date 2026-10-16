from datetime import date, timedelta

from fastapi.testclient import TestClient

from ai.agents.finance_agent import finance_agent
from app.core.security import get_current_user
from app.main import app
from app.schemas.auth import AuthenticatedUser
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


def test_every_documented_api_operation(monkeypatch):
    user = AuthenticatedUser(user_id="all-endpoints-user", email="endpoints@example.com")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(receipt_service, "gateway", ReviewReceiptGateway())
    monkeypatch.setattr(finance_agent, "gateway", UnavailableAgentGateway())
    covered: set[tuple[str, str]] = set()

    def call(client: TestClient, method: str, path: str, **kwargs):
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
