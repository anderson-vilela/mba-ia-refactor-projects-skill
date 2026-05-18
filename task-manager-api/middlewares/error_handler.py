import logging

from flask import jsonify


logger = logging.getLogger(__name__)


class BusinessError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class ValidationError(BusinessError):
    status_code = 400


class NotFoundError(BusinessError):
    status_code = 404


class ConflictError(BusinessError):
    status_code = 409


class UnauthorizedError(BusinessError):
    status_code = 401


class ForbiddenError(BusinessError):
    status_code = 403


def register_error_handlers(app) -> None:
    @app.errorhandler(BusinessError)
    def _handle_business(error: BusinessError):
        return jsonify({"error": str(error)}), error.status_code

    @app.errorhandler(404)
    def _handle_not_found(_error):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def _handle_generic(error: Exception):
        logger.exception("Erro não tratado: %s", error)
        return jsonify({"error": "Erro interno do servidor"}), 500
