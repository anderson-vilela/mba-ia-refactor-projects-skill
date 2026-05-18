import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.environ.get("SECRET_KEY", "dev-only-change-me-in-prod")
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    database_uri: str = os.environ.get(
        "DATABASE_URI", "sqlite:///tasks.db"
    )
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "5000"))
    cors_origins: str = os.environ.get("CORS_ORIGINS", "*")
    jwt_expiration_seconds: int = int(os.environ.get("JWT_EXPIRATION", "3600"))
    smtp_host: str = os.environ.get("SMTP_HOST", "")
    smtp_port: int = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user: str = os.environ.get("SMTP_USER", "")
    smtp_password: str = os.environ.get("SMTP_PASSWORD", "")


VALID_TASK_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_USER_ROLES = ("user", "admin", "manager")
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_COLOR = "#000000"

settings = Settings()
