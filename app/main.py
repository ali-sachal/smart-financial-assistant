from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import Message, register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.schemas.general_response import SuccessResponse
from app.utils.logging import configure_logging

configure_logging()

tags_metadata = [
    {"name": "Health", "description": "Application liveness."},
    {"name": "Authentication", "description": "Amazon Cognito access-token identity."},
    {"name": "Finance", "description": "Profiles, accounts, transactions, budgets, bills, dashboards, and forecasts."},
    {"name": "Receipts", "description": "Multimodal receipt extraction and review."},
    {"name": "Assistant", "description": "Grounded financial conversations and tool execution."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_TAGLINE,
    openapi_tags=tags_metadata,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", response_model=SuccessResponse[dict], include_in_schema=False)
def home(request: Request) -> SuccessResponse[dict]:
    return SuccessResponse(
        code="APP_READY",
        message=Message.APP_READY,
        result={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "documentation": "/docs",
            "year": datetime.now(UTC).year,
        },
        request_id=getattr(request.state, "request_id", "-"),
    )
