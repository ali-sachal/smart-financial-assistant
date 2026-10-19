import base64
import copy
import json
import threading
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.utils.logging import get_module_logger

logger = get_module_logger("repositories")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_decimal(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {key: _to_decimal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_decimal(item) for item in value]
    return value


def _from_decimal(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {key: _from_decimal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_from_decimal(item) for item in value]
    return value


class FinanceRepository:
    def __init__(self) -> None:
        self._memory: dict[tuple[str, str], dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._table = None
        self._client = None

    @property
    def uses_memory(self) -> bool:
        return settings.USE_IN_MEMORY_REPOSITORY

    def _dynamo_table(self):
        if self._table is None:
            resource = boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION,
                endpoint_url=settings.DYNAMODB_ENDPOINT_URL or None,
            )
            self._table = resource.Table(settings.FINANCE_TABLE_NAME)
            self._client = resource.meta.client
        return self._table

    def clear_user(self, user_id: str) -> None:
        pk = f"USER#{user_id}"
        try:
            items, cursor = self.query_prefix(user_id, "")
            while True:
                if self.uses_memory:
                    with self._lock:
                        for item in items:
                            self._memory.pop((item["PK"], item["SK"]), None)
                else:
                    with self._dynamo_table().batch_writer() as batch:
                        for item in items:
                            batch.delete_item(Key={"PK": pk, "SK": item["SK"]})
                if not cursor:
                    break
                items, cursor = self.query_prefix(user_id, "", cursor=cursor)
            logger.info("event=user_data_cleared user_id=%s", user_id)
        except (BotoCoreError, ClientError) as exc:
            self._raise_storage_error("clear_user", exc)

    def put(self, item: dict[str, Any], *, must_not_exist: bool = False) -> dict[str, Any]:
        normalized = _to_decimal(copy.deepcopy(item))
        try:
            if self.uses_memory:
                key = (str(item["PK"]), str(item["SK"]))
                with self._lock:
                    if must_not_exist and key in self._memory:
                        raise AppException(
                            ResponseCode.CONFLICT,
                            Message.RESOURCE_ALREADY_EXISTS,
                            error_code=ErrorCode.FIN_RECEIPT_DUPLICATE,
                        )
                    self._memory[key] = normalized
            else:
                kwargs: dict[str, Any] = {"Item": normalized}
                if must_not_exist:
                    kwargs["ConditionExpression"] = "attribute_not_exists(PK) AND attribute_not_exists(SK)"
                self._dynamo_table().put_item(**kwargs)
            logger.info("event=item_put entity=%s sk=%s", item.get("entity_type"), item.get("SK"))
            return _from_decimal(normalized)
        except AppException:
            raise
        except (BotoCoreError, ClientError) as exc:
            if isinstance(exc, ClientError) and exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise AppException(
                    ResponseCode.CONFLICT,
                    Message.RESOURCE_ALREADY_EXISTS,
                    error_code=ErrorCode.FIN_RECEIPT_DUPLICATE,
                ) from exc
            self._raise_storage_error("put", exc)

    def put_many(self, items: list[dict[str, Any]]) -> None:
        try:
            if self.uses_memory:
                with self._lock:
                    for item in items:
                        self._memory[(item["PK"], item["SK"])] = _to_decimal(copy.deepcopy(item))
            else:
                with self._dynamo_table().batch_writer() as batch:
                    for item in items:
                        batch.put_item(Item=_to_decimal(item))
            logger.info("event=batch_put count=%s", len(items))
        except (BotoCoreError, ClientError) as exc:
            self._raise_storage_error("put_many", exc)

    def put_with_audit(self, item: dict[str, Any], audit: dict[str, Any]) -> None:
        try:
            if self.uses_memory:
                with self._lock:
                    self._memory[(item["PK"], item["SK"])] = _to_decimal(copy.deepcopy(item))
                    self._memory[(audit["PK"], audit["SK"])] = _to_decimal(copy.deepcopy(audit))
                return
            table = self._dynamo_table()
            serializer = TypeSerializer()
            serialized_item = {key: serializer.serialize(value) for key, value in _to_decimal(item).items()}
            serialized_audit = {key: serializer.serialize(value) for key, value in _to_decimal(audit).items()}
            self._client.transact_write_items(
                TransactItems=[
                    {"Put": {"TableName": table.name, "Item": serialized_item}},
                    {
                        "Put": {
                            "TableName": table.name,
                            "Item": serialized_audit,
                            "ConditionExpression": "attribute_not_exists(PK) AND attribute_not_exists(SK)",
                        }
                    },
                ]
            )
        except (BotoCoreError, ClientError) as exc:
            self._raise_storage_error("put_with_audit", exc)

    def get(self, user_id: str, sk: str) -> dict[str, Any] | None:
        pk = f"USER#{user_id}"
        try:
            if self.uses_memory:
                with self._lock:
                    item = copy.deepcopy(self._memory.get((pk, sk)))
            else:
                item = self._dynamo_table().get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True).get("Item")
            logger.info("event=item_get user_id=%s sk=%s found=%s", user_id, sk, bool(item))
            return _from_decimal(item) if item else None
        except (BotoCoreError, ClientError) as exc:
            self._raise_storage_error("get", exc)

    def query_prefix(
        self,
        user_id: str,
        prefix: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        pk = f"USER#{user_id}"
        try:
            if self.uses_memory:
                with self._lock:
                    values = [
                        copy.deepcopy(item)
                        for (item_pk, sk), item in self._memory.items()
                        if item_pk == pk and sk.startswith(prefix)
                    ]
                values.sort(key=lambda value: value["SK"])
                offset = int(base64.urlsafe_b64decode(cursor.encode()).decode()) if cursor else 0
                page = values[offset : offset + limit]
                next_cursor = None
                if offset + limit < len(values):
                    next_cursor = base64.urlsafe_b64encode(str(offset + limit).encode()).decode()
                logger.info("event=prefix_query user_id=%s prefix=%s count=%s", user_id, prefix, len(page))
                return [_from_decimal(item) for item in page], next_cursor
            key_expression = Key("PK").eq(pk)
            if prefix:
                key_expression = key_expression & Key("SK").begins_with(prefix)
            kwargs: dict[str, Any] = {"KeyConditionExpression": key_expression, "Limit": limit}
            if cursor:
                kwargs["ExclusiveStartKey"] = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
            response = self._dynamo_table().query(**kwargs)
            next_key = response.get("LastEvaluatedKey")
            next_cursor = (
                base64.urlsafe_b64encode(json.dumps(next_key).encode()).decode() if next_key else None
            )
            result = [_from_decimal(item) for item in response.get("Items", [])]
            logger.info("event=prefix_query user_id=%s prefix=%s count=%s", user_id, prefix, len(result))
            return result, next_cursor
        except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError) as exc:
            self._raise_storage_error("query_prefix", exc)

    def query_timeline(
        self,
        user_id: str,
        entity: str,
        start: str,
        end: str,
        *,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        gsi_pk = f"USER#{user_id}#{entity}"
        try:
            if self.uses_memory:
                with self._lock:
                    values = [
                        copy.deepcopy(item)
                        for item in self._memory.values()
                        if item.get("GSI1PK") == gsi_pk and start <= item.get("GSI1SK", "") <= f"{end}~"
                    ]
                values.sort(key=lambda value: value.get("GSI1SK", ""), reverse=True)
                offset = int(base64.urlsafe_b64decode(cursor.encode()).decode()) if cursor else 0
                page = values[offset : offset + limit]
                next_cursor = None
                if offset + limit < len(values):
                    next_cursor = base64.urlsafe_b64encode(str(offset + limit).encode()).decode()
                logger.info("event=timeline_query user_id=%s entity=%s count=%s", user_id, entity, len(page))
                return [_from_decimal(item) for item in page], next_cursor
            kwargs: dict[str, Any] = {
                "IndexName": "GSI1",
                "KeyConditionExpression": Key("GSI1PK").eq(gsi_pk) & Key("GSI1SK").between(start, f"{end}~"),
                "Limit": limit,
                "ScanIndexForward": False,
            }
            if cursor:
                kwargs["ExclusiveStartKey"] = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
            response = self._dynamo_table().query(**kwargs)
            next_key = response.get("LastEvaluatedKey")
            next_cursor = (
                base64.urlsafe_b64encode(json.dumps(next_key).encode()).decode() if next_key else None
            )
            result = [_from_decimal(item) for item in response.get("Items", [])]
            logger.info("event=timeline_query user_id=%s entity=%s count=%s", user_id, entity, len(result))
            return result, next_cursor
        except (BotoCoreError, ClientError, ValueError, json.JSONDecodeError) as exc:
            self._raise_storage_error("query_timeline", exc)

    def find_receipt_hash(self, user_id: str, digest: str) -> dict[str, Any] | None:
        receipts, cursor = self.query_prefix(user_id, "RECEIPT#", limit=100)
        while True:
            match = next((item for item in receipts if item.get("sha256") == digest), None)
            if match or not cursor:
                return match
            receipts, cursor = self.query_prefix(user_id, "RECEIPT#", limit=100, cursor=cursor)

    def _raise_storage_error(self, operation: str, exc: Exception) -> None:
        logger.exception("event=dynamodb_failure operation=%s", operation)
        raise AppException(
            ResponseCode.SERVICE_UNAVAILABLE,
            Message.DYNAMODB_ERROR,
            details={"operation": operation},
            error_code=ErrorCode.AWS_DYNAMODB_ERROR,
        ) from exc


class ReceiptObjectRepository:
    def __init__(self) -> None:
        self._memory: dict[str, bytes] = {}
        self._client = None

    def _s3(self):
        if self._client is None:
            self._client = boto3.client("s3", region_name=settings.AWS_REGION)
        return self._client

    def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            if settings.USE_IN_MEMORY_REPOSITORY:
                self._memory[key] = data
            else:
                self._s3().put_object(
                    Bucket=settings.RECEIPTS_BUCKET_NAME,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                    ServerSideEncryption="AES256",
                )
            logger.info("event=receipt_object_put key=%s bytes=%s", key, len(data))
        except (BotoCoreError, ClientError) as exc:
            logger.exception("event=s3_put_failure key=%s", key)
            raise AppException(
                ResponseCode.SERVICE_UNAVAILABLE,
                Message.S3_ERROR,
                error_code=ErrorCode.AWS_S3_ERROR,
            ) from exc


finance_repository = FinanceRepository()
receipt_object_repository = ReceiptObjectRepository()
