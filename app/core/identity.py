from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

import requests

from app.core.config import settings
from app.core.exceptions import AppException, Message, ResponseCode

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    account_created: bool = False
    extra: dict = field(default_factory=dict)


def _payload_get(payload: Any, key: str, default=None):
    if payload is None:
        return default
    if isinstance(payload, dict):
        return payload.get(key, default)
    return getattr(payload, key, default)


class IdentityProvider(Protocol):
    def get_profile_from_claims(self, claims: dict) -> UserProfile: ...
    def get_profile(self, user_id: str) -> UserProfile: ...
    def auto_signup(self, payload: Any) -> UserProfile: ...


class LocalIdentity:
    """Identity that does not call an external IAM. Guest checkout mints a user id."""

    def get_profile_from_claims(self, claims: dict) -> UserProfile:
        claims = claims or {}
        return UserProfile(
            user_id=str(claims.get("sub") or ""),
            first_name=claims.get("first_name") or claims.get("given_name"),
            last_name=claims.get("last_name") or claims.get("family_name"),
            email=claims.get("email"),
            extra=claims,
        )

    def get_profile(self, user_id: str) -> UserProfile:
        return UserProfile(
            user_id=str(user_id),
            first_name="Customer",
            last_name="",
            email="customer@example.com",
        )

    def auto_signup(self, payload: Any) -> UserProfile:
        user_id = str(_payload_get(payload, "user_id") or uuid.uuid4())
        password = secrets.token_urlsafe(10)
        return UserProfile(
            user_id=user_id,
            first_name=_payload_get(payload, "first_name") or "Customer",
            last_name=_payload_get(payload, "last_name") or "",
            email=_payload_get(payload, "email"),
            password=password,
            account_created=True,
        )


class LaravelIdentity:
    """Laravel Passport user directory. Falls back to JWT claims / local signup
    when the Laravel URL is not configured (generic projects).
    """

    def __init__(self, require_remote: bool = False):
        self.require_remote = require_remote
        self._local = LocalIdentity()

    def _api_url(self) -> str:
        return (settings.LARAVEL_API_URL or "").rstrip("/")

    def _client_token(self) -> str:
        url = f"{self._api_url()}/oauth/token"
        response = requests.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.LARAVEL_CLIENT_ID,
                "client_secret": settings.LARAVEL_CLIENT_SECRET,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def get_profile_from_claims(self, claims: dict) -> UserProfile:
        token = (claims or {}).get("raw_token")
        if token and self._api_url():
            try:
                response = requests.get(
                    f"{self._api_url()}/api/user",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                response.raise_for_status()
                body = response.json()
                user = body.get("data", body)
                return UserProfile(
                    user_id=str(user.get("id") or claims.get("sub")),
                    first_name=user.get("first_name") or user.get("name"),
                    last_name=user.get("last_name") or "",
                    email=user.get("email"),
                    extra=user if isinstance(user, dict) else {},
                )
            except Exception as exc:
                logger.exception("Laravel /api/user failed")
                if self.require_remote:
                    raise AppException(
                        ResponseCode.SERVICE_UNAVAILABLE,
                        Message.LARAVEL_USER_INFO_REQUEST_FAILED,
                        details={"error": str(exc)},
                    )
        return self._local.get_profile_from_claims(claims)

    def get_profile(self, user_id: str) -> UserProfile:
        if not self._api_url():
            if self.require_remote:
                raise AppException(
                    ResponseCode.SERVICE_UNAVAILABLE,
                    Message.LARAVEL_USER_INFO_REQUEST_FAILED,
                    details={"reason": "LARAVEL_API_URL is not set"},
                )
            return self._local.get_profile(user_id)
        try:
            token = self._client_token()
            response = requests.get(
                f"{self._api_url()}/api/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            body = response.json()
            user = body.get("data", body)
            return UserProfile(
                user_id=str(user.get("id") or user_id),
                first_name=user.get("first_name") or user.get("name") or "Customer",
                last_name=user.get("last_name") or "",
                email=user.get("email") or "customer@example.com",
                extra=user if isinstance(user, dict) else {},
            )
        except AppException:
            raise
        except Exception as exc:
            logger.exception("Laravel user lookup failed user_id=%s", user_id)
            if self.require_remote:
                raise AppException(
                    ResponseCode.SERVICE_UNAVAILABLE,
                    Message.LARAVEL_USER_INFO_REQUEST_FAILED,
                    details={"error": str(exc)},
                )
            return self._local.get_profile(user_id)

    def auto_signup(self, payload: Any) -> UserProfile:
        if not self._api_url():
            if self.require_remote:
                raise AppException(
                    ResponseCode.SERVICE_UNAVAILABLE,
                    Message.LARAVEL_TOKEN_REQUEST_FAILED,
                    details={"reason": "LARAVEL_API_URL is not set"},
                )
            return self._local.auto_signup(payload)
        try:
            response = requests.post(
                f"{self._api_url()}/api/auto-signup",
                json={
                    "first_name": _payload_get(payload, "first_name"),
                    "last_name": _payload_get(payload, "last_name"),
                    "email": _payload_get(payload, "email"),
                    "phone_number": _payload_get(payload, "phone_number"),
                    "user_source": _payload_get(payload, "user_source"),
                    "category_id": _payload_get(payload, "category_id"),
                },
                timeout=15,
            )
            response.raise_for_status()
            body = response.json()
            user = body.get("data", body)
            return UserProfile(
                user_id=str(user.get("id") or user.get("user_id")),
                first_name=user.get("first_name") or _payload_get(payload, "first_name"),
                last_name=user.get("last_name") or _payload_get(payload, "last_name") or "",
                email=user.get("email") or _payload_get(payload, "email"),
                password=user.get("password"),
                account_created=True,
                extra=user if isinstance(user, dict) else {},
            )
        except AppException:
            raise
        except Exception as exc:
            logger.exception("Laravel auto-signup failed")
            raise AppException(
                ResponseCode.SERVICE_UNAVAILABLE,
                Message.LARAVEL_TOKEN_REQUEST_FAILED,
                details={"error": str(exc)},
            )


_provider: Optional[IdentityProvider] = None


def get_identity_provider() -> IdentityProvider:
    global _provider
    if _provider is not None:
        return _provider
    mode = (settings.AUTH_MODE or "jwt_rs256").lower()
    if mode == "laravel":
        _provider = LaravelIdentity(require_remote=True)
    elif mode in ("jwt_rs256", "passport"):
        _provider = LaravelIdentity(require_remote=False)
    else:
        _provider = LocalIdentity()
    return _provider


def reset_identity_provider() -> None:
    global _provider
    _provider = None
