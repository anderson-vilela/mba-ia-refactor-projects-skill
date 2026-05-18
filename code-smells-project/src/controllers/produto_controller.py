from flask import jsonify, request

from src.config.settings import CATEGORIAS_VALIDAS
from src.middlewares.error_handler import NotFoundError, ValidationError
from src.models import produto_model


def _validar_payload(dados: dict, *, exigir_todos: bool = True) -> dict:
    if not dados:
        raise ValidationError("Dados inválidos")

    obrigatorios = ("nome", "preco", "estoque")
    if exigir_todos:
        for campo in obrigatorios:
            if campo not in dados:
                raise ValidationError(f"{campo.capitalize()} é obrigatório")

    nome = dados.get("nome", "")
    descricao = dados.get("descricao", "")
    preco = dados.get("preco", 0)
    estoque = dados.get("estoque", 0)
    categoria = dados.get("categoria", "geral")

    if not isinstance(nome, str) or len(nome) < 2:
        raise ValidationError("Nome muito curto")
    if len(nome) > 200:
        raise ValidationError("Nome muito longo")
    if preco is None or float(preco) < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque is None or int(estoque) < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}"
        )

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": float(preco),
        "estoque": int(estoque),
        "categoria": categoria,
    }


def listar():
    produtos = produto_model.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def detalhar(id: int):
    produto = produto_model.por_id(id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar():
    payload = _validar_payload(request.get_json(silent=True) or {})
    novo_id = produto_model.criar(**payload)
    return jsonify({
        "dados": {"id": novo_id},
        "sucesso": True,
        "mensagem": "Produto criado",
    }), 201


def atualizar(id: int):
    if produto_model.por_id(id) is None:
        raise NotFoundError("Produto não encontrado")
    payload = _validar_payload(request.get_json(silent=True) or {})
    produto_model.atualizar(id, **payload)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(id: int):
    if produto_model.por_id(id) is None:
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")

    preco_min_value = float(preco_min) if preco_min else None
    preco_max_value = float(preco_max) if preco_max else None

    resultados = produto_model.buscar(
        termo=termo or None,
        categoria=categoria,
        preco_min=preco_min_value,
        preco_max=preco_max_value,
    )
    return jsonify({
        "dados": resultados,
        "total": len(resultados),
        "sucesso": True,
    }), 200
