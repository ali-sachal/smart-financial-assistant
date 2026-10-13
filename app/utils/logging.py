import json
import logging
import os
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

REQUEST_ID_CTX_VAR: ContextVar[str] = ContextVar("request_id", default="-")
BASE_LOG_DIR = Path(os.getenv("LOGS_DIR", "logs"))


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CTX_VAR.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def set_request_id(request_id: str | None):
    return REQUEST_ID_CTX_VAR.set(request_id or "-")


def reset_request_id(token) -> None:
    REQUEST_ID_CTX_VAR.reset(token)


def _json_enabled() -> bool:
    default = "true" if os.getenv("ENVIRONMENT", "local").lower() in {"prod", "production", "staging"} else "false"
    return os.getenv("LOG_JSON", default).lower() in {"1", "true", "yes"}


def _level() -> int:
    return getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)


def _formatter() -> logging.Formatter:
    if _json_enabled():
        return JsonFormatter()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | req_id=%(request_id)s | %(message)s"
    )
    formatter.converter = time.gmtime
    return formatter


def _handler(component: str) -> logging.Handler:
    directory = BASE_LOG_DIR / component
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(_level())
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(_formatter())
    return handler


def get_module_logger(component: str) -> logging.Logger:
    logger = logging.getLogger(component)
    logger.setLevel(_level())
    expected = str((BASE_LOG_DIR / component / f"{datetime.now().strftime('%Y-%m-%d')}.log").resolve())
    if not any(getattr(item, "baseFilename", None) == expected for item in logger.handlers):
        logger.addHandler(_handler(component))
    logger.propagate = True
    return logger


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(_level())
    if not any(getattr(handler, "_finance_console", False) for handler in root.handlers):
        handler = logging.StreamHandler()
        handler._finance_console = True
        handler.setLevel(_level())
        handler.addFilter(RequestIdFilter())
        handler.setFormatter(_formatter())
        root.addHandler(handler)

    for component in ("api", "services", "repositories", "auth", "ai", "agent", "audit", "errors"):
        get_module_logger(component)
