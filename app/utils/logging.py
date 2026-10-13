# app/utils/logging.py
import logging
import json
import os
import time
from pathlib import Path
from enum import StrEnum
from typing import Union, Optional
from contextvars import ContextVar
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | req_id=%(request_id)s | %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s | %(levelname)s | %(name)s | req_id=%(request_id)s | %(pathname)s:%(funcName)s:%(lineno)d | %(message)s"

BASE_LOG_DIR = Path(os.getenv("LOGS_DIR", "logs"))

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"   # alias to WARNING
    error = "ERROR"
    debug = "DEBUG"


# Context variable to carry request_id through async tasks
REQUEST_ID_CTX_VAR: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = REQUEST_ID_CTX_VAR.get()
        except LookupError:
            record.request_id = "-"
        return True


def set_request_id(request_id: Optional[str]):
    if not request_id:
        request_id = "-"
    return REQUEST_ID_CTX_VAR.set(request_id)


def reset_request_id(token) -> None:
    try:
        REQUEST_ID_CTX_VAR.reset(token)
    except Exception:
        pass


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        payload = {
            "timestamp": ts,
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_stream_handler(level: int, json_enabled: bool) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    if json_enabled:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = LOG_FORMAT_DEBUG if level == logging.DEBUG else LOG_FORMAT
        formatter = logging.Formatter(fmt)
        formatter.converter = time.gmtime
        handler.setFormatter(formatter)
    return handler


def _build_daily_file_handler(module_name: str, level: int, json_enabled: bool) -> logging.Handler:
    log_dir = BASE_LOG_DIR / module_name
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    if json_enabled:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = LOG_FORMAT_DEBUG if level == logging.DEBUG else LOG_FORMAT
        formatter = logging.Formatter(fmt)
        formatter.converter = time.gmtime
        handler.setFormatter(formatter)
    return handler


def get_module_logger(module_name: str, level=logging.INFO):
    env = os.getenv("ENVIRONMENT", "local").lower()
    json_default = "true" if env in ("prod", "production", "staging") else "false"
    json_enabled = os.getenv("LOG_JSON", json_default).lower() in ("1", "true", "yes")
    today = datetime.now().strftime("%Y-%m-%d")
    logger = logging.getLogger(f"{module_name}-{today}")
    logger.setLevel(level)
    handler = _build_daily_file_handler(module_name, level, json_enabled)
    expected_path = str((BASE_LOG_DIR / module_name / f"{today}.log").resolve())
    if not any(getattr(h, "baseFilename", None) == expected_path for h in logger.handlers if hasattr(h, "baseFilename")):
        logger.addHandler(handler)
    logger.propagate = True
    return logger


def _build_file_handler(log_path: str, level: int, json_enabled: bool, when: str = "midnight", backup_count: int = 14) -> logging.Handler:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    handler = TimedRotatingFileHandler(log_path, when=when, backupCount=backup_count, encoding="utf-8", utc=True)
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    if json_enabled:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = LOG_FORMAT_DEBUG if level == logging.DEBUG else LOG_FORMAT
        formatter = logging.Formatter(fmt)
        formatter.converter = time.gmtime
        handler.setFormatter(formatter)
    return handler


def configure_logging(log_level: Union[str, LogLevels, None] = None) -> None:
    env = os.getenv("ENVIRONMENT", "local").lower()
    json_default = "true" if env in ("prod", "production", "staging") else "false"
    json_enabled = os.getenv("LOG_JSON", json_default).lower() in ("1", "true", "yes")
    level_str = (log_level.value if isinstance(log_level, LogLevels) else str(log_level or os.getenv("LOG_LEVEL", "INFO"))).upper()
    if level_str == "WARN":
        level_str = "WARNING"
    level = getattr(logging, level_str, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(_build_stream_handler(level, json_enabled))
        log_file = os.getenv("LOG_FILE", os.path.join("logs", "app.log"))
        root.addHandler(_build_file_handler(log_file, level, json_enabled))
    else:
        for h in root.handlers:
            h.setLevel(level)
            h.addFilter(RequestIdFilter())
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "python_multipart.multipart", "googleapiclient.discovery"):
        lg = logging.getLogger(name)
        if name in ("python_multipart.multipart", "googleapiclient.discovery"):
            lg.setLevel(logging.WARNING)
        else:
            lg.setLevel(level)
        if not lg.handlers:
            lg.propagate = True
        for h in lg.handlers:
            h.setLevel(level)
            h.addFilter(RequestIdFilter())
    audit = logging.getLogger("audit")
    audit.setLevel(logging.INFO)
    if not audit.handlers:
        audit.addHandler(_build_file_handler(os.getenv("AUDIT_LOG_FILE", os.path.join("logs", "audit.log")), logging.INFO, True))

    # Configure specialized loggers
    _configure_specialized_loggers(level, json_enabled)


def _configure_specialized_loggers(level: int, json_enabled: bool) -> None:
    loggers_config = {
        "subscription":{
            "loggers":["app.services.subscription_service","app.services.stripe_service","app.services.paypal_service"],
        },
        "notifications":{
            "loggers":["app.kafka.producer", "app.kafka.handler", "app.utils.email_utils", "app.utils.teams_utils"],
        },
    }

    today = datetime.now().strftime("%Y-%m-%d")
    for module_name, config in loggers_config.items():
        handler = _build_daily_file_handler(module_name, level, json_enabled)
        target_path = str((BASE_LOG_DIR / module_name / f"{today}.log").resolve())
        for logger_name in config["loggers"]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
            if not any(getattr(h, "baseFilename", None) == target_path for h in logger.handlers if hasattr(h, "baseFilename")):
                logger.addHandler(handler)
            logger.propagate = True
