from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request

from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.core.security import get_current_user
from app.schemas.auth import AuthenticatedUser
from app.schemas.finance import BillCreate, BillUpdate, BudgetUpsert, ProfileUpdate, TransactionCreate, TransactionUpdate
from app.schemas.general_response import SuccessResponse
from app.services.finance_service import FinanceService, finance_service

router = APIRouter()


def _response(request: Request, code: str, message: str, result):
    return SuccessResponse(code=code, message=message, result=result, request_id=getattr(request.state, "request_id", "-"))


def _unexpected(exc: Exception) -> AppException:
    return AppException(ResponseCode.INTERNAL_SERVER_ERROR, Message.INTERNAL_SERVER_ERROR, error_code=ErrorCode.INTERNAL_ERROR)


@router.get("/profile", response_model=SuccessResponse[dict])
def get_profile(request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_PROFILE_RETRIEVED", Message.PROFILE_RETRIEVED, service.get_profile(user.user_id))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.put("/profile", response_model=SuccessResponse[dict])
def put_profile(payload: ProfileUpdate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_PROFILE_UPDATED", Message.PROFILE_UPDATED, service.upsert_profile(user.user_id, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.post("/demo/seed", response_model=SuccessResponse[dict])
def seed_demo(request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_DEMO_SEEDED", Message.DEMO_SEEDED, service.seed_demo(user.user_id))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/accounts", response_model=SuccessResponse[list[dict]])
def accounts(request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_ACCOUNTS_RETRIEVED", Message.ACCOUNTS_RETRIEVED, service.list_accounts(user.user_id))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/transactions", response_model=SuccessResponse[dict])
def transactions(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    transaction_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    cursor: str | None = None,
    user: AuthenticatedUser = Depends(get_current_user),
    service: FinanceService = Depends(lambda: finance_service),
):
    try:
        end = end_date or date.today()
        start = start_date or end - timedelta(days=60)
        result = service.list_transactions(user.user_id, start, end, category, transaction_type, limit, cursor)
        return _response(request, "FIN_TRANSACTIONS_RETRIEVED", Message.TRANSACTIONS_RETRIEVED, result)
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.post("/transactions", response_model=SuccessResponse[dict], status_code=201)
def create_transaction(payload: TransactionCreate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_TRANSACTION_CREATED", Message.TRANSACTION_CREATED, service.create_transaction(user.user_id, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.patch("/transactions/{transaction_id}", response_model=SuccessResponse[dict])
def update_transaction(transaction_id: str, payload: TransactionUpdate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_TRANSACTION_UPDATED", Message.TRANSACTION_UPDATED, service.update_transaction(user.user_id, transaction_id, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/budgets/{month}/{category}", response_model=SuccessResponse[dict])
def budget(month: str, category: str, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_BUDGET_RETRIEVED", Message.BUDGET_RETRIEVED, service.budget_status(user.user_id, month, category))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.put("/budgets/{month}/{category}", response_model=SuccessResponse[dict])
def put_budget(month: str, category: str, payload: BudgetUpsert, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_BUDGET_UPDATED", Message.BUDGET_UPDATED, service.upsert_budget(user.user_id, month, category, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/bills", response_model=SuccessResponse[list[dict]])
def bills(request: Request, days: int = Query(default=30, ge=1, le=365), user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        today = date.today()
        return _response(request, "FIN_BILLS_RETRIEVED", Message.BILLS_RETRIEVED, service.list_bills(user.user_id, today, today + timedelta(days=days)))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.post("/bills", response_model=SuccessResponse[dict], status_code=201)
def create_bill(payload: BillCreate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_BILL_CREATED", Message.BILL_CREATED, service.create_bill(user.user_id, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.patch("/bills/{bill_id}", response_model=SuccessResponse[dict])
def update_bill(bill_id: str, payload: BillUpdate, request: Request, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_BILL_UPDATED", Message.BILL_UPDATED, service.update_bill(user.user_id, bill_id, payload))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/dashboard", response_model=SuccessResponse[dict])
def dashboard(request: Request, month: str | None = None, user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        selected = month or date.today().strftime("%Y-%m")
        return _response(request, "FIN_DASHBOARD_RETRIEVED", Message.DASHBOARD_RETRIEVED, service.dashboard(user.user_id, selected))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc


@router.get("/forecast", response_model=SuccessResponse[dict])
def forecast(request: Request, days: int = Query(default=30, ge=1, le=90), user: AuthenticatedUser = Depends(get_current_user), service: FinanceService = Depends(lambda: finance_service)):
    try:
        return _response(request, "FIN_FORECAST_RETRIEVED", Message.FORECAST_RETRIEVED, service.forecast(user.user_id, days))
    except AppException:
        raise
    except Exception as exc:
        raise _unexpected(exc) from exc
