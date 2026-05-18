'use strict';

function createAuditLogModel(db) {
    return {
        async record(action) {
            return db.runWithResult(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [action]
            );
        },
    };
}

module.exports = { createAuditLogModel };
