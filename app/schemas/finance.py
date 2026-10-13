from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


CurrencyCode = str
TransactionType = Literal["income", "expense", "transfer", "refund"]
BillKind = Literal["expense", "income"]
Frequency = Literal["once", "weekly", "monthly"]


class ProfileUpdate(BaseModel):
    currency: CurrencyCode = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    monthly_income_minor: int = Field(default=0, ge=0)
    opening_balance_minor: int = 0
    safety_buffer_minor: int = Field(default=0, ge=0)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class TransactionCreate(BaseModel):
    account_id: str = Field(default="checking", min_length=1, max_length=64)
    amount_minor: int = Field(gt=0)
    currency: CurrencyCode = Field(default="USD", min_length=3, max_length=3)
    transaction_type: TransactionType
    category: str = Field(min_length=1, max_length=64)
    merchant: str = Field(min_length=1, max_length=160)
    posted_at: date
    source: Literal["manual", "seed", "receipt", "agent"] = "manual"
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class TransactionUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=64)
    merchant: str | None = Field(default=None, min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=500)


class BudgetUpsert(BaseModel):
    limit_minor: int = Field(ge=0)
    currency: CurrencyCode = Field(default="USD", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class BillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount_minor: int = Field(gt=0)
    currency: CurrencyCode = Field(default="USD", min_length=3, max_length=3)
    category: str = Field(min_length=1, max_length=64)
    kind: BillKind = "expense"
    next_due_date: date
    frequency: Frequency = "monthly"
    active: bool = True

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class BillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    amount_minor: int | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    next_due_date: date | None = None
    frequency: Frequency | None = None
    active: bool | None = None


class ReceiptLineItem(BaseModel):
    description: str
    quantity: float = 1
    amount_minor: int


class ReceiptExtraction(BaseModel):
    merchant: str | None = None
    transaction_date: date | None = None
    subtotal_minor: int | None = None
    tax_minor: int | None = None
    total_minor: int | None = None
    currency: str = "USD"
    category: str = "other"
    line_items: list[ReceiptLineItem] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)


class ReceiptUpdate(BaseModel):
    merchant: str | None = Field(default=None, min_length=1, max_length=160)
    transaction_date: date | None = None
    total_minor: int | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category: str | None = Field(default=None, min_length=1, max_length=64)
    confirm: bool = False


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=64)


class FetchBalanceArgs(BaseModel):
    pass


class ListTransactionsArgs(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    category: str | None = None


class SpendingSummaryArgs(BaseModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class BudgetStatusArgs(BaseModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    category: str | None = None


class UpsertBudgetArgs(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    category: str = Field(min_length=1, max_length=64)
    limit_minor: int = Field(ge=0)


class ListBillsArgs(BaseModel):
    days: int = Field(default=30, ge=1, le=365)


class UpsertBillArgs(BillCreate):
    bill_id: str | None = None


class CategorizeTransactionArgs(BaseModel):
    transaction_id: str
    category: str = Field(min_length=1, max_length=64)


class ForecastArgs(BaseModel):
    days: int = Field(default=30, ge=1, le=90)


class ReceiptResultArgs(BaseModel):
    receipt_id: str


class AgentStep(BaseModel):
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    final_text: str | None = None

