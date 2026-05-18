import logging
from datetime import datetime

from flask import jsonify, request
from sqlalchemy.orm import selectinload

from config.settings import (
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_TASK_STATUSES,
)
from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User


logger = logging.getLogger(__name__)


def _parse_due_date(raw: str | None) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError as err:
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD") from err


def _serialize_tags(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(value)
    return str(value)


def _validate_title(title: str) -> None:
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("Título é obrigatório")
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")


def _validate_status(status: str) -> None:
    if status not in VALID_TASK_STATUSES:
        raise ValidationError("Status inválido")


def _validate_priority(priority: int) -> None:
    if not isinstance(priority, int) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError(f"Prioridade deve estar entre {MIN_PRIORITY} e {MAX_PRIORITY}")


def _ensure_user_exists(user_id):
    if user_id and User.query.get(user_id) is None:
        raise NotFoundError("Usuário não encontrado")


def _ensure_category_exists(category_id):
    if category_id and Category.query.get(category_id) is None:
        raise NotFoundError("Categoria não encontrada")


def list_tasks():
    tasks = (
        Task.query.options(selectinload(Task.user), selectinload(Task.category))
        .all()
    )
    return jsonify([task.to_dict(expand=True) for task in tasks]), 200


def get_task(task_id: int):
    task = Task.query.get(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    return jsonify(task.to_dict(expand=True)), 200


def create_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    _validate_title(title)

    status = data.get("status", "pending")
    _validate_status(status)
    priority = data.get("priority", 3)
    _validate_priority(priority)

    user_id = data.get("user_id")
    category_id = data.get("category_id")
    _ensure_user_exists(user_id)
    _ensure_category_exists(category_id)

    task = Task()
    task.title = title
    task.description = data.get("description", "")
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id
    task.due_date = _parse_due_date(data.get("due_date"))
    task.tags = _serialize_tags(data.get("tags"))

    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: id=%s title=%s", task.id, task.title)
    return jsonify(task.to_dict(expand=True)), 201


def update_task(task_id: int):
    task = Task.query.get(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")

    data = request.get_json(silent=True) or {}
    if not data:
        raise ValidationError("Dados inválidos")

    if "title" in data:
        _validate_title(data["title"])
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        _validate_status(data["status"])
        task.status = data["status"]
    if "priority" in data:
        _validate_priority(data["priority"])
        task.priority = data["priority"]
    if "user_id" in data:
        _ensure_user_exists(data["user_id"])
        task.user_id = data["user_id"]
    if "category_id" in data:
        _ensure_category_exists(data["category_id"])
        task.category_id = data["category_id"]
    if "due_date" in data:
        task.due_date = _parse_due_date(data["due_date"])
    if "tags" in data:
        task.tags = _serialize_tags(data["tags"])

    db.session.commit()
    return jsonify(task.to_dict(expand=True)), 200


def delete_task(task_id: int):
    task = Task.query.get(task_id)
    if task is None:
        raise NotFoundError("Task não encontrada")
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deletada com sucesso"}), 200


def search_tasks():
    args = request.args
    query = Task.query
    if args.get("q"):
        like = f"%{args['q']}%"
        query = query.filter(db.or_(Task.title.like(like), Task.description.like(like)))
    if args.get("status"):
        query = query.filter(Task.status == args["status"])
    if args.get("priority"):
        try:
            query = query.filter(Task.priority == int(args["priority"]))
        except ValueError as err:
            raise ValidationError("Prioridade deve ser numérica") from err
    if args.get("user_id"):
        try:
            query = query.filter(Task.user_id == int(args["user_id"]))
        except ValueError as err:
            raise ValidationError("user_id deve ser numérico") from err

    return jsonify([task.to_dict() for task in query.all()]), 200


def task_stats():
    counts = dict(
        db.session.query(Task.status, db.func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    total = sum(counts.values())
    overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
    done = counts.get("done", 0)
    return jsonify({
        "total": total,
        "pending": counts.get("pending", 0),
        "in_progress": counts.get("in_progress", 0),
        "done": done,
        "cancelled": counts.get("cancelled", 0),
        "overdue": overdue_count,
        "completion_rate": round((done / total) * 100, 2) if total else 0,
    }), 200
