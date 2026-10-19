from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.schemas.finance import (
    BillCreate,
    BillUpdate,
    BudgetStatusArgs,
    CategorizeTransactionArgs,
    FetchBalanceArgs,
    ForecastArgs,
    ListBillsArgs,
    ListTransactionsArgs,
    ReceiptResultArgs,
    SpendingSummaryArgs,
    TransactionUpdate,
    UpsertBillArgs,
    UpsertBudgetArgs,
    BudgetUpsert,
)
from app.services.finance_service import FinanceService, finance_service
from app.services.receipt_service import ReceiptService, receipt_service
from app.utils.logging import get_module_logger

logger = get_module_logger("agent")


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    schema: type[BaseModel]
    handler: Callable[[str, BaseModel], Any]

    def declaration(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema.model_json_schema(),
        }


class FinanceToolRegistry:
    def __init__(self, finances: FinanceService = finance_service, receipts: ReceiptService = receipt_service) -> None:
        self.finances = finances
        self.receipts = receipts
        self.tools = {
            item.name: item
            for item in [
                ToolDefinition("fetch_balance", "Return the authenticated user's account balances.", FetchBalanceArgs, self._fetch_balance),
                ToolDefinition("list_transactions", "List recent transactions with optional category filtering.", ListTransactionsArgs, self._list_transactions),
                ToolDefinition("get_spending_summary", "Return income and spending totals for a month.", SpendingSummaryArgs, self._spending_summary),
                ToolDefinition("get_budget_status", "Return budget utilization for a month and optional category.", BudgetStatusArgs, self._budget_status),
                ToolDefinition("upsert_budget", "Create or update a reversible monthly category budget.", UpsertBudgetArgs, self._upsert_budget),
                ToolDefinition("list_bills", "List upcoming scheduled bills and income.", ListBillsArgs, self._list_bills),
                ToolDefinition("upsert_bill", "Create an upcoming bill. Never initiates a payment.", UpsertBillArgs, self._upsert_bill),
                ToolDefinition("categorize_transaction", "Correct the category of one transaction.", CategorizeTransactionArgs, self._categorize_transaction),
                ToolDefinition("get_cashflow_forecast", "Return the deterministic cash-flow forecast.", ForecastArgs, self._forecast),
                ToolDefinition("get_receipt_result", "Return stored structured receipt extraction.", ReceiptResultArgs, self._receipt),
            ]
        }

    def declarations(self) -> list[dict[str, Any]]:
        return [tool.declaration() for tool in self.tools.values()]

    def execute(self, user_id: str, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.tools.get(name)
        if not tool:
            raise AppException(ResponseCode.BAD_REQUEST, Message.INVALID_INPUT, details={"tool": name}, error_code=ErrorCode.FIN_TOOL_INVALID)
        if "user_id" in arguments:
            raise AppException(ResponseCode.FORBIDDEN, Message.UNAUTHORIZED_ACCESS, error_code=ErrorCode.FIN_UNSAFE_ACTION)
        try:
            payload = tool.schema.model_validate(arguments)
        except ValidationError as exc:
            raise AppException(
                ResponseCode.UNPROCESSABLE_ENTITY,
                Message.INVALID_INPUT,
                details={"tool": name, "errors": exc.errors(include_url=False)},
                error_code=ErrorCode.FIN_TOOL_INVALID,
            ) from exc
        logger.info("event=agent_tool_execute user_id=%s tool=%s", user_id, name)
        return tool.handler(user_id, payload)

    def _fetch_balance(self, user_id: str, _: FetchBalanceArgs) -> Any:
        return self.finances.current_balance(user_id)

    def _list_transactions(self, user_id: str, payload: ListTransactionsArgs) -> Any:
        today = date.today()
        return self.finances.list_transactions(user_id, today - timedelta(days=payload.days), today, category=payload.category)

    def _spending_summary(self, user_id: str, payload: SpendingSummaryArgs) -> Any:
        return self.finances.spending_summary(user_id, payload.month or date.today().strftime("%Y-%m"))

    def _budget_status(self, user_id: str, payload: BudgetStatusArgs) -> Any:
        return self.finances.budget_status(user_id, payload.month or date.today().strftime("%Y-%m"), payload.category)

    def _upsert_budget(self, user_id: str, payload: UpsertBudgetArgs) -> Any:
        return self.finances.upsert_budget(
            user_id, payload.month, payload.category,
            BudgetUpsert(limit_minor=payload.limit_minor), actor="agent",
        )

    def _list_bills(self, user_id: str, payload: ListBillsArgs) -> Any:
        today = date.today()
        return self.finances.list_bills(user_id, today, today + timedelta(days=payload.days))

    def _upsert_bill(self, user_id: str, payload: UpsertBillArgs) -> Any:
        values = payload.model_dump(exclude={"bill_id"})
        if payload.bill_id:
            return self.finances.update_bill(user_id, payload.bill_id, BillUpdate(**values), actor="agent")
        return self.finances.create_bill(user_id, BillCreate(**values), actor="agent")

    def _categorize_transaction(self, user_id: str, payload: CategorizeTransactionArgs) -> Any:
        return self.finances.update_transaction(
            user_id, payload.transaction_id, TransactionUpdate(category=payload.category), actor="agent"
        )

    def _forecast(self, user_id: str, payload: ForecastArgs) -> Any:
        return self.finances.forecast(user_id, payload.days)

    def _receipt(self, user_id: str, payload: ReceiptResultArgs) -> Any:
        return self.receipts.get(user_id, payload.receipt_id)


finance_tool_registry = FinanceToolRegistry()
