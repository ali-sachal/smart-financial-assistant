from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.features import require_feature
from app.core.security import get_current_user
from app.schemas.general_response import SuccessResponse
from app.utils.api_utils import get_db

router = APIRouter()
prefix = "/example"
tags = ["Example domain"]


@router.get("/ping", response_model=SuccessResponse[dict])
def ping():
    return SuccessResponse(message="Example domain is enabled", result={"domain": "example"})


@router.get("/whoami", response_model=SuccessResponse[dict])
def whoami(claims: dict = Depends(get_current_user)):
    return SuccessResponse(result={"user_id": str(claims["sub"])})


@router.get(
    "/entitlements/{module_slug}",
    response_model=SuccessResponse[dict],
    dependencies=[Depends(require_feature("FEATURE_SUBSCRIPTION"))],
)
def check_entitlement(
    module_slug: str,
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.subscription_service import subscription_service

    allowed, credit_type = subscription_service.ensure_paid_tool_access(
        db, str(claims["sub"]), module_slug
    )
    return SuccessResponse(
        message="Entitlement granted",
        result={"allowed": allowed, "module_slug": module_slug, "credit_type": credit_type},
    )
