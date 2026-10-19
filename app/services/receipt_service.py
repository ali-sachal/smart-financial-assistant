import hashlib
import uuid
from datetime import date
from typing import Any

from fastapi import UploadFile

from ai.gemini import GeminiGateway, gemini_gateway
from app.core.config import settings
from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.models.finance import EntityType, ReceiptEntity
from app.repositories.finance import (
    FinanceRepository,
    ReceiptObjectRepository,
    finance_repository,
    receipt_object_repository,
)
from app.schemas.finance import ReceiptUpdate, TransactionCreate
from app.services.finance_service import FinanceService, finance_service, public_item, user_pk, utc_now
from app.utils.logging import get_module_logger

logger = get_module_logger("services")


class ReceiptService:
    def __init__(
        self,
        repository: FinanceRepository = finance_repository,
        object_repository: ReceiptObjectRepository = receipt_object_repository,
        gateway: GeminiGateway = gemini_gateway,
        finances: FinanceService = finance_service,
    ) -> None:
        self.repository = repository
        self.object_repository = object_repository
        self.gateway = gateway
        self.finances = finances

    async def scan(self, user_id: str, upload: UploadFile) -> dict[str, Any]:
        data = await upload.read(settings.RECEIPT_MAX_BYTES + 1)
        if len(data) > settings.RECEIPT_MAX_BYTES:
            raise AppException(ResponseCode.PAYLOAD_TOO_LARGE, Message.RECEIPT_TOO_LARGE, error_code=ErrorCode.FIN_RECEIPT_TOO_LARGE)
        content_type = self._validate_content(data, upload.content_type or "")
        digest = hashlib.sha256(data).hexdigest()
        duplicate = self.repository.find_receipt_hash(user_id, digest)
        if duplicate:
            raise AppException(
                ResponseCode.CONFLICT,
                Message.RESOURCE_ALREADY_EXISTS,
                details={"receipt_id": duplicate.get("receipt_id")},
                error_code=ErrorCode.FIN_RECEIPT_DUPLICATE,
            )
        receipt_id = str(uuid.uuid4())
        extension = {"image/jpeg": "jpg", "image/png": "png", "application/pdf": "pdf"}[content_type]
        s3_key = f"users/{user_id}/receipts/{receipt_id}.{extension}"
        self.object_repository.put(s3_key, data, content_type)
        extraction = self.gateway.extract_receipt(data, content_type)
        valid = bool(extraction.merchant and extraction.transaction_date and extraction.total_minor and extraction.total_minor > 0)
        status = "parsed" if valid and extraction.confidence >= settings.RECEIPT_AUTO_CREATE_CONFIDENCE else "needs_review"
        transaction_id = None
        if status == "parsed":
            transaction = self.finances.create_transaction(
                user_id,
                TransactionCreate(
                    amount_minor=extraction.total_minor,
                    currency=extraction.currency,
                    transaction_type="expense",
                    category=extraction.category,
                    merchant=extraction.merchant,
                    posted_at=extraction.transaction_date,
                    source="receipt",
                ),
                receipt_id=receipt_id,
            )
            transaction_id = transaction["transaction_id"]
        now = utc_now()
        entity = ReceiptEntity(
            PK=user_pk(user_id), SK=f"RECEIPT#{receipt_id}", entity_type=EntityType.RECEIPT,
            created_at=now, updated_at=now, receipt_id=receipt_id, s3_key=s3_key,
            content_type=content_type, sha256=digest, status=status,
            extraction=extraction.model_dump(mode="json"), transaction_id=transaction_id,
        )
        item = self.repository.put(entity.to_item(), must_not_exist=True)
        logger.info("event=receipt_scanned user_id=%s receipt_id=%s status=%s", user_id, receipt_id, status)
        return self._public_receipt(item)

    def get(self, user_id: str, receipt_id: str) -> dict[str, Any]:
        item = self.repository.get(user_id, f"RECEIPT#{receipt_id}")
        if not item:
            raise AppException(ResponseCode.NOT_FOUND, Message.RECEIPT_NOT_FOUND, error_code=ErrorCode.FIN_RECEIPT_NOT_FOUND)
        return self._public_receipt(item)

    def update(self, user_id: str, receipt_id: str, payload: ReceiptUpdate) -> dict[str, Any]:
        item = self.repository.get(user_id, f"RECEIPT#{receipt_id}")
        if not item:
            raise AppException(ResponseCode.NOT_FOUND, Message.RECEIPT_NOT_FOUND, error_code=ErrorCode.FIN_RECEIPT_NOT_FOUND)
        extraction = {**item.get("extraction", {}), **payload.model_dump(exclude_none=True, exclude={"confirm"}, mode="json")}
        transaction_id = item.get("transaction_id")
        if payload.confirm and not transaction_id:
            required = [extraction.get("merchant"), extraction.get("transaction_date"), extraction.get("total_minor")]
            if not all(required):
                raise AppException(ResponseCode.BAD_REQUEST, Message.RECEIPT_INVALID, error_code=ErrorCode.FIN_RECEIPT_INVALID)
            transaction = self.finances.create_transaction(
                user_id,
                TransactionCreate(
                    amount_minor=int(extraction["total_minor"]), currency=extraction.get("currency", "USD"),
                    transaction_type="expense", category=extraction.get("category", "other"),
                    merchant=extraction["merchant"], posted_at=date.fromisoformat(extraction["transaction_date"]),
                    source="receipt",
                ),
                receipt_id=receipt_id,
            )
            transaction_id = transaction["transaction_id"]
        updated = {
            **item,
            "extraction": extraction,
            "transaction_id": transaction_id,
            "status": "parsed" if transaction_id else "needs_review",
            "updated_at": utc_now(),
            "version": int(item.get("version", 1)) + 1,
        }
        self.repository.put(updated)
        return self._public_receipt(updated)

    def _public_receipt(self, item: dict[str, Any]) -> dict[str, Any]:
        result = public_item(item)
        result.pop("s3_key", None)
        result.pop("sha256", None)
        return result

    def _validate_content(self, data: bytes, declared: str) -> str:
        detected = ""
        if data.startswith(b"\xff\xd8\xff"):
            detected = "image/jpeg"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            detected = "image/png"
        elif data.startswith(b"%PDF-"):
            detected = "application/pdf"
        if not detected or declared.split(";")[0].lower() != detected:
            raise AppException(ResponseCode.UNSUPPORTED_MEDIA_TYPE, Message.RECEIPT_INVALID, error_code=ErrorCode.FIN_RECEIPT_INVALID)
        return detected


receipt_service = ReceiptService()
