from sqlalchemy.orm import Session

from app.schemas.subscription import ModuleCreate, ModuleUpdate, PlanCreate, SubscriptionPurchaseRequest

from .checkout import CheckoutService
from .entitlements import EntitlementService
from .invoices import InvoiceService
from .lifecycle import SubscriptionLifecycleService
from .plans import PlanService
from .webhooks import BillingWebhookService


class BillingService:
    """Compatibility facade over focused billing services."""

    def __init__(self):
        self.plans = PlanService()
        self.lifecycle = SubscriptionLifecycleService()
        self.entitlements = EntitlementService()
        self.checkout = CheckoutService(self.plans, self.lifecycle)
        self.invoices = InvoiceService()
        self.webhooks = BillingWebhookService(self.lifecycle)

    def get_plans_with_modules(self, db: Session, user_id: str | None = None):
        active_plan_id = self.lifecycle.active_plan_id(db, user_id) if user_id else None
        return self.plans.list(db, active_plan_id)

    async def create_subscription_purchase(self, db: Session, claims: dict, payload: SubscriptionPurchaseRequest):
        return await self.checkout.create(db, claims, payload)

    def get_credits_for_user(self, db: Session, user_id: str):
        return self.lifecycle.credits(db, user_id)

    def get_user_subscriptions_paginated(self, db: Session, user_id: str, page: int = 1, limit: int = 20):
        return self.lifecycle.history(db, user_id, page, limit)

    def get_user_subscriptions(self, db: Session, user_id: str):
        return self.lifecycle.paid_subscriptions(db, user_id)

    async def download_invoice(self, db: Session, _type: str, uuid_str: str):
        return await self.invoices.download(db, uuid_str)

    def get_all_modules(self, db: Session):
        return self.plans.list_modules(db)

    def create_module(self, db: Session, payload: ModuleCreate):
        return self.plans.create_module(db, payload)

    def update_module(self, db: Session, module_id: int, payload: ModuleUpdate):
        return self.plans.update_module(db, module_id, payload)

    def create_plan(self, db: Session, payload: PlanCreate):
        return self.plans.create(db, payload)

    def ensure_paid_tool_access(self, db: Session, user_id: str, module_slug: str, uuid=None):
        return self.entitlements.ensure_access(db, user_id, module_slug, uuid)

    def use_credit(self, db: Session, user_id: str, module_slug: str, credit_type: str):
        return self.entitlements.use_credit(db, user_id, module_slug, credit_type)
