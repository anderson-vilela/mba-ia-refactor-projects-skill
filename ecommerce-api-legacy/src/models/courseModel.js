'use strict';

function createCourseModel(db) {
    return {
        async findActiveById(id) {
            return db.getAsync(
                "SELECT id, title, price FROM courses WHERE id = ? AND active = 1",
                [id]
            );
        },
        async listAll() {
            return db.allAsync("SELECT id, title, price, active FROM courses");
        },
    };
}

module.exports = { createCourseModel };
