'use strict';

class BusinessError extends Error {
    constructor(message, statusCode = 400) {
        super(message);
        this.statusCode = statusCode;
        this.name = this.constructor.name;
    }
}

class NotFoundError extends BusinessError {
    constructor(message = 'Recurso não encontrado') { super(message, 404); }
}

class UnauthorizedError extends BusinessError {
    constructor(message = 'Não autorizado') { super(message, 401); }
}

class ValidationError extends BusinessError {
    constructor(message = 'Dados inválidos') { super(message, 400); }
}

function errorHandler(err, _req, res, _next) {
    if (err instanceof BusinessError) {
        return res.status(err.statusCode).json({ error: err.message });
    }
    console.error('[ERROR]', err.stack || err.message);
    return res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = { BusinessError, NotFoundError, UnauthorizedError, ValidationError, errorHandler };
