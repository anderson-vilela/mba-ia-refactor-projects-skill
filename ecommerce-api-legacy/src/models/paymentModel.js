'use strict';

function createPaymentModel(db) {
    return {
        async create({ enrollmentId, amount, status }) {
            const { lastID } = await db.runWithResult(
                "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
                [enrollmentId, amount, status]
            );
            return { id: lastID, enrollment_id: enrollmentId, amount, status };
        },
        async deleteByEnrollmentIds(ids) {
            if (!ids.length) return 0;
            const placeholders = ids.map(() => '?').join(',');
            const { changes } = await db.runWithResult(
                `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`,
                ids
            );
            return changes;
        },
    };
}

module.exports = { createPaymentModel };
