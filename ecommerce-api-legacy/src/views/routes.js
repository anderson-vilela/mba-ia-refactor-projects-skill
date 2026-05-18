'use strict';

const { Router } = require('express');

function buildRouter({ checkoutController, reportController, userController }) {
    const router = Router();

    router.post('/api/checkout', checkoutController);
    router.get('/api/admin/financial-report', reportController);
    router.delete('/api/users/:id', userController.deleteUser);

    router.get('/health', (_req, res) => res.json({ status: 'ok' }));
    router.get('/', (_req, res) => res.json({
        message: 'LMS API',
        version: '2.0.0',
        endpoints: {
            checkout: 'POST /api/checkout',
            report: 'GET /api/admin/financial-report',
            deleteUser: 'DELETE /api/users/:id',
        },
    }));

    return router;
}

module.exports = { buildRouter };
