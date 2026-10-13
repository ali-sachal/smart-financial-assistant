from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppException, Message, ResponseCode
from app.repositories.subscription import module_repository, plan_detail_repository, user_subscription_repository
from app.repositories.user import user_repository


class EntitlementService:
    def usable_credits(self, db: Session, user_id: str) -> dict:
        user = user_repository.get_general_credits(db, user_id)
        general = {"total_credits": 0, "credits_left": 0, "credits_used": 0} if user is None else {
            "total_credits": user.total_general_credits,
            "credits_left": user.general_credits_left,
            "credits_used": user.general_credits_used,
        }
        subscriptions = user_subscription_repository.get_active_paid_credits(db, user_id)
        plan = {
            "total_credits": sum(item.total_credits for item in subscriptions),
            "credits_left": sum(item.credits_left for item in subscriptions),
            "credits_used": sum(item.credits_used for item in subscriptions),
        }
        return {"general_credits": general, "plan_credits": plan}

    def ensure_access(self, db: Session, user_id: str, module_slug: str, operation_id: Optional[UUID] = None) -> tuple[bool, str]:
        module = module_repository.get_by_slug(db, module_slug)
        details = {"uuid": str(operation_id) if operation_id else None, "module": module_slug}
        if not module:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND, {**details, "reason": "Module not found"})
        subscription = user_subscription_repository.get_latest_active_paid_by_user_id(db, user_id)
        if not subscription:
            raise AppException(ResponseCode.FORBIDDEN, Message.PLAN_EXPIRED, {**details, "reason": "No active paid subscription found"})
        entitlement = plan_detail_repository.get_active_module_limit(db, subscription.plan_id, module.id)
        if not entitlement:
            raise AppException(ResponseCode.FORBIDDEN, Message.CREDIT_LIMIT_EXCEED, {**details, "reason": "Module is not included in the active plan"})
        credits = self.usable_credits(db, user_id)
        required = module.credits_required
        general = credits["general_credits"]["credits_left"]
        plan = credits["plan_credits"]["credits_left"]
        if general >= required:
            return True, "general"
        if plan >= required:
            return True, "plan"
        if general + plan >= required:
            return True, "both"
        raise AppException(ResponseCode.FORBIDDEN, Message.CREDIT_LIMIT_EXCEED, {
            **details, "required": float(required), "general_credits_left": float(general),
            "plan_credits_left": float(plan), "reason": "Not enough credits",
        })

    def use_credit(self, db: Session, user_id: str, module_slug: str, credit_type: str) -> bool:
        module = module_repository.get_by_slug(db, module_slug)
        if not module:
            return False
        remaining = module.credits_required
        general = user_repository.get_general_credits(db, user_id)
        subscriptions = user_subscription_repository.get_active_paid_credits(db, user_id)
        usage = []
        if credit_type in {"plan", "both"}:
            for subscription in subscriptions:
                deducted = min(subscription.credits_left, remaining)
                if deducted > 0:
                    usage.append({"id": subscription.id, "type": "plan", "used_credit": deducted})
                    remaining -= deducted
                if remaining <= 0:
                    break
        if remaining > 0 and credit_type in {"general", "both"} and general:
            deducted = min(general.general_credits_left, remaining)
            if deducted > 0:
                usage.append({"id": general.user_id, "type": "general", "used_credit": deducted})
                remaining -= deducted
        return remaining <= 0 and user_subscription_repository.update_usage(db, usage)
