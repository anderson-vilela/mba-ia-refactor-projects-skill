from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp


def register_blueprints(app) -> None:
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
