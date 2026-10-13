# app/api/endpoints/healthcheck.py
from fastapi import APIRouter, Request
import time
from app.schemas.general_response import SuccessResponse, ErrorResponse
from app.core.exceptions import Message, ResponseCode, AppException
from app.services.health_service import health_payload

# This should be defined here, as it's part of the health info
APP_START_TIME = time.time()

router = APIRouter()


@router.get("/check", response_model=SuccessResponse[dict] | ErrorResponse)
def health(request: Request):
    """
    Health check with dependency status and latency.
    Returns 200 if all systems OK, 503 otherwise.
    """
    try:
        request_id = getattr(request.state, "request_id", "-")
        payload, all_ok = health_payload(request_id, APP_START_TIME)
        
        if all_ok:
            return SuccessResponse(result=payload, message=Message.SUCCESS)
        
        raise AppException(ResponseCode.SERVICE_UNAVAILABLE, Message.SERVICE_UNAVAILABLE, details=payload)
    except AppException as e:
        raise e
    except Exception as e:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, details={"error": str(e)})
