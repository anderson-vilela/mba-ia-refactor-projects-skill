'use strict';

const { paymentGatewayKey } = require('../config/settings');
const { hashPassword, maskCard } = require('../infra/crypto');
const {
    NotFoundError,
    UnauthorizedError,
    ValidationError,
} = require('../middlewares/errorHandler');

function authorizePayment(card) {
    return card && card.startsWith('4') ? 'PAID' : 'DENIED';
}

function createCheckoutController({
    db,
    userModel,
    courseModel,
    enrollmentModel,
    paymentModel,
    auditLogModel,
}) {
    return async function checkout(req, res, next) {
        try {
            const { usr: name, eml: email, pwd: password, c_id: courseId, card } = req.body;

            if (!name || !email || !courseId || !card) {
                throw new ValidationError('Bad Request: campos obrigatórios ausentes');
            }

            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            let user = await userModel.findByEmail(email);
            if (!user) {
                const passwordHash = await hashPassword(password || '123456');
                user = await userModel.create({ name, email, passwordHash });
            }

            console.log(
                `Processando cartão ${maskCard(card)} (gateway=${paymentGatewayKey ? 'configurado' : 'sem-key'})`
            );

            const paymentStatus = authorizePayment(card);
            if (paymentStatus === 'DENIED') {
                throw new UnauthorizedError('Pagamento recusado');
            }

            await db.runAsync('BEGIN');
            try {
                const enrollment = await enrollmentModel.create(user.id, courseId);
                await paymentModel.create({
                    enrollmentId: enrollment.id,
                    amount: course.price,
                    status: paymentStatus,
                });
                await auditLogModel.record(`Checkout curso ${courseId} por ${user.id}`);
                await db.runAsync('COMMIT');

                return res.status(200).json({
                    msg: 'Sucesso',
                    enrollment_id: enrollment.id,
                });
            } catch (innerErr) {
                await db.runAsync('ROLLBACK');
                throw innerErr;
            }
        } catch (err) {
            return next(err);
        }
    };
}

module.exports = { createCheckoutController };
