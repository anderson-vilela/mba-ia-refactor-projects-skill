'use strict';

function createUserModel(db) {
    return {
        async findByEmail(email) {
            return db.getAsync("SELECT id, name, email, pass FROM users WHERE email = ?", [email]);
        },
        async create({ name, email, passwordHash }) {
            const { lastID } = await db.runWithResult(
                "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
                [name, email, passwordHash]
            );
            return { id: lastID, name, email };
        },
        async deleteById(id) {
            const { changes } = await db.runWithResult("DELETE FROM users WHERE id = ?", [id]);
            return changes;
        },
    };
}

module.exports = { createUserModel };
