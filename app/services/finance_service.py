import calendar
import math
import statistics
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.models.finance import (
    AccountEntity,
    AuditEntity,
    BillEntity,
    BudgetEntity,
    ConversationEntity,
    EntityType,
    MessageEntity,
    ProfileEntity,
    TransactionEntity,
)
from app.repositories.finance import FinanceRepository, finance_repository
from app.schemas.finance import (
    BillCreate,
    BillUpdate,
    BudgetUpsert,
    ProfileUpdate,
    TransactionCreate,
    TransactionUpdate,
)
from app.utils.logging import get_module_logger

logger = get_module_logger("services")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def user_pk(user_id: str) -> str:
    return f"USER#{user_id}"


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in item.items()
        if key not in {"PK", "SK", "GSI1PK", "GSI1SK"}
    }


class FinanceService:
    def __init__(self, repository: FinanceRepository = finance_repository) -> None:
        self.repository = repository

    def get_profile(self, user_id: str) -> dict[str, Any]:
        item = self.repository.get(user_id, "PROFILE")
        if not item:
            raise AppException(
                ResponseCode.NOT_FOUND,
                Message.PROFILE_NOT_FOUND,
                error_code=ErrorCode.FIN_PROFILE_NOT_FOUND,
            )
        return public_item(item)

    def upsert_profile(self, user_id: str, payload: ProfileUpdate) -> dict[str, Any]:
        now = utc_now()
        previous = self.repository.get(user_id, "PROFILE")
        entity = ProfileEntity(
            PK=user_pk(user_id),
            SK="PROFILE",
            entity_type=EntityType.PROFILE,
            created_at=previous.get("created_at", now) if previous else now,
            updated_at=now,
            version=int(previous.get("version", 0)) + 1 if previous else 1,
            **payload.model_dump(),
        )
        item = self.repository.put(entity.to_item())
        logger.info("event=profile_upserted user_id=%s", user_id)
        return public_item(item)

    def seed_demo(self, user_id: str) -> dict[str, Any]:
        self.repository.clear_user(user_id)
        today = date.today()
        now = utc_now()
        profile = ProfileEntity(
            PK=user_pk(user_id), SK="PROFILE", entity_type=EntityType.PROFILE,
            created_at=now, updated_at=now, currency="USD", timezone="UTC",
            monthly_income_minor=500_000, opening_balance_minor=240_000,
            safety_buffer_minor=75_000,
        )
        account = AccountEntity(
            PK=user_pk(user_id), SK="ACCOUNT#checking", entity_type=EntityType.ACCOUNT,
            created_at=now, updated_at=now, account_id="checking", name="Everyday Checking",
            account_type="checking", balance_minor=240_000, currency="USD",
        )
        expenses = [
            (2, "Fresh Market", 8_450, "groceries"),
            (5, "Metro Transit", 2_500, "transport"),
            (8, "Corner Cafe", 3_200, "dining"),
            (12, "Fresh Market", 11_275, "groceries"),
            (16, "StreamFlix", 1_599, "entertainment"),
            (21, "Fuel Station", 5_800, "transport"),
            (27, "Bistro 21", 7_400, "dining"),
            (34, "Fresh Market", 9_130, "groceries"),
            (41, "Pharmacy", 3_750, "health"),
            (49, "Corner Cafe", 2_850, "dining"),
            (56, "Home Store", 6_900, "shopping"),
        ]
        items: list[dict[str, Any]] = [profile.to_item(), account.to_item()]
        for days_ago, merchant, amount, category in expenses:
            transaction_id = str(uuid.uuid4())
            posted_at = (today - timedelta(days=days_ago)).isoformat()
            items.append(TransactionEntity(
                PK=user_pk(user_id), SK=f"TXN#{transaction_id}", entity_type=EntityType.TRANSACTION,
                created_at=now, updated_at=now, transaction_id=transaction_id,
                account_id="checking", amount_minor=amount, currency="USD",
                transaction_type="expense", category=category, merchant=merchant,
                posted_at=posted_at, source="seed", GSI1PK=f"USER#{user_id}#TXN",
                GSI1SK=f"{posted_at}#{transaction_id}",
            ).to_item())
        salary_id = str(uuid.uuid4())
        salary_date = today.replace(day=1).isoformat()
        items.append(TransactionEntity(
            PK=user_pk(user_id), SK=f"TXN#{salary_id}", entity_type=EntityType.TRANSACTION,
            created_at=now, updated_at=now, transaction_id=salary_id, account_id="checking",
            amount_minor=500_000, currency="USD", transaction_type="income", category="salary",
            merchant="Employer", posted_at=salary_date, source="seed",
            GSI1PK=f"USER#{user_id}#TXN", GSI1SK=f"{salary_date}#{salary_id}",
        ).to_item())
        for category, limit_minor in {"groceries": 60_000, "dining": 30_000, "transport": 35_000}.items():
            month = today.strftime("%Y-%m")
            items.append(BudgetEntity(
                PK=user_pk(user_id), SK=f"BUDGET#{month}#{category}", entity_type=EntityType.BUDGET,
                created_at=now, updated_at=now, month=month, category=category,
                limit_minor=limit_minor, currency="USD",
            ).to_item())
        bills = [
            ("Rent", 120_000, "housing", "expense", today + timedelta(days=5)),
            ("Utilities", 18_000, "utilities", "expense", today + timedelta(days=9)),
            ("Salary", 500_000, "salary", "income", today + timedelta(days=20)),
        ]
        for name, amount, category, kind, due in bills:
            bill_id = str(uuid.uuid4())
            due_text = due.isoformat()
            items.append(BillEntity(
                PK=user_pk(user_id), SK=f"BILL#{bill_id}", entity_type=EntityType.BILL,
                created_at=now, updated_at=now, bill_id=bill_id, name=name,
                amount_minor=amount, currency="USD", category=category, kind=kind,
                next_due_date=due_text, frequency="monthly", active=True,
                GSI1PK=f"USER#{user_id}#BILL", GSI1SK=f"{due_text}#{bill_id}",
            ).to_item())
        self.repository.put_many(items)
        logger.info("event=demo_seeded user_id=%s item_count=%s", user_id, len(items))
        return {"seeded": True, "item_count": len(items)}

    def list_accounts(self, user_id: str) -> list[dict[str, Any]]:
        items, _ = self.repository.query_prefix(user_id, "ACCOUNT#")
        return [public_item(item) for item in items]

    def current_balance(self, user_id: str) -> dict[str, Any]:
        accounts = self.list_accounts(user_id)
        return {
            "balance_minor": sum(int(account["balance_minor"]) for account in accounts),
            "currency": accounts[0]["currency"] if accounts else "USD",
            "accounts": accounts,
        }

    def list_transactions(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        category: str | None = None,
        transaction_type: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        items, next_cursor = self.repository.query_timeline(
            user_id, "TXN", start_date.isoformat(), end_date.isoformat(), limit=limit, cursor=cursor
        )
        if category:
            items = [item for item in items if item.get("category") == category]
        if transaction_type:
            items = [item for item in items if item.get("transaction_type") == transaction_type]
        return {"items": [public_item(item) for item in items], "next_cursor": next_cursor}

    def create_transaction(
        self,
        user_id: str,
        payload: TransactionCreate,
        *,
        receipt_id: str | None = None,
        actor: str = "user",
    ) -> dict[str, Any]:
        now = utc_now()
        transaction_id = str(uuid.uuid4())
        posted_at = payload.posted_at.isoformat()
        entity = TransactionEntity(
            PK=user_pk(user_id), SK=f"TXN#{transaction_id}", entity_type=EntityType.TRANSACTION,
            created_at=now, updated_at=now, transaction_id=transaction_id,
            receipt_id=receipt_id, GSI1PK=f"USER#{user_id}#TXN",
            GSI1SK=f"{posted_at}#{transaction_id}", **payload.model_dump(mode="json"),
        )
        item = entity.to_item()
        if actor == "agent":
            self.repository.put_with_audit(item, self._audit(user_id, "transaction.create", actor, "transaction", transaction_id, None, item))
        else:
            self.repository.put(item)
        self._adjust_account_balance(user_id, payload.account_id, payload.amount_minor, payload.transaction_type)
        logger.info("event=transaction_created user_id=%s transaction_id=%s actor=%s", user_id, transaction_id, actor)
        return public_item(item)

    def update_transaction(
        self,
        user_id: str,
        transaction_id: str,
        payload: TransactionUpdate,
        *,
        actor: str = "user",
    ) -> dict[str, Any]:
        existing = self.repository.get(user_id, f"TXN#{transaction_id}")
        if not existing:
            raise AppException(ResponseCode.NOT_FOUND, Message.TRANSACTION_NOT_FOUND, error_code=ErrorCode.FIN_TRANSACTION_NOT_FOUND)
        updated = {**existing, **payload.model_dump(exclude_none=True), "updated_at": utc_now(), "version": int(existing.get("version", 1)) + 1}
        if actor == "agent":
            self.repository.put_with_audit(updated, self._audit(user_id, "transaction.update", actor, "transaction", transaction_id, existing, updated))
        else:
            self.repository.put(updated)
        return public_item(updated)

    def upsert_budget(self, user_id: str, month: str, category: str, payload: BudgetUpsert, *, actor: str = "user") -> dict[str, Any]:
        sk = f"BUDGET#{month}#{category.lower()}"
        previous = self.repository.get(user_id, sk)
        now = utc_now()
        item = BudgetEntity(
            PK=user_pk(user_id), SK=sk, entity_type=EntityType.BUDGET,
            created_at=previous.get("created_at", now) if previous else now, updated_at=now,
            version=int(previous.get("version", 0)) + 1 if previous else 1,
            month=month, category=category.lower(), **payload.model_dump(),
        ).to_item()
        if actor == "agent":
            self.repository.put_with_audit(item, self._audit(user_id, "budget.upsert", actor, "budget", sk, previous, item))
        else:
            self.repository.put(item)
        return self.budget_status(user_id, month, category.lower())

    def budget_status(self, user_id: str, month: str, category: str | None = None) -> dict[str, Any]:
        budgets, _ = self.repository.query_prefix(user_id, f"BUDGET#{month}#")
        start = date.fromisoformat(f"{month}-01")
        end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
        transactions = self.list_transactions(user_id, start, end, transaction_type="expense", limit=500)["items"]
        spending: dict[str, int] = {}
        for transaction in transactions:
            spending[transaction["category"]] = spending.get(transaction["category"], 0) + int(transaction["amount_minor"])
        results = []
        for budget in budgets:
            budget_category = budget["category"]
            if category and category != budget_category:
                continue
            spent = spending.get(budget_category, 0)
            limit_minor = int(budget["limit_minor"])
            results.append({
                **public_item(budget),
                "spent_minor": spent,
                "remaining_minor": limit_minor - spent,
                "utilization": round(spent / limit_minor, 4) if limit_minor else 0.0,
            })
        return {"month": month, "items": results}

    def list_bills(self, user_id: str, start_date: date, end_date: date) -> list[dict[str, Any]]:
        items, _ = self.repository.query_timeline(user_id, "BILL", start_date.isoformat(), end_date.isoformat(), limit=500)
        return [public_item(item) for item in items if item.get("active", True)]

    def create_bill(self, user_id: str, payload: BillCreate, *, actor: str = "user") -> dict[str, Any]:
        now = utc_now()
        bill_id = str(uuid.uuid4())
        due = payload.next_due_date.isoformat()
        item = BillEntity(
            PK=user_pk(user_id), SK=f"BILL#{bill_id}", entity_type=EntityType.BILL,
            created_at=now, updated_at=now, bill_id=bill_id,
            GSI1PK=f"USER#{user_id}#BILL", GSI1SK=f"{due}#{bill_id}",
            **payload.model_dump(mode="json"),
        ).to_item()
        if actor == "agent":
            self.repository.put_with_audit(item, self._audit(user_id, "bill.create", actor, "bill", bill_id, None, item))
        else:
            self.repository.put(item)
        return public_item(item)

    def update_bill(self, user_id: str, bill_id: str, payload: BillUpdate, *, actor: str = "user") -> dict[str, Any]:
        existing = self.repository.get(user_id, f"BILL#{bill_id}")
        if not existing:
            raise AppException(ResponseCode.NOT_FOUND, Message.BILL_NOT_FOUND, error_code=ErrorCode.FIN_BILL_NOT_FOUND)
        values = payload.model_dump(exclude_none=True, mode="json")
        updated = {**existing, **values, "updated_at": utc_now(), "version": int(existing.get("version", 1)) + 1}
        updated["GSI1SK"] = f"{updated['next_due_date']}#{bill_id}"
        if actor == "agent":
            self.repository.put_with_audit(updated, self._audit(user_id, "bill.update", actor, "bill", bill_id, existing, updated))
        else:
            self.repository.put(updated)
        return public_item(updated)

    def spending_summary(self, user_id: str, month: str) -> dict[str, Any]:
        start = date.fromisoformat(f"{month}-01")
        end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
        transactions = self.list_transactions(user_id, start, end, limit=500)["items"]
        category_totals: dict[str, int] = {}
        merchant_totals: dict[str, int] = {}
        income = 0
        spending = 0
        for item in transactions:
            if item["transaction_type"] == "income":
                income += int(item["amount_minor"])
            elif item["transaction_type"] == "expense":
                amount = int(item["amount_minor"])
                spending += amount
                category_totals[item["category"]] = category_totals.get(item["category"], 0) + amount
                merchant_totals[item["merchant"]] = merchant_totals.get(item["merchant"], 0) + amount
        return {
            "month": month,
            "income_minor": income,
            "spending_minor": spending,
            "net_minor": income - spending,
            "category_totals": category_totals,
            "top_merchants": sorted(merchant_totals.items(), key=lambda pair: pair[1], reverse=True)[:5],
        }

    def forecast(self, user_id: str, days: int = 30) -> dict[str, Any]:
        if days < 1 or days > 90:
            raise AppException(ResponseCode.BAD_REQUEST, Message.INVALID_INPUT, error_code=ErrorCode.FIN_FORECAST_INVALID)
        today = date.today()
        history_start = today - timedelta(days=60)
        history = self.list_transactions(user_id, history_start, today, transaction_type="expense", limit=1000)["items"]
        daily_totals = {history_start + timedelta(days=index): 0 for index in range(61)}
        for transaction in history:
            if transaction.get("source") != "bill":
                daily_totals[date.fromisoformat(transaction["posted_at"])] += int(transaction["amount_minor"])
        samples = list(daily_totals.values())
        daily_mean = statistics.fmean(samples) if samples else 0.0
        daily_std = statistics.pstdev(samples) if len(samples) > 1 else 0.0
        balance = self.current_balance(user_id)["balance_minor"]
        profile = self.repository.get(user_id, "PROFILE") or {}
        buffer_minor = int(profile.get("safety_buffer_minor", 0))
        bills = self.list_bills(user_id, today, today + timedelta(days=days))
        bills_by_date: dict[str, list[dict[str, Any]]] = {}
        for bill in bills:
            bills_by_date.setdefault(bill["next_due_date"], []).append(bill)
        points = []
        alerts = []
        projected = float(balance)
        for offset in range(1, days + 1):
            point_date = today + timedelta(days=offset)
            projected -= daily_mean
            scheduled_income = 0
            scheduled_expense = 0
            for bill in bills_by_date.get(point_date.isoformat(), []):
                if bill["kind"] == "income":
                    scheduled_income += int(bill["amount_minor"])
                else:
                    scheduled_expense += int(bill["amount_minor"])
            projected += scheduled_income - scheduled_expense
            spread = 1.2816 * daily_std * math.sqrt(offset)
            point = {
                "date": point_date.isoformat(),
                "projected_minor": round(projected),
                "lower_minor": round(projected - spread),
                "upper_minor": round(projected + spread),
                "scheduled_income_minor": scheduled_income,
                "scheduled_expense_minor": scheduled_expense,
            }
            points.append(point)
            if point["lower_minor"] < 0 and not any(alert["type"] == "negative_balance" for alert in alerts):
                alerts.append({"type": "negative_balance", "date": point["date"], "balance_minor": point["lower_minor"]})
            elif point["lower_minor"] < buffer_minor and not any(alert["type"] == "safety_buffer" for alert in alerts):
                alerts.append({"type": "safety_buffer", "date": point["date"], "balance_minor": point["lower_minor"]})
        result = {
            "days": days,
            "starting_balance_minor": balance,
            "daily_discretionary_mean_minor": round(daily_mean),
            "daily_discretionary_std_minor": round(daily_std),
            "confidence": 0.80,
            "points": points,
            "alerts": alerts,
        }
        logger.info("event=forecast_generated user_id=%s days=%s alerts=%s", user_id, days, len(alerts))
        return result

    def dashboard(self, user_id: str, month: str) -> dict[str, Any]:
        summary = self.spending_summary(user_id, month)
        budgets = self.budget_status(user_id, month)
        forecast = self.forecast(user_id, 30)
        today = date.today()
        bills = self.list_bills(user_id, today, today + timedelta(days=30))
        insights = []
        for budget in budgets["items"]:
            if budget["utilization"] >= 1:
                insights.append({"type": "budget_exceeded", "category": budget["category"], "amount_minor": -budget["remaining_minor"]})
            elif budget["utilization"] >= 0.8:
                insights.append({"type": "budget_warning", "category": budget["category"], "utilization": budget["utilization"]})
        insights.extend(forecast["alerts"])
        return {
            "balance": self.current_balance(user_id),
            "summary": summary,
            "budgets": budgets["items"],
            "upcoming_bills": bills,
            "forecast": forecast,
            "insights": insights,
        }

    def ensure_conversation(self, user_id: str, conversation_id: str | None) -> str:
        if conversation_id and self.repository.get(user_id, f"CONV#{conversation_id}"):
            return conversation_id
        conversation_id = str(uuid.uuid4())
        now = utc_now()
        entity = ConversationEntity(
            PK=user_pk(user_id), SK=f"CONV#{conversation_id}", entity_type=EntityType.CONVERSATION,
            created_at=now, updated_at=now, conversation_id=conversation_id,
        )
        self.repository.put(entity.to_item())
        return conversation_id

    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, tool_data: dict[str, Any] | None = None) -> dict[str, Any]:
        now = utc_now()
        message_id = str(uuid.uuid4())
        entity = MessageEntity(
            PK=user_pk(user_id), SK=f"CONV#{conversation_id}#MSG#{now}#{message_id}", entity_type=EntityType.MESSAGE,
            created_at=now, updated_at=now, conversation_id=conversation_id,
            message_id=message_id, role=role, content=content, tool_data=tool_data or {},
        )
        self.repository.put(entity.to_item())
        return public_item(entity.to_item())

    def conversation(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        header = self.repository.get(user_id, f"CONV#{conversation_id}")
        if not header:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, error_code=ErrorCode.FIN_TOOL_INVALID)
        messages, _ = self.repository.query_prefix(user_id, f"CONV#{conversation_id}#MSG#", limit=100)
        return {"conversation": public_item(header), "messages": [public_item(item) for item in messages]}

    def _audit(
        self,
        user_id: str,
        action: str,
        actor: str,
        target_type: str,
        target_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> dict[str, Any]:
        now = utc_now()
        audit_id = str(uuid.uuid4())
        return AuditEntity(
            PK=user_pk(user_id), SK=f"AUDIT#{now}#{audit_id}", entity_type=EntityType.AUDIT,
            created_at=now, updated_at=now, audit_id=audit_id, action=action,
            actor=actor, target_type=target_type, target_id=target_id,
            before=public_item(before) if before else None, after=public_item(after) if after else None,
        ).to_item()

    def _adjust_account_balance(self, user_id: str, account_id: str, amount_minor: int, transaction_type: str) -> None:
        account = self.repository.get(user_id, f"ACCOUNT#{account_id}")
        if not account:
            return
        direction = 1 if transaction_type in {"income", "refund"} else -1 if transaction_type == "expense" else 0
        updated = {
            **account,
            "balance_minor": int(account["balance_minor"]) + direction * int(amount_minor),
            "updated_at": utc_now(),
            "version": int(account.get("version", 1)) + 1,
        }
        self.repository.put(updated)


finance_service = FinanceService()
