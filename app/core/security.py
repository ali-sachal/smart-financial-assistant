import logging
import time
from typing import Any

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import (
    ExpiredSignatureError,
    InvalidIssuerError,
    InvalidTokenError,
    PyJWKClient,
    PyJWKClientConnectionError,
    PyJWKClientError,
)

from app.core.config import settings
from app.core.exceptions import AppException, ErrorCode, Message, ResponseCode
from app.schemas.auth import AuthenticatedUser
from app.utils.logging import get_module_logger

logger = get_module_logger("auth")
bearer = HTTPBearer(auto_error=False)


class CognitoTokenVerifier:
    def __init__(self) -> None:
        self._jwks_client: PyJWKClient | None = None
        self._created_at = 0.0

    @property
    def issuer(self) -> str:
        return (
            f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
            f"{settings.COGNITO_USER_POOL_ID}"
        )

    def _client(self) -> PyJWKClient:
        now = time.monotonic()
        expired = now - self._created_at >= settings.COGNITO_JWKS_TTL_SECONDS
        if self._jwks_client is None or expired:
            self._jwks_client = PyJWKClient(
                f"{self.issuer}/.well-known/jwks.json",
                cache_keys=True,
                lifespan=settings.COGNITO_JWKS_TTL_SECONDS,
            )
            self._created_at = now
        return self._jwks_client

    def verify(self, token: str) -> AuthenticatedUser:
        if not settings.COGNITO_USER_POOL_ID or not settings.COGNITO_APP_CLIENT_ID:
            logger.error("event=cognito_configuration_missing")
            raise AppException(
                ResponseCode.SERVICE_UNAVAILABLE,
                Message.AUTH_JWKS_UNAVAILABLE,
                error_code=ErrorCode.AUTH_JWKS_UNAVAILABLE,
            )
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not header.get("kid"):
                raise AppException(
                    ResponseCode.UNAUTHORIZED,
                    Message.AUTH_TOKEN_INVALID,
                    error_code=ErrorCode.AUTH_TOKEN_INVALID,
                )
            signing_key = self._client().get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer,
                options={"require": ["exp", "iat", "iss", "sub", "token_use"]},
                leeway=settings.CLOCK_SKEW_LEEWAY,
            )
            if claims.get("token_use") != "access":
                raise AppException(
                    ResponseCode.UNAUTHORIZED,
                    Message.AUTH_TOKEN_TYPE_INVALID,
                    error_code=ErrorCode.AUTH_TOKEN_TYPE_INVALID,
                )
            if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
                raise AppException(
                    ResponseCode.UNAUTHORIZED,
                    Message.AUTH_CLIENT_INVALID,
                    error_code=ErrorCode.AUTH_CLIENT_INVALID,
                )
            scopes = str(claims.get("scope") or "").split()
            groups = list(claims.get("cognito:groups") or [])
            return AuthenticatedUser(
                user_id=str(claims["sub"]),
                email=claims.get("email"),
                username=claims.get("username") or claims.get("cognito:username"),
                scopes=scopes,
                groups=groups,
            )
        except AppException:
            raise
        except ExpiredSignatureError as exc:
            raise AppException(
                ResponseCode.UNAUTHORIZED,
                Message.AUTH_TOKEN_EXPIRED,
                error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            ) from exc
        except InvalidIssuerError as exc:
            raise AppException(
                ResponseCode.UNAUTHORIZED,
                Message.AUTH_ISSUER_INVALID,
                error_code=ErrorCode.AUTH_ISSUER_INVALID,
            ) from exc
        except (PyJWKClientConnectionError, OSError) as exc:
            logger.exception("event=cognito_jwks_failure")
            raise AppException(
                ResponseCode.SERVICE_UNAVAILABLE,
                Message.AUTH_JWKS_UNAVAILABLE,
                error_code=ErrorCode.AUTH_JWKS_UNAVAILABLE,
            ) from exc
        except PyJWKClientError as exc:
            raise AppException(
                ResponseCode.UNAUTHORIZED,
                Message.AUTH_TOKEN_INVALID,
                error_code=ErrorCode.AUTH_TOKEN_INVALID,
            ) from exc
        except InvalidTokenError as exc:
            raise AppException(
                ResponseCode.UNAUTHORIZED,
                Message.AUTH_TOKEN_INVALID,
                error_code=ErrorCode.AUTH_TOKEN_INVALID,
            ) from exc


token_verifier = CognitoTokenVerifier()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthenticatedUser:
    if credentials is None:
        raise AppException(
            ResponseCode.UNAUTHORIZED,
            Message.AUTH_TOKEN_MISSING,
            error_code=ErrorCode.AUTH_TOKEN_MISSING,
        )
    return token_verifier.verify(credentials.credentials)


def require_admin(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if "admin" not in user.groups:
        raise AppException(
            ResponseCode.FORBIDDEN,
            Message.UNAUTHORIZED_ACCESS,
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
        )
    return user
