'use strict';

function createReportController({ financialReportModel }) {
    return async function getFinancialReport(_req, res, next) {
        try {
            const report = await financialReportModel.buildReport();
            return res.status(200).json(report);
        } catch (err) {
            return next(err);
        }
    };
}

module.exports = { createReportController };
