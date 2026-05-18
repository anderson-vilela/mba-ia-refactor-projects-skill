from typing import Optional

from src.infra.db import get_db


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar() -> list[dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM produtos").fetchall()
    return [_row_to_dict(row) for row in rows]


def por_id(produto_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def criar(nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(
    produto_id: int,
    nome: str,
    descricao: str,
    preco: float,
    estoque: int,
    categoria: str,
) -> None:
    db = get_db()
    db.execute(
        """
        UPDATE produtos
        SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
        WHERE id = ?
        """,
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar(
    termo: str | None = None,
    categoria: str | None = None,
    preco_min: float | None = None,
    preco_max: float | None = None,
) -> list[dict]:
    sql = "SELECT * FROM produtos WHERE 1=1"
    params: list = []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        sql += " AND preco <= ?"
        params.append(preco_max)
    rows = get_db().execute(sql, params).fetchall()
    return [_row_to_dict(row) for row in rows]
