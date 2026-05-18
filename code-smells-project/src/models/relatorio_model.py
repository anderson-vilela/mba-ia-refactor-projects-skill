from src.config.settings import FAIXAS_DESCONTO
from src.infra.db import get_db


def vendas() -> dict:
    db = get_db()
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
            SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
        """
    ).fetchone()

    total_pedidos = row["total_pedidos"] or 0
    faturamento = float(row["faturamento"] or 0)

    desconto = 0.0
    for limiar, percentual in FAIXAS_DESCONTO:
        if faturamento > limiar:
            desconto = faturamento * percentual
            break

    ticket_medio = round(faturamento / total_pedidos, 2) if total_pedidos else 0

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": row["pendentes"] or 0,
        "pedidos_aprovados": row["aprovados"] or 0,
        "pedidos_cancelados": row["cancelados"] or 0,
        "ticket_medio": ticket_medio,
    }
