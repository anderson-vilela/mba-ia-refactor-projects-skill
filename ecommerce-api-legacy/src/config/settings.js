'use strict';

require('dotenv').config({ quiet: true });

module.exports = {
    port: parseInt(process.env.PORT || '3000', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    smtpUser: process.env.SMTP_USER || '',
    dbUser: process.env.DB_USER || '',
    dbPass: process.env.DB_PASS || '',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '10', 10),
};
