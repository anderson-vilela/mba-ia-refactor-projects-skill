'use strict';

const express = require('express');

const settings = require('./config/settings');
const { setupDatabase } = require('./infra/db');
const { errorHandler } = require('./middlewares/errorHandler');
const { requestLogger } = require('./middlewares/requestLogger');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createFinancialReportModel } = require('./models/financialReportModel');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { buildRouter } = require('./views/routes');

async function buildApp() {
    const db = await setupDatabase();

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);
    const financialReportModel = createFinancialReportModel(db);

    const checkoutController = createCheckoutController({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
    });
    const reportController = createReportController({ financialReportModel });
    const userController = createUserController({ db, userModel, enrollmentModel, paymentModel });

    const app = express();
    app.use(express.json());
    app.use(requestLogger);
    app.use(buildRouter({ checkoutController, reportController, userController }));
    app.use(errorHandler);

    return { app, db };
}

async function start() {
    const { app } = await buildApp();
    app.listen(settings.port, () => {
        console.log(`LMS API rodando na porta ${settings.port} (env=${settings.nodeEnv})`);
    });
}

if (require.main === module) {
    start().catch((err) => {
        console.error('Falha ao iniciar', err);
        process.exit(1);
    });
}

module.exports = { buildApp };
