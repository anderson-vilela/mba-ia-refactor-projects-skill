from datetime import datetime, timedelta, timezone

from flask import jsonify
from sqlalchemy.orm import selectinload

from database import db
from models.category import Category
from models.task import Task
from models.user import User


def _now_naive_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary_report():
    now_utc = _now_naive_utc()
    seven_days_ago = now_utc - timedelta(days=7)

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = dict(
        db.session.query(Task.status, db.func.count(Task.id))
        .group_by(Task.status)
        .all()
    )
    priority_counts = dict(
        db.session.query(Task.priority, db.func.count(Task.id))
        .group_by(Task.priority)
        .all()
    )

    overdue_list = []
    for task in Task.query.filter(Task.due_date.isnot(None)).all():
        if task.is_overdue():
            overdue_list.append({
                "id": task.id,
                "title": task.title,
                "due_date": str(task.due_date),
                "days_overdue": (now_utc - task.due_date).days,
            })

    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == "done", Task.updated_at >= seven_days_ago
    ).count()

    user_stats = []
    users = User.query.options(selectinload(User.tasks)).all()
    for user in users:
        total = len(user.tasks)
        completed = sum(1 for t in user.tasks if t.status == "done")
        user_stats.append({
            "user_id": user.id,
            "user_name": user.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": round((completed / total) * 100, 2) if total else 0,
        })

    return jsonify({
        "generated_at": str(now_utc),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": status_counts.get("pending", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "done": status_counts.get("done", 0),
            "cancelled": status_counts.get("cancelled", 0),
        },
        "tasks_by_priority": {
            "critical": priority_counts.get(1, 0),
            "high": priority_counts.get(2, 0),
            "medium": priority_counts.get(3, 0),
            "low": priority_counts.get(4, 0),
            "minimal": priority_counts.get(5, 0),
        },
        "overdue": {
            "count": len(overdue_list),
            "tasks": overdue_list,
        },
        "recent_activity": {
            "tasks_created_last_7_days": recent_tasks,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }), 200


def user_report(user_id: int):
    from middlewares.error_handler import NotFoundError

    user = User.query.options(selectinload(User.tasks)).filter_by(id=user_id).first()
    if user is None:
        raise NotFoundError("Usuário não encontrado")

    tasks = list(user.tasks)
    total = len(tasks)
    done = sum(1 for t in tasks if t.status == "done")
    pending = sum(1 for t in tasks if t.status == "pending")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")
    cancelled = sum(1 for t in tasks if t.status == "cancelled")
    overdue = sum(1 for t in tasks if t.is_overdue())
    high_priority = sum(1 for t in tasks if t.priority and t.priority <= 2)

    return jsonify({
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": pending,
            "in_progress": in_progress,
            "cancelled": cancelled,
            "overdue": overdue,
            "high_priority": high_priority,
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        },
    }), 200
