import logging

from flask import jsonify


logger = logging.getLogger(__name__)


class BusinessError(Exception):
    status_code = 400


class ValidationError(BusinessError):
    status_code = 400


class NotFoundError(BusinessError):
    status_code = 404


class UnauthorizedError(BusinessError):
    status_code = 401


def register_error_handlers(app) -> None:
    @app.errorhandler(BusinessError)
    def _handle_business(error: BusinessError):
        return (
            jsonify({"erro": str(error), "sucesso": False}),
            error.status_code,
        )

    @app.errorhandler(404)
    def _handle_not_found(_error):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def _handle_generic(error: Exception):
        logger.exception("Erro não tratado: %s", error)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
