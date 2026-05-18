import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import settings
from src.infra.db import register_db
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_routes


def create_app() -> Flask:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    CORS(app, origins=origins if origins != ["*"] else "*")

    register_db(app)
    register_error_handlers(app)
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
