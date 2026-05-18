'use strict';

function createFinancialReportModel(db) {
    return {
        async buildReport() {
            const rows = await db.allAsync(`
                SELECT
                    c.id     AS course_id,
                    c.title  AS course_title,
                    e.id     AS enrollment_id,
                    u.name   AS user_name,
                    u.email  AS user_email,
                    p.amount AS payment_amount,
                    p.status AS payment_status
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                LEFT JOIN users u ON u.id = e.user_id
                LEFT JOIN payments p ON p.enrollment_id = e.id
                ORDER BY c.id, e.id
            `);

            const byCourse = new Map();
            for (const row of rows) {
                if (!byCourse.has(row.course_id)) {
                    byCourse.set(row.course_id, {
                        course: row.course_title,
                        revenue: 0,
                        students: [],
                    });
                }
                const courseData = byCourse.get(row.course_id);

                if (row.enrollment_id == null) continue;

                if (row.payment_status === 'PAID' && row.payment_amount) {
                    courseData.revenue += row.payment_amount;
                }
                courseData.students.push({
                    student: row.user_name || 'Unknown',
                    paid: row.payment_amount || 0,
                });
            }
            return Array.from(byCourse.values());
        },
    };
}

module.exports = { createFinancialReportModel };
