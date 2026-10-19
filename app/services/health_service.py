import time
from datetime import datetime, timezone

from app.core.config import settings


def health_payload(request_id: str, app_start_time: float) -> tuple[dict, bool]:
    payload = {
        "status": "ok",
        "checks": {"api": {"ok": True}},
        "info": {
            "environment": settings.ENVIRONMENT,
            "storage": "memory" if settings.USE_IN_MEMORY_REPOSITORY else "dynamodb",
            "version": settings.APP_VERSION,
            "uptime_seconds": int(time.time() - app_start_time),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id or "-",
    }
    return payload, True
