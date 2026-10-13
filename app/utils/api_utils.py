# app/utils/api_utils.py
import logging
from urllib.parse import urlparse
from app.core.config import settings
from app.db.session import SessionLocal
from app.core.exceptions import AppException
from app.core.config import settings
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def handle_onboarding_exception(exc: AppException):
    """
    Simply re-raise; global exception handlers will produce a consistent ErrorResponse.
    """
    raise exc


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False
def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    # Formula: ((x_input_token * INPUT_TOKEN_PRICE) + ( x__output_tokens * OUTPUT_TOKEN_PRICE))/10^6
    price = (input_tokens * settings.INPUT_TOKEN_PRICE) + (output_tokens * settings.OUTPUT_TOKEN_PRICE)
    return price / 1_000_000.0



def calculate_cost_nanobanana(input_tokens: int, output_tokens: int) -> float:
    # Formula: ((x_input_token * INPUT_TOKEN_PRICE) + ( x__output_tokens * OUTPUT_TOKEN_PRICE))/10^6
    price = (input_tokens * settings.NANOBANANA_INPUT_TOKEN_PRICE) + (output_tokens * settings.NANOBANANA_OUTPUT_TOKEN_PRICE)
    return price / 1_000_000.0

def _strip_llm_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_llm_data(v) for k, v in value.items() if k != "llm_data"}
    if isinstance(value, list):
        return [_strip_llm_data(item) for item in value]
    return value