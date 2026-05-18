import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.environ.get("SECRET_KEY", "dev-only-change-me-in-prod")
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"
    db_path: str = os.environ.get("DB_PATH", "loja.db")
    host: str = os.environ.get("HOST", "0.0.0.0")
    port: int = int(os.environ.get("PORT", "5000"))
    cors_origins: str = os.environ.get("CORS_ORIGINS", "*")


CATEGORIAS_VALIDAS = (
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
)

STATUS_PEDIDO_VALIDOS = (
    "pendente",
    "aprovado",
    "enviado",
    "entregue",
    "cancelado",
)

FAIXAS_DESCONTO = (
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
)

settings = Settings()
