import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.core.exceptions import AppException
from jwt import PyJWKClientError

from app.core.security import CognitoTokenVerifier


class FakeJwksClient:
    def __init__(self, public_key):
        self.public_key = public_key

    def get_signing_key_from_jwt(self, _: str):
        return SimpleNamespace(key=self.public_key)


def make_token(private_key, **overrides):
    now = int(time.time())
    claims = {
        "sub": "cognito-user",
        "iss": f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        "client_id": settings.COGNITO_APP_CLIENT_ID,
        "token_use": "access",
        "iat": now,
        "exp": now + 300,
        "scope": "openid profile",
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-key"})


@pytest.fixture
def verifier_and_key(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = CognitoTokenVerifier()
    fake = FakeJwksClient(private_key.public_key())
    monkeypatch.setattr(verifier, "_client", lambda: fake)
    return verifier, private_key


def test_valid_cognito_access_token(verifier_and_key):
    verifier, private_key = verifier_and_key
    user = verifier.verify(make_token(private_key))
    assert user.user_id == "cognito-user"
    assert user.scopes == ["openid", "profile"]


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"token_use": "id"}, "AUTH_TOKEN_TYPE_INVALID"),
        ({"client_id": "wrong-client"}, "AUTH_CLIENT_INVALID"),
        ({"iss": "https://wrong.example"}, "AUTH_ISSUER_INVALID"),
        ({"exp": 1}, "AUTH_TOKEN_EXPIRED"),
    ],
)
def test_rejects_invalid_cognito_claims(verifier_and_key, override, expected):
    verifier, private_key = verifier_and_key
    with pytest.raises(AppException) as captured:
        verifier.verify(make_token(private_key, **override))
    assert captured.value.error_code == expected


def test_rejects_malformed_token(verifier_and_key):
    verifier, _ = verifier_and_key
    with pytest.raises(AppException) as captured:
        verifier.verify("not-a-jwt")
    assert captured.value.error_code == "AUTH_TOKEN_INVALID"


def test_unknown_signing_key_is_rejected(verifier_and_key, monkeypatch):
    verifier, private_key = verifier_and_key

    class MissingKeyClient:
        def get_signing_key_from_jwt(self, _: str):
            raise PyJWKClientError("Unable to find a signing key that matches")

    monkeypatch.setattr(verifier, "_client", lambda: MissingKeyClient())
    with pytest.raises(AppException) as captured:
        verifier.verify(make_token(private_key))
    assert captured.value.error_code == "AUTH_TOKEN_INVALID"
