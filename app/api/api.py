# app/api/api.py
from fastapi import APIRouter

from app.api.endpoints import healthcheck
from app.core.config import settings
from app.core.domains import include_domain_routers

api_router = APIRouter()
api_router.include_router(healthcheck.router, prefix="/health", tags=["Health"])

if settings.FEATURE_AUTH:
    from app.api.endpoints import auth

    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

if settings.FEATURE_USERS:
    from app.api.endpoints import users

    api_router.include_router(users.router, prefix="/users", tags=["Users"])

if settings.FEATURE_SUBSCRIPTION:
    from app.api.endpoints import subscription

    api_router.include_router(subscription.router, prefix="/subscriptions", tags=["Subscriptions"])
    api_router.include_router(subscription.admin_router, prefix="/admin/subscriptions", tags=["Admin: subscriptions"])

include_domain_routers(api_router)
