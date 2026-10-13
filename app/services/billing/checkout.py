from datetime import datetime, timedelta
from decimal import Decimal
import logging
from urllib.parse import urlencode

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException, Message, ResponseCode
from app.core.identity import get_identity_provider
from app.kafka.producer import send_message
from app.models.subscription import UserSubscription
from app.repositories.subscription import user_subscription_repository
from app.schemas.payment import PaymentResponse
from app.schemas.subscription import SubscriptionPurchaseRequest
from app.services.stripe_service import stripe_service

from .lifecycle import SubscriptionLifecycleService
from .plans import PlanService

logger = logging.getLogger(__name__)


class CheckoutService:
    def __init__(self, plans: PlanService, lifecycle: SubscriptionLifecycleService):
        self.plans = plans
        self.lifecycle = lifecycle

    async def create(self, db: Session, claims: dict, payload: SubscriptionPurchaseRequest) -> PaymentResponse:
        if not claims or not claims.get("sub"):
            raise AppException(ResponseCode.UNAUTHORIZED, Message.INVALID_TOKEN)
        profile = get_identity_provider().get_profile_from_claims(claims)
        user_id = str(profile.user_id)
        plan = self.plans.get(db, payload.plan_id)
        expiry = datetime.utcnow() + timedelta(days=plan.duration)
        frontend = settings.FRONTEND_URL.rstrip("/")
        params = {"plan_id": plan.id, "user_id": user_id}
        confirmation_url = f"{frontend}/subscription-plans/confirmation?{urlencode(params)}"
        failure_url = f"{frontend}/subscription-plans"

        if plan.pricing <= Decimal("0.00"):
            if user_subscription_repository.have_availed_free_plan(db, user_id, plan.id):
                raise AppException(ResponseCode.FORBIDDEN, Message.FREE_PLAN_ALREADY_AVAILED)
            subscription = user_subscription_repository.create(db, UserSubscription(
                user_id=user_id, plan_id=plan.id, plan_title=plan.plan_title,
                purchase_at=datetime.utcnow(), amount_paid=plan.pricing, expiry_at=expiry,
                payment_status="paid", total_credits=plan.credits, credits_left=plan.credits,
            ))
            self.lifecycle.ensure_user(db, user_id, plan.id, "free")
            await self._notify(profile.email, profile.first_name, plan.plan_title, plan.pricing, subscription)
            return PaymentResponse(
                uuid=str(subscription.id), user_id=user_id, payment_id=None, payment_link=None,
                success_url=confirmation_url, failure_url=failure_url, plan_name=plan.plan_title,
            )

        if not settings.FEATURE_PAYMENTS:
            raise AppException(ResponseCode.SERVICE_UNAVAILABLE, "Payments are disabled")
        success_url = f"{confirmation_url}&session_id={{CHECKOUT_SESSION_ID}}"
        session = stripe_service.create_checkout_session(
            service_name=f"Subscription - {plan.plan_title}",
            amount_cents=int(plan.pricing * 100), success_url=success_url, cancel_url=failure_url,
        )
        subscription = user_subscription_repository.create(db, UserSubscription(
            user_id=user_id, plan_id=plan.id, plan_title=plan.plan_title,
            purchase_at=datetime.utcnow(), purchased_id=session.id, amount_paid=plan.pricing,
            expiry_at=expiry, payment_status="pending", total_credits=plan.credits,
            credits_left=plan.credits,
        ))
        return PaymentResponse(
            uuid=str(subscription.id), user_id=user_id, payment_id=session.id,
            payment_link=session.url, success_url=success_url, failure_url=failure_url,
            plan_name=plan.plan_title,
        )

    async def _notify(self, email, first_name, plan_title, amount, subscription) -> None:
        if not email:
            return
        try:
            await send_message(settings.KAFKA_EMAIL_TOPIC, {
                "type": "purchase_email",
                "data": {
                    "first_name": first_name or "Customer", "email": email,
                    "plan_title": plan_title, "amount_paid": float(amount),
                    "purchase_at": str(subscription.purchase_at),
                    "purchase_id": str(subscription.id), "purchase_type": "plan",
                    "plan_credits": subscription.total_credits,
                },
            })
        except Exception:
            logger.exception("Purchase succeeded, but its notification could not be sent")
