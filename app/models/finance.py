from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class EntityType(StrEnum):
    PROFILE = "PROFILE"
    ACCOUNT = "ACCOUNT"
    TRANSACTION = "TXN"
    BUDGET = "BUDGET"
    BILL = "BILL"
    RECEIPT = "RECEIPT"
    CONVERSATION = "CONV"
    MESSAGE = "MSG"
    AUDIT = "AUDIT"


@dataclass
class FinanceEntity:
    PK: str
    SK: str
    entity_type: str
    created_at: str
    updated_at: str
    version: int = 1

    def to_item(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProfileEntity(FinanceEntity):
    currency: str = "USD"
    timezone: str = "UTC"
    monthly_income_minor: int = 0
    opening_balance_minor: int = 0
    safety_buffer_minor: int = 0


@dataclass
class AccountEntity(FinanceEntity):
    account_id: str = ""
    name: str = ""
    account_type: str = "checking"
    balance_minor: int = 0
    currency: str = "USD"


@dataclass
class TransactionEntity(FinanceEntity):
    transaction_id: str = ""
    account_id: str = ""
    amount_minor: int = 0
    currency: str = "USD"
    transaction_type: str = "expense"
    category: str = "other"
    merchant: str = ""
    posted_at: str = ""
    source: str = "manual"
    notes: str | None = None
    receipt_id: str | None = None
    GSI1PK: str = ""
    GSI1SK: str = ""


@dataclass
class BudgetEntity(FinanceEntity):
    month: str = ""
    category: str = ""
    limit_minor: int = 0
    currency: str = "USD"


@dataclass
class BillEntity(FinanceEntity):
    bill_id: str = ""
    name: str = ""
    amount_minor: int = 0
    currency: str = "USD"
    category: str = "other"
    kind: str = "expense"
    next_due_date: str = ""
    frequency: str = "monthly"
    active: bool = True
    GSI1PK: str = ""
    GSI1SK: str = ""


@dataclass
class ReceiptEntity(FinanceEntity):
    receipt_id: str = ""
    s3_key: str = ""
    content_type: str = ""
    sha256: str = ""
    status: str = "needs_review"
    extraction: dict[str, Any] = field(default_factory=dict)
    transaction_id: str | None = None


@dataclass
class ConversationEntity(FinanceEntity):
    conversation_id: str = ""
    title: str = "Financial conversation"


@dataclass
class MessageEntity(FinanceEntity):
    conversation_id: str = ""
    message_id: str = ""
    role: str = "user"
    content: str = ""
    tool_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEntity(FinanceEntity):
    audit_id: str = ""
    action: str = ""
    actor: str = "user"
    target_type: str = ""
    target_id: str = ""
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
