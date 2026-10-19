from fastapi import APIRouter, Depends, Request

from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.core.security import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.general_response import SuccessResponse

router = APIRouter()


@router.get("/me", response_model=SuccessResponse[AuthenticatedUser])
def current_user(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
) -> SuccessResponse[AuthenticatedUser]:
    try:
        return SuccessResponse(
            code="AUTH_USER_RETRIEVED",
            message=Message.AUTH_USER_RETRIEVED,
            result=user,
            request_id=getattr(request.state, "request_id", "-"),
        )
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            ResponseCode.INTERNAL_SERVER_ERROR,
            Message.INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
        ) from exc
