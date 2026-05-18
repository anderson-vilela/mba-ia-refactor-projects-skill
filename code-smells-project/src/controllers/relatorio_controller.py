from flask import jsonify

from src.infra.db import get_db
from src.models import relatorio_model


def vendas():
    return jsonify({"dados": relatorio_model.vendas(), "sucesso": True}), 200


def health_check():
    db = get_db()
    try:
        db.execute("SELECT 1").fetchone()
        produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    except Exception as err:
        return jsonify({"status": "erro", "detalhes": str(err)}), 500

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos,
        },
        "versao": "2.0.0",
    }), 200


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "2.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    }), 200
