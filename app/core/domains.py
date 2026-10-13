"""Discovery helpers for product domains that extend the platform."""

from __future__ import annotations

import importlib
import logging

from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)


def _domain_module(domain: str, module: str):
    if not domain.replace("_", "").isalnum():
        raise ValueError(f"Invalid domain name: {domain!r}")
    package = {
        "api": "app.api.endpoints",
        "models": "app.api.models",
    }[module]
    return importlib.import_module(f"{package}.{domain}")


def include_domain_routers(root_router: APIRouter) -> None:
    for domain in settings.enabled_domains:
        try:
            api = _domain_module(domain, "api")
        except ModuleNotFoundError as exc:
            if exc.name == f"app.api.endpoints.{domain}":
                logger.warning("Enabled domain %s has no api module", domain)
                continue
            raise
        root_router.include_router(
            api.router,
            prefix=getattr(api, "prefix", f"/{domain}"),
            tags=getattr(api, "tags", [domain.replace("_", " ").title()]),
        )


def import_domain_models() -> None:
    for domain in settings.enabled_domains:
        try:
            _domain_module(domain, "models")
        except ModuleNotFoundError as exc:
            if exc.name != f"app.api.models.{domain}":
                raise
