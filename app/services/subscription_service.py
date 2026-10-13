"""Backward-compatible import for the modular billing service."""

from app.services.billing import BillingService, billing_service

SubscriptionService = BillingService
subscription_service = billing_service

__all__ = ["SubscriptionService", "subscription_service"]
