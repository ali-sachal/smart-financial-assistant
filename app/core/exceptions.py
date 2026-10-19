import time
import uuid
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas.general_response import ErrorResponse
from app.utils.logging import get_module_logger

logger = get_module_logger("errors")


class ResponseCode:
    SUCCESS = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    CONFLICT = status.HTTP_409_CONFLICT
    PAYLOAD_TOO_LARGE = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    UNSUPPORTED_MEDIA_TYPE = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE


class ErrorCode(StrEnum):
    SUCCESS = "SUCCESS"
    AUTH_TOKEN_MISSING = "AUTH_TOKEN_MISSING"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_ISSUER_INVALID = "AUTH_ISSUER_INVALID"
    AUTH_CLIENT_INVALID = "AUTH_CLIENT_INVALID"
    AUTH_TOKEN_TYPE_INVALID = "AUTH_TOKEN_TYPE_INVALID"
    AUTH_JWKS_UNAVAILABLE = "AUTH_JWKS_UNAVAILABLE"
    AUTH_USER_NOT_FOUND = "AUTH_USER_NOT_FOUND"
    FIN_PROFILE_NOT_FOUND = "FIN_PROFILE_NOT_FOUND"
    FIN_TRANSACTION_NOT_FOUND = "FIN_TRANSACTION_NOT_FOUND"
    FIN_BILL_NOT_FOUND = "FIN_BILL_NOT_FOUND"
    FIN_BUDGET_NOT_FOUND = "FIN_BUDGET_NOT_FOUND"
    FIN_RECEIPT_NOT_FOUND = "FIN_RECEIPT_NOT_FOUND"
    FIN_RECEIPT_INVALID = "FIN_RECEIPT_INVALID"
    FIN_RECEIPT_TOO_LARGE = "FIN_RECEIPT_TOO_LARGE"
    FIN_RECEIPT_DUPLICATE = "FIN_RECEIPT_DUPLICATE"
    FIN_FORECAST_INVALID = "FIN_FORECAST_INVALID"
    FIN_UNSAFE_ACTION = "FIN_UNSAFE_ACTION"
    FIN_TOOL_INVALID = "FIN_TOOL_INVALID"
    AWS_DYNAMODB_ERROR = "AWS_DYNAMODB_ERROR"
    AWS_S3_ERROR = "AWS_S3_ERROR"
    AI_GEMINI_UNAVAILABLE = "AI_GEMINI_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Message:
    SUCCESS = "Operation successful."
    APP_READY = "Smart Personal Finance Assistant is ready."
    INTERNAL_SERVER_ERROR = "An internal server error occurred."
    SERVICE_UNAVAILABLE = "The service is temporarily unavailable."
    INVALID_INPUT = "The provided input data is invalid."
    UNAUTHORIZED_ACCESS = "You are not authorized to access this resource."
    RESOURCE_NOT_FOUND = "The requested resource was not found."
    RESOURCE_ALREADY_EXISTS = "The resource already exists."
    AUTH_TOKEN_MISSING = "Authentication token is required."
    AUTH_TOKEN_EXPIRED = "The authentication token has expired."
    AUTH_TOKEN_INVALID = "The authentication token is invalid."
    AUTH_ISSUER_INVALID = "The authentication token issuer is invalid."
    AUTH_CLIENT_INVALID = "The authentication token client is invalid."
    AUTH_TOKEN_TYPE_INVALID = "An access token is required."
    AUTH_JWKS_UNAVAILABLE = "Authentication keys are temporarily unavailable."
    AUTH_USER_RETRIEVED = "Authenticated user retrieved successfully."
    PROFILE_RETRIEVED = "Profile retrieved successfully."
    PROFILE_UPDATED = "Profile updated successfully."
    PROFILE_NOT_FOUND = "Financial profile was not found."
    DEMO_SEEDED = "Demo financial data seeded successfully."
    ACCOUNTS_RETRIEVED = "Accounts retrieved successfully."
    TRANSACTIONS_RETRIEVED = "Transactions retrieved successfully."
    TRANSACTION_CREATED = "Transaction created successfully."
    TRANSACTION_UPDATED = "Transaction updated successfully."
    TRANSACTION_NOT_FOUND = "Transaction was not found."
    BUDGET_RETRIEVED = "Budget retrieved successfully."
    BUDGET_UPDATED = "Budget updated successfully."
    BILLS_RETRIEVED = "Bills retrieved successfully."
    BILL_CREATED = "Bill created successfully."
    BILL_UPDATED = "Bill updated successfully."
    BILL_NOT_FOUND = "Bill was not found."
    DASHBOARD_RETRIEVED = "Dashboard retrieved successfully."
    FORECAST_RETRIEVED = "Cash-flow forecast generated successfully."
    RECEIPT_SCANNED = "Receipt processed successfully."
    RECEIPT_RETRIEVED = "Receipt retrieved successfully."
    RECEIPT_UPDATED = "Receipt updated successfully."
    RECEIPT_NOT_FOUND = "Receipt was not found."
    RECEIPT_INVALID = "Receipt file is invalid or unsupported."
    RECEIPT_TOO_LARGE = "Receipt file exceeds the maximum allowed size."
    CHAT_COMPLETED = "Assistant response generated successfully."
    CONVERSATION_RETRIEVED = "Conversation retrieved successfully."
    DYNAMODB_ERROR = "Financial data storage is temporarily unavailable."
    S3_ERROR = "Receipt storage is temporarily unavailable."
    GEMINI_UNAVAILABLE = "The AI assistant is temporarily unavailable."


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: dict[str, Any] | None = None,
        error_code: ErrorCode | str = ErrorCode.INTERNAL_ERROR,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        self.error_code = str(error_code)
        super().__init__(message)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())


def _headers(request: Request) -> dict[str, str]:
    headers = {"X-Request-ID": _request_id(request)}
    started = getattr(request.state, "start_time", None)
    if started is not None:
        headers["X-Response-Time"] = f"{int((time.perf_counter() - started) * 1000)}ms"
    return headers


def _error_response(request: Request, status_code: int, code: str, message: str, errors: Any = None) -> JSONResponse:
    response = ErrorResponse(code=code, message=message, errors=errors, request_id=_request_id(request))
    return JSONResponse(status_code=status_code, content=jsonable_encoder(response), headers=_headers(request))


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.error("event=app_exception status=%s code=%s details=%s", exc.status_code, exc.error_code, exc.details)
    return _error_response(request, exc.status_code, exc.error_code, exc.message, exc.details or None)


async def validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError) -> JSONResponse:
    errors = [
        {
            "field": ".".join(str(part) for part in error.get("loc", [])),
            "message": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    logger.warning("event=validation_error count=%s", len(errors))
    return _error_response(request, ResponseCode.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", Message.INVALID_INPUT, errors)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return _error_response(request, exc.status_code, "HTTP_ERROR", str(exc.detail))


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("event=unexpected_exception type=%s", type(exc).__name__)
    return _error_response(request, ResponseCode.INTERNAL_SERVER_ERROR, ErrorCode.INTERNAL_ERROR, Message.INTERNAL_SERVER_ERROR)


def register_exception_handlers(app) -> None:
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
