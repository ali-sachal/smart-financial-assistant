from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.core.security import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.finance import ReceiptUpdate
from app.schemas.general_response import SuccessResponse
from app.services.receipt_service import ReceiptService, receipt_service

router = APIRouter()


@router.post("/scan", response_model=SuccessResponse[dict], status_code=201)
async def scan_receipt(request: Request, file: UploadFile = File(...), user: AuthenticatedUser = Depends(get_current_user), service: ReceiptService = Depends(lambda: receipt_service)):
    try:
        result = await service.scan(user.user_id, file)
        return SuccessResponse(code="FIN_RECEIPT_SCANNED", message=Message.RECEIPT_SCANNED, result=result, request_id=getattr(request.state, "request_id", "-"))
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR) from exc


@router.get("/{receipt_id}", response_model=SuccessResponse[dict])
def get_receipt(receipt_id: str, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: ReceiptService = Depends(lambda: receipt_service)):
    try:
        return SuccessResponse(code="FIN_RECEIPT_RETRIEVED", message=Message.RECEIPT_RETRIEVED, result=service.get(user.user_id, receipt_id), request_id=getattr(request.state, "request_id", "-"))
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR) from exc


@router.patch("/{receipt_id}", response_model=SuccessResponse[dict])
def update_receipt(receipt_id: str, payload: ReceiptUpdate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: ReceiptService = Depends(lambda: receipt_service)):
    try:
        return SuccessResponse(code="FIN_RECEIPT_UPDATED", message=Message.RECEIPT_UPDATED, result=service.update(user.user_id, receipt_id, payload), request_id=getattr(request.state, "request_id", "-"))
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR) from exc
