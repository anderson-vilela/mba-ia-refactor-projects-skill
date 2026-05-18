import logging
import re

from flask import jsonify, request

from config.settings import MIN_PASSWORD_LENGTH, VALID_USER_ROLES
from database import db
from infra.jwt_service import issue_token
from middlewares.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.task import Task
from models.user import User


logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def _validate_email(email: str) -> None:
    if not _EMAIL_PATTERN.match(email or ""):
        raise ValidationError("Email inválido")


def list_users():
    users = User.query.all()
    payload = []
    for user in users:
        data = user.to_dict()
        data["task_count"] = len(user.tasks)
        payload.append(data)
    return jsonify(payload), 200


def get_user(user_id: int):
    user = User.query.get(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    data = user.to_dict()
    data["tasks"] = [task.to_dict() for task in user.tasks]
    return jsonify(data), 200


def create_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "user")

    if not name:
        raise ValidationError("Nome é obrigatório")
    _validate_email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres"
        )
    if role not in VALID_USER_ROLES:
        raise ValidationError("Role inválido")
    if User.query.filter_by(email=email).first():
        raise ConflictError("Email já cadastrado")

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()
    logger.info("Usuário criado: id=%s email=%s", user.id, user.email)
    return jsonify(user.to_dict()), 201


def update_user(user_id: int):
    user = User.query.get(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")

    data = request.get_json(silent=True) or {}
    if not data:
        raise ValidationError("Dados inválidos")

    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        _validate_email(data["email"])
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            raise ConflictError("Email já cadastrado")
        user.email = data["email"]
    if "password" in data:
        if len(data["password"]) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        user.set_password(data["password"])
    if "role" in data:
        if data["role"] not in VALID_USER_ROLES:
            raise ValidationError("Role inválido")
        user.role = data["role"]
    if "active" in data:
        user.active = bool(data["active"])

    db.session.commit()
    return jsonify(user.to_dict()), 200


def delete_user(user_id: int):
    user = User.query.get(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")

    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    logger.info("Usuário deletado: %s", user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200


def get_user_tasks(user_id: int):
    user = User.query.get(user_id)
    if user is None:
        raise NotFoundError("Usuário não encontrado")
    return jsonify([task.to_dict() for task in user.tasks]), 200


def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        raise UnauthorizedError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    return jsonify({
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": issue_token(user.id, user.role),
    }), 200
