'use strict';

const bcrypt = require('bcryptjs');
const { bcryptRounds } = require('../config/settings');

async function hashPassword(plain) {
    return bcrypt.hash(plain || '', bcryptRounds);
}

async function verifyPassword(plain, hashed) {
    if (!hashed) return false;
    return bcrypt.compare(plain || '', hashed);
}

function maskCard(card) {
    if (!card || card.length < 4) return '****';
    return `****-****-****-${card.slice(-4)}`;
}

module.exports = { hashPassword, verifyPassword, maskCard };
