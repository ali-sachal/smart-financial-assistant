import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.logging import reset_request_id, set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.perf_counter()
        token = set_request_id(request_id)
        logger = logging.getLogger("api")
        logger.info(
            "event=request_started method=%s path=%s content_type=%s",
            request.method,
            request.url.path,
            request.headers.get("content-type", "-"),
        )
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            try:
                duration_ms = int((time.perf_counter() - request.state.start_time) * 1000)
                if response is not None:
                    response.headers["X-Request-ID"] = request_id
                    response.headers["X-Response-Time"] = f"{duration_ms}ms"
                    logger.info(
                        "event=request_completed method=%s path=%s status=%s duration_ms=%s",
                        request.method,
                        request.url.path,
                        response.status_code,
                        duration_ms,
                    )
            finally:
                reset_request_id(token)
