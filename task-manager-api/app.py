import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import settings
from database import db
from middlewares.error_handler import register_error_handlers
from views.routes import register_blueprints


def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    CORS(app, origins=origins if origins != ["*"] else "*")

    db.init_app(app)
    register_blueprints(app)
    register_error_handlers(app)

    @app.route("/health")
    def health():
        from datetime import datetime, timezone
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @app.route("/")
    def index():
        return jsonify({"message": "Task Manager API", "version": "2.0"})

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
