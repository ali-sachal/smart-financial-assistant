from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.exceptions import AppException, ResponseCode
from app.core.security import create_local_token
from app.schemas.general_response import SuccessResponse

router = APIRouter()


class DevelopmentTokenRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    role: str | None = None


@router.post("/dev-token", response_model=SuccessResponse[dict])
def development_token(payload: DevelopmentTokenRequest):
    if settings.ENVIRONMENT.lower() in {"prod", "production"} or settings.AUTH_MODE != "local":
        raise AppException(ResponseCode.NOT_FOUND, "Development token endpoint is not available")
    extra = {"role": payload.role} if payload.role else None
    return SuccessResponse(
        message="Development token created",
        result={"access_token": create_local_token(payload.user_id, extra=extra), "token_type": "bearer"},
    )
