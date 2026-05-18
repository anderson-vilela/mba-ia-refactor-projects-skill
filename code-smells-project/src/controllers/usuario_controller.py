from flask import jsonify, request

from src.middlewares.error_handler import (
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from src.models import usuario_model


def listar():
    return jsonify({"dados": usuario_model.listar(), "sucesso": True}), 200


def detalhar(id: int):
    usuario = usuario_model.por_id(id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar():
    dados = request.get_json(silent=True) or {}
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    novo_id = usuario_model.criar(nome, email, senha)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    dados = request.get_json(silent=True) or {}
    email = dados.get("email", "").strip()
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if usuario is None:
        raise UnauthorizedError("Email ou senha inválidos")

    return jsonify({
        "dados": usuario,
        "sucesso": True,
        "mensagem": "Login OK",
    }), 200
