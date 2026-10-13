import time
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.core.exceptions import AppException, Message, ResponseCode

auth = HTTPBearer(auto_error=False)

DEV_USER = {
    "sub": "dev-user",
    "aud": settings.EXPECTED_AUD,
    "scopes": ["admin"],
    "exp": 0,
    "jti": "dev",
}


def create_local_token(user_id: str, extra: Optional[dict] = None, ttl: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + ttl,
        "aud": settings.EXPECTED_AUD,
        "scopes": [],
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_jwt(creds: Optional[HTTPAuthorizationCredentials] = Depends(auth)) -> Optional[dict]:
    if not settings.FEATURE_AUTH or (settings.AUTH_MODE or "").lower() == "none":
        return dict(DEV_USER)

    if creds is None:
        return None

    token = creds.credentials
    mode = (settings.AUTH_MODE or "jwt_rs256").lower()

    try:
        if mode == "local":
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"],
                audience=settings.EXPECTED_AUD,
                options={"require": ["exp", "iat"], "verify_aud": bool(settings.EXPECTED_AUD)},
                leeway=settings.CLOCK_SKEW_LEEWAY,
            )
        else:
            if not settings.PASSPORT_PUBLIC_KEY:
                raise HTTPException(status_code=401, detail="Invalid token: signing key is not configured")
            payload = jwt.decode(
                token,
                settings.PASSPORT_PUBLIC_KEY,
                algorithms=["RS256"],
                audience=settings.EXPECTED_AUD,
                options={"require": ["exp", "iat"]},
                leeway=settings.CLOCK_SKEW_LEEWAY,
            )

        exp = payload["exp"]
        ttl = int(exp - time.time())
        if ttl <= 0:
            raise HTTPException(status_code=401, detail="Token expired")

        payload["raw_token"] = token
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


verify_passport_jwt = verify_jwt


def get_optional_user(claims: Optional[dict] = Depends(verify_jwt)) -> Optional[dict]:
    return claims


def get_current_user(claims: Optional[dict] = Depends(verify_jwt)) -> dict:
    if not claims or not claims.get("sub"):
        raise AppException(ResponseCode.UNAUTHORIZED, Message.INVALID_TOKEN)
    return claims


def require_admin(claims: dict = Depends(get_current_user)) -> dict:
    scopes = claims.get("scopes") or []
    role = claims.get("role")
    if "admin" in scopes or role == "admin":
        return claims
    if settings.ADMIN_OPEN and settings.ENVIRONMENT.lower() in ("local", "test", "dev"):
        return claims
    raise AppException(ResponseCode.FORBIDDEN, Message.UNAUTHORIZED_ACCESS)


def get_user_data_from_claims(claims: dict) -> dict:
    return {
        "user_id": claims.get("sub"),
        "aud": claims.get("aud"),
        "scopes": claims.get("scopes", []),
        "exp": claims.get("exp"),
        "jti": claims.get("jti"),
    }


def get_jti_from_claims(claims: dict) -> str | None:
    return claims.get("jti")
