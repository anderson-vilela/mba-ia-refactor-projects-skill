from typing import Optional

from src.infra.db import get_db
from src.infra.security import hash_password, verify_password


_PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")


def _row_to_public_dict(row) -> dict:
    return {field: row[field] for field in _PUBLIC_FIELDS}


def listar() -> list[dict]:
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_row_to_public_dict(row) for row in rows]


def por_id(usuario_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    return _row_to_public_dict(row) if row else None


def criar(nome: str, email: str, senha: str, tipo: str = "cliente") -> int:
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, hash_password(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email: str, senha: str) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if row is None:
        return None
    if not verify_password(senha, row["senha"]):
        return None
    return _row_to_public_dict(row)
