from fastapi import APIRouter, Depends, Request

from ai.agents.finance_agent import FinanceAgent, finance_agent
from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.core.security import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.finance import ChatRequest
from app.schemas.general_response import SuccessResponse
from app.services.finance_service import FinanceService, finance_service

router = APIRouter()


@router.post("/chat", response_model=SuccessResponse[dict])
def chat(payload: ChatRequest, request: Request, user: AuthenticatedUser = Depends(get_current_user), agent: FinanceAgent = Depends(lambda: finance_agent)):
    try:
        return SuccessResponse(code="FIN_CHAT_COMPLETED", message=Message.CHAT_COMPLETED, result=agent.run(user.user_id, payload.message, payload.conversation_id), request_id=getattr(request.state, "request_id", "-"))
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR) from exc


@router.get("/conversations/{conversation_id}", response_model=SuccessResponse[dict])
def conversation(conversation_id: str, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return SuccessResponse(code="FIN_CONVERSATION_RETRIEVED", message=Message.CONVERSATION_RETRIEVED, result=service.conversation(user.user_id, conversation_id), request_id=getattr(request.state, "request_id", "-"))
    except AppException:
        raise
    except Exception as exc:
        raise AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR) from exc
