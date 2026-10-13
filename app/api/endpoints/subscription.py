from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException, Message, ResponseCode
from app.core.features import require_feature
from app.core.security import get_current_user, get_optional_user, require_admin
from app.schemas.general_response import SuccessResponse
from app.schemas.subscription import ModuleCreate, PlanCreate, SubscriptionPurchaseRequest
from app.services.subscription_service import subscription_service
from app.services.stripe_service import stripe_service
from app.utils.api_utils import get_db

router = APIRouter(dependencies=[Depends(require_feature("FEATURE_SUBSCRIPTION"))])
admin_router = APIRouter(dependencies=[Depends(require_admin), Depends(require_feature("FEATURE_SUBSCRIPTION"))])


@router.post("/webhooks/stripe", response_model=SuccessResponse[dict])
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    event = stripe_service.construct_webhook_event(await request.body(), stripe_signature)
    return SuccessResponse(result=subscription_service.webhooks.handle_stripe(db, event))


@router.get("/plans", response_model=SuccessResponse[list])
def list_plans(
    claims: dict | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    user_id = str(claims["sub"]) if claims and claims.get("sub") else None
    return SuccessResponse(result=subscription_service.get_plans_with_modules(db, user_id))


@router.post("/purchases", response_model=SuccessResponse[dict])
async def create_purchase(
    payload: SubscriptionPurchaseRequest,
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await subscription_service.create_subscription_purchase(db, claims, payload)
    return SuccessResponse(message="Purchase created", result=result.model_dump(mode="json"))


@router.get("/me/credits", response_model=SuccessResponse[dict])
def current_credits(
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SuccessResponse(result=subscription_service.get_credits_for_user(db, str(claims["sub"])))


@router.get("/me/history", response_model=SuccessResponse[dict])
def purchase_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return SuccessResponse(
        result=subscription_service.get_user_subscriptions_paginated(
            db, str(claims["sub"]), page=page, limit=limit
        )
    )


@router.get("/me/invoices/{subscription_id}")
async def download_invoice(
    subscription_id: str,
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not settings.FEATURE_INVOICES:
        raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND)
    subscriptions = subscription_service.get_user_subscriptions(db, str(claims["sub"]))
    if not any(str(item.id) == subscription_id for item in subscriptions):
        raise AppException(ResponseCode.NOT_FOUND, Message.RESOURCE_NOT_FOUND)
    pdf, filename = await subscription_service.download_invoice(db, "plan", subscription_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_router.get("/modules", response_model=SuccessResponse[list])
def list_modules(db: Session = Depends(get_db)):
    return SuccessResponse(result=subscription_service.get_all_modules(db))


@admin_router.post("/modules", response_model=SuccessResponse[dict])
def create_module(payload: ModuleCreate, db: Session = Depends(get_db)):
    module = subscription_service.create_module(db, payload)
    return SuccessResponse(message="Module created", result=ModuleCreate.model_validate(module).model_dump(mode="json"))


@admin_router.post("/plans", response_model=SuccessResponse[dict])
def create_plan(payload: PlanCreate, db: Session = Depends(get_db)):
    plan = subscription_service.create_plan(db, payload)
    return SuccessResponse(message="Plan created", result={"id": plan.id, "title": plan.plan_title})
