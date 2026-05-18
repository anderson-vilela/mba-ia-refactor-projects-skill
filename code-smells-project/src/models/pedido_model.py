from typing import Optional

from src.infra.db import get_db


def _row_to_pedido(row) -> dict:
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def _carregar_itens_com_join(pedido_ids: list[int]) -> dict[int, list[dict]]:
    if not pedido_ids:
        return {}
    placeholders = ",".join("?" for _ in pedido_ids)
    rows = get_db().execute(
        f"""
        SELECT ip.pedido_id,
               ip.produto_id,
               ip.quantidade,
               ip.preco_unitario,
               COALESCE(p.nome, 'Desconhecido') AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        pedido_ids,
    ).fetchall()
    agrupados: dict[int, list[dict]] = {pid: [] for pid in pedido_ids}
    for row in rows:
        agrupados[row["pedido_id"]].append({
            "produto_id": row["produto_id"],
            "produto_nome": row["produto_nome"],
            "quantidade": row["quantidade"],
            "preco_unitario": row["preco_unitario"],
        })
    return agrupados


def listar_todos() -> list[dict]:
    rows = get_db().execute("SELECT * FROM pedidos").fetchall()
    pedidos = [_row_to_pedido(row) for row in rows]
    itens_por_pedido = _carregar_itens_com_join([p["id"] for p in pedidos])
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido.get(pedido["id"], [])
    return pedidos


def listar_por_usuario(usuario_id: int) -> list[dict]:
    rows = get_db().execute(
        "SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)
    ).fetchall()
    pedidos = [_row_to_pedido(row) for row in rows]
    itens_por_pedido = _carregar_itens_com_join([p["id"] for p in pedidos])
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido.get(pedido["id"], [])
    return pedidos


def criar(usuario_id: int, itens: list[dict]) -> dict:
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("BEGIN")

        total = 0.0
        produtos_cache: dict[int, dict] = {}
        for item in itens:
            row = cursor.execute(
                "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                (item["produto_id"],),
            ).fetchone()
            if row is None:
                db.rollback()
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if row["estoque"] < item["quantidade"]:
                db.rollback()
                return {"erro": f"Estoque insuficiente para {row['nome']}"}
            produtos_cache[row["id"]] = row
            total += row["preco"] * item["quantidade"]

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            produto = produtos_cache[item["produto_id"]]
            cursor.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": round(total, 2)}
    except Exception:
        db.rollback()
        raise


def atualizar_status(pedido_id: int, novo_status: str) -> Optional[dict]:
    db = get_db()
    cursor = db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
    )
    db.commit()
    if cursor.rowcount == 0:
        return None
    return {"id": pedido_id, "status": novo_status}
