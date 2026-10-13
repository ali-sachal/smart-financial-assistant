# app/core/middleware.py
import time
import uuid
import logging
import json
from typing import Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import set_request_id, reset_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.perf_counter()

        token = set_request_id(request_id)

        logger = logging.getLogger("request")
        def _sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
            masked = {}
            for k, v in headers.items():
                lk = k.lower()
                if lk in ("authorization", "cookie", "set-cookie"):
                    masked[k] = "***"
                else:
                    masked[k] = v
            return masked

        method = request.method
        path = request.url.path
        ctype = request.headers.get("content-type", "-")
        logger.info(f"request method={method} path={path} content_type={ctype}")

        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            reset_request_id(token)
            if response is not None:
                duration_ms = int((time.perf_counter() - request.state.start_time) * 1000)
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{duration_ms}ms"
                status_code = getattr(response, "status_code", 0)
                logger.info(f"response method={method} path={path} status={status_code} duration_ms={duration_ms}")
