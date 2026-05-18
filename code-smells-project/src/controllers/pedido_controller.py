import logging

from flask import jsonify, request

from src.config.settings import STATUS_PEDIDO_VALIDOS
from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models import pedido_model


logger = logging.getLogger(__name__)


def _notificar_pedido_criado(usuario_id: int, pedido_id: int) -> None:
    logger.info("Pedido %s criado para usuário %s", pedido_id, usuario_id)


def _notificar_mudanca_de_status(pedido_id: int, novo_status: str) -> None:
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)


def criar():
    dados = request.get_json(silent=True) or {}
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        raise ValidationError(resultado["erro"])

    _notificar_pedido_criado(usuario_id, resultado["pedido_id"])
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def listar_por_usuario(usuario_id: int):
    pedidos = pedido_model.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos():
    return jsonify({"dados": pedido_model.listar_todos(), "sucesso": True}), 200


def atualizar_status(pedido_id: int):
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")

    atualizado = pedido_model.atualizar_status(pedido_id, novo_status)
    if atualizado is None:
        raise NotFoundError("Pedido não encontrado")

    _notificar_mudanca_de_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
