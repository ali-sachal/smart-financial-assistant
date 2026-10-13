from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.user import Users
from app.repositories.subscription import user_subscription_repository
from app.repositories.user import user_repository


class SubscriptionLifecycleService:
    def active(self, db: Session, user_id: str):
        return user_subscription_repository.get_latest_active_paid_by_user_id(db, user_id)

    def active_plan_id(self, db: Session, user_id: str) -> int | None:
        subscription = self.active(db, user_id)
        return subscription.plan_id if subscription else None

    def ensure_user(self, db: Session, user_id: str, plan_id: int, provider: str, customer_id: str | None = None) -> Users:
        user = user_repository.get_by_user_id(db, user_id)
        if not user:
            user = user_repository.create(db, Users(user_id=user_id))
        user.plan_id = plan_id
        user.auto_sub = True
        user.provider = provider
        user.customer_id = customer_id or user.customer_id
        return user_repository.update(db, user)

    def credits(self, db: Session, user_id: str) -> dict[str, Any]:
        cutoff = datetime.combine(date.today() - timedelta(days=1), datetime.min.time())
        blocked = user_subscription_repository.is_failed_or_pending_latest_purchase_after_expired_paid_subscriptions(db, user_id, cutoff)
        zero = {"total_credits": 0, "credits_left": 0, "credits_used": 0}
        if blocked:
            return {"general_credits": zero.copy(), "all_credits": zero.copy()}
        user = user_repository.get_general_credits(db, user_id)
        general = zero.copy() if user is None else {
            "total_credits": user.total_general_credits,
            "credits_left": user.general_credits_left,
            "credits_used": user.general_credits_used,
        }
        billing_user = user_repository.get_by_user_id(db, user_id)
        credits = (
            user_subscription_repository.get_all_credits(db, user_id)
            if billing_user and billing_user.auto_sub
            else user_subscription_repository.get_all_credits_of_active_plan(db, user_id)
        )
        all_credits = zero.copy() if not credits else {
            "total_credits": sum(item.total_credits for item in credits),
            "credits_left": sum(item.credits_left for item in credits),
            "credits_used": sum(item.credits_used for item in credits),
        }
        return {"general_credits": general, "all_credits": all_credits}

    def history(self, db: Session, user_id: str, page: int = 1, limit: int = 20) -> dict[str, Any]:
        items, total = user_subscription_repository.get_paginated_by_user_id(db, user_id, (page - 1) * limit, limit)
        return {
            "data": [{column: getattr(item, column) for column in (
                "id", "user_id", "plan_id", "plan_title", "purchase_at", "purchased_id",
                "total_credits", "credits_used", "credits_left", "payment_status", "amount_paid", "expiry_at"
            )} for item in items],
            "total": total, "current_page": page, "per_page": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    def paid_subscriptions(self, db: Session, user_id: str):
        return [item for item in user_subscription_repository.get_all_by_user_id(db, user_id) if item.payment_status == "paid"]
