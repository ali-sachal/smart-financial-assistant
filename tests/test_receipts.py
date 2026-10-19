from datetime import date

from fastapi.testclient import TestClient

from app.core.security import get_current_user
from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.finance import ReceiptExtraction
from app.services.finance_service import finance_service
from app.services.receipt_service import receipt_service


class FakeReceiptGateway:
    def extract_receipt(self, data: bytes, mime_type: str) -> ReceiptExtraction:
        assert data.startswith(b"\xff\xd8\xff")
        assert mime_type == "image/jpeg"
        return ReceiptExtraction(
            merchant="Demo Market",
            transaction_date=date.today(),
            subtotal_minor=1000,
            tax_minor=80,
            total_minor=1080,
            currency="USD",
            category="groceries",
            confidence=0.95,
        )


def test_receipt_creates_transaction_and_rejects_duplicate(monkeypatch):
    user = AuthenticatedUser(user_id="receipt-user")
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(receipt_service, "gateway", FakeReceiptGateway())
    finance_service.seed_demo(user.user_id)
    image = b"\xff\xd8\xff" + b"receipt-data"
    try:
        with TestClient(app) as client:
            first = client.post("/api/receipts/scan", files={"file": ("receipt.jpg", image, "image/jpeg")})
            duplicate = client.post("/api/receipts/scan", files={"file": ("receipt.jpg", image, "image/jpeg")})
        assert first.status_code == 201
        assert first.json()["result"]["status"] == "parsed"
        assert first.json()["result"]["transaction_id"]
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "FIN_RECEIPT_DUPLICATE"
    finally:
        app.dependency_overrides.clear()


def test_receipt_rejects_spoofed_media_type(monkeypatch):
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(user_id="receipt-invalid")
    monkeypatch.setattr(receipt_service, "gateway", FakeReceiptGateway())
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/receipts/scan",
                files={"file": ("fake.jpg", b"%PDF-fake", "image/jpeg")},
            )
        assert response.status_code == 415
        assert response.json()["code"] == "FIN_RECEIPT_INVALID"
    finally:
        app.dependency_overrides.clear()
