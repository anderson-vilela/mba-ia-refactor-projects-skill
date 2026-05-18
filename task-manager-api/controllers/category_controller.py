from flask import jsonify, request

from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task


def list_categories():
    categories = Category.query.all()
    payload = []
    for cat in categories:
        data = cat.to_dict()
        data["task_count"] = Task.query.filter_by(category_id=cat.id).count()
        payload.append(data)
    return jsonify(payload), 200


def create_category():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationError("Nome é obrigatório")

    category = Category()
    category.name = name
    category.description = data.get("description", "")
    category.color = data.get("color") or "#000000"

    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


def update_category(cat_id: int):
    category = Category.query.get(cat_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada")

    data = request.get_json(silent=True) or {}
    if "name" in data:
        category.name = data["name"]
    if "description" in data:
        category.description = data["description"]
    if "color" in data:
        category.color = data["color"]

    db.session.commit()
    return jsonify(category.to_dict()), 200


def delete_category(cat_id: int):
    category = Category.query.get(cat_id)
    if category is None:
        raise NotFoundError("Categoria não encontrada")
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Categoria deletada"}), 200
