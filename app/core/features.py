from fastapi import Request
from app.core.config import settings
from app.core.exceptions import AppException, ResponseCode, Message


def feature_enabled(name: str) -> bool:
    return bool(getattr(settings, name, False))


def require_feature(name: str):
    def _dep(_: Request = None):
        if not feature_enabled(name):
            raise AppException(
                ResponseCode.NOT_FOUND,
                Message.RESOURCE_NOT_FOUND,
                details={"feature": name},
            )

    return _dep
