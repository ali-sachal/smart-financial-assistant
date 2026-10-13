from pydantic import BaseModel
from typing import Optional, Generic, TypeVar, Any

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    errors: Optional[Any] = None
    result: Optional[T] = None

class SuccessResponse(ApiResponse[T]):
    success: bool = True
    message: Optional[str] = None
    errors: Optional[Any] = None
    result: Optional[T] = None

class ErrorResponse(ApiResponse[None]):
    success: bool = False
    message: str
    errors: Optional[Any] = None
    result: Optional[None] = None
