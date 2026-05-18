"""Helpers genéricos. Validações específicas de domínio vivem em controllers."""

import logging
import re
import uuid
from datetime import datetime


logger = logging.getLogger(__name__)


_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def format_date(date_obj) -> str | None:
    if date_obj is None:
        return None
    return str(date_obj)


def calculate_percentage(part: float, total: float) -> float:
    if not total:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email: str) -> bool:
    return bool(email) and bool(_EMAIL_PATTERN.match(email))


def sanitize_string(value: str | None) -> str | None:
    if not value:
        return value
    return value.strip()


def generate_id() -> str:
    return str(uuid.uuid4())


def log_action(action: str, details: dict | None = None) -> None:
    if details:
        logger.info("ACTION %s details=%s", action, details)
    else:
        logger.info("ACTION %s", action)


def parse_date(raw: str | None):
    if not raw:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def is_valid_color(color: str | None) -> bool:
    return bool(color) and len(color) == 7 and color[0] == "#"
