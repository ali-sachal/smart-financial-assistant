from sqlalchemy.orm import Session

from app.core.exceptions import AppException, Message, ResponseCode
from app.repositories.subscription import user_subscription_repository

from .lifecycle import SubscriptionLifecycleService


class BillingWebhookService:
    def __init__(self, lifecycle: SubscriptionLifecycleService):
        self.lifecycle = lifecycle

    def handle_stripe(self, db: Session, event: dict) -> dict:
        event_type = event.get("type")
        if event_type not in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            return {"handled": False, "event_type": event_type}
        session = event["data"]["object"]
        if session.get("payment_status") != "paid":
            return {"handled": False, "reason": "payment_not_paid"}
        subscription = user_subscription_repository.get_by_purchase_id(db, session["id"])
        if not subscription:
            raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND)
        if subscription.payment_status != "paid":
            user_subscription_repository.mark_paid(db, subscription)
        self.lifecycle.ensure_user(
            db, subscription.user_id, subscription.plan_id, "stripe", session.get("customer")
        )
        return {"handled": True, "subscription_id": str(subscription.id)}
