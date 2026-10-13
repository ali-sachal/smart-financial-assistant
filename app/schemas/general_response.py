from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    code: str
    message: Optional[str] = None
    errors: Optional[Any] = None
    result: Optional[T] = None
    request_id: Optional[str] = None

class SuccessResponse(ApiResponse[T]):
    success: bool = True
    code: str = "SUCCESS"
    message: Optional[str] = None
    errors: Optional[Any] = None
    result: Optional[T] = None

class ErrorResponse(ApiResponse[None]):
    success: bool = False
    code: str = "INTERNAL_ERROR"
    message: str
    errors: Optional[Any] = None
    result: Optional[None] = None
