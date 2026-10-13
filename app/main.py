import datetime
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse

from app.api.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.homepage import Homepage_HTML
from app.utils.logging import configure_logging

logging.basicConfig(level=logging.INFO)
configure_logging()

tags_metadata = [
    {"name": "Health", "description": "Liveness and dependency health."},
    {"name": "Authentication", "description": "Authentication helpers and token validation."},
    {"name": "Users", "description": "Current user identity and billing profile."},
    {"name": "Subscriptions", "description": "Plans, purchases, entitlements, and invoices."},
    {"name": "Admin: subscriptions", "description": "Plan and module administration."},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.FEATURE_KAFKA:
        from app.kafka.producer import start_producer, stop_producer

        await start_producer()
        try:
            yield
        finally:
            await stop_producer()
    else:
        yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_TAGLINE,
    redoc_url=None,
    openapi_tags=tags_metadata,
    lifespan=lifespan,
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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    html = (
        Homepage_HTML
        .replace("{{REQUEST_ID}}", str(getattr(request.state, "request_id", "-")))
        .replace("{{APP_NAME}}", settings.APP_NAME)
        .replace("{{TAGLINE}}", settings.APP_TAGLINE)
        .replace("{{APP_VERSION}}", settings.APP_VERSION)
        .replace("{{ENV}}", settings.ENVIRONMENT)
        .replace("{{API_BASE}}", f"{settings.API_PREFIX.rstrip('/')}/")
        .replace("{{YEAR}}", str(datetime.datetime.now(datetime.UTC).year))
        .replace("{{ORIGIN}}", "")
    )
    return HTMLResponse(html)


app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/redoc", include_in_schema=False)
def custom_redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
    )
