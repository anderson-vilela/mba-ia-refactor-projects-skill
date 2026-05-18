'use strict';

function createEnrollmentModel(db) {
    return {
        async create(userId, courseId) {
            const { lastID } = await db.runWithResult(
                "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
                [userId, courseId]
            );
            return { id: lastID, user_id: userId, course_id: courseId };
        },
        async deleteByUserId(userId) {
            const { changes } = await db.runWithResult(
                "DELETE FROM enrollments WHERE user_id = ?",
                [userId]
            );
            return changes;
        },
        async listIdsByUserId(userId) {
            const rows = await db.allAsync(
                "SELECT id FROM enrollments WHERE user_id = ?",
                [userId]
            );
            return rows.map((row) => row.id);
        },
    };
}

module.exports = { createEnrollmentModel };
