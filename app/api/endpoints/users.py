from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.identity import get_identity_provider
from app.core.security import get_current_user
from app.repositories.user import user_repository
from app.schemas.general_response import SuccessResponse
from app.utils.api_utils import get_db

router = APIRouter()


class UserSettingsUpdate(BaseModel):
    auto_sub: bool


@router.get("/me", response_model=SuccessResponse[dict])
def current_user(
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = get_identity_provider().get_profile_from_claims(claims)
    billing = user_repository.get_by_user_id(db, profile.user_id)
    return SuccessResponse(
        message="Current user retrieved",
        result={
            "id": profile.user_id,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "billing": {
                "auto_renew": bool(billing.auto_sub),
                "plan_id": billing.plan_id,
                "provider": billing.provider,
                "general_credits": {
                    "total": billing.total_general_credits,
                    "used": billing.general_credits_used,
                    "left": billing.general_credits_left,
                },
            } if billing else None,
        },
    )


@router.patch("/me/settings", response_model=SuccessResponse[dict])
def update_current_user_settings(
    payload: UserSettingsUpdate,
    claims: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = user_repository.cancel_subscrption(db, str(claims["sub"]), payload.auto_sub)
    return SuccessResponse(
        message="User settings updated" if updated else "No billing profile found",
        result={"updated": updated, "auto_renew": payload.auto_sub},
    )
