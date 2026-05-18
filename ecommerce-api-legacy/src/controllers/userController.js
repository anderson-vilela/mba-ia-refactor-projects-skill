'use strict';

const { NotFoundError } = require('../middlewares/errorHandler');

function createUserController({ db, userModel, enrollmentModel, paymentModel }) {
    return {
        async deleteUser(req, res, next) {
            try {
                const userId = parseInt(req.params.id, 10);

                await db.runAsync('BEGIN');
                let committed = false;
                try {
                    const enrollmentIds = await enrollmentModel.listIdsByUserId(userId);
                    await paymentModel.deleteByEnrollmentIds(enrollmentIds);
                    await enrollmentModel.deleteByUserId(userId);
                    const removed = await userModel.deleteById(userId);
                    if (removed === 0) {
                        throw new NotFoundError('Usuário não encontrado');
                    }
                    await db.runAsync('COMMIT');
                    committed = true;
                    return res.status(200).json({ msg: 'Usuário e dados relacionados removidos' });
                } catch (innerErr) {
                    if (!committed) {
                        try { await db.runAsync('ROLLBACK'); } catch (_) { /* já abortada */ }
                    }
                    throw innerErr;
                }
            } catch (err) {
                return next(err);
            }
        },
    };
}

module.exports = { createUserController };
