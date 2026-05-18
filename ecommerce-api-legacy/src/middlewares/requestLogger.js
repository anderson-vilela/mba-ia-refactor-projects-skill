'use strict';

function requestLogger(req, _res, next) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.path}`);
    next();
}

module.exports = { requestLogger };
