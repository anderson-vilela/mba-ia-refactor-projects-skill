'use strict';

const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');

function createDatabase() {
    const db = new sqlite3.Database(':memory:');
    db.runAsync = promisify(db.run.bind(db));
    db.getAsync = promisify(db.get.bind(db));
    db.allAsync = promisify(db.all.bind(db));

    db.runWithResult = function (sql, params = []) {
        return new Promise((resolve, reject) => {
            db.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    };

    return db;
}

async function initSchema(db) {
    await db.runAsync(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        pass TEXT
    )`);
    await db.runAsync(`CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        title TEXT,
        price REAL,
        active INTEGER
    )`);
    await db.runAsync(`CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        course_id INTEGER
    )`);
    await db.runAsync(`CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER,
        amount REAL,
        status TEXT
    )`);
    await db.runAsync(`CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT,
        created_at DATETIME
    )`);
}

async function seed(db) {
    const bcrypt = require('bcryptjs');
    const hash = await bcrypt.hash('123', 10);

    await db.runAsync(
        "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
        ['Leonan', 'leonan@fullcycle.com.br', hash]
    );
    await db.runAsync(
        "INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)",
        ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
    );
    await db.runAsync(
        "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
        [1, 1]
    );
    await db.runAsync(
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
        [1, 997.00, 'PAID']
    );
}

async function setupDatabase() {
    const db = createDatabase();
    await initSchema(db);
    await seed(db);
    return db;
}

module.exports = { setupDatabase };
