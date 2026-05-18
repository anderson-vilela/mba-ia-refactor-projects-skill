import logging
import smtplib
from datetime import datetime, timezone

from config.settings import settings


logger = logging.getLogger(__name__)


class NotificationService:
    """Encapsula envio de notificações por email.

    As credenciais SMTP vêm de variáveis de ambiente (config.settings).
    Notificações ficam em log estruturado.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.user = user or settings.smtp_user
        self.password = password or settings.smtp_password

    def _can_send(self) -> bool:
        return bool(self.host and self.user and self.password)

    def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self._can_send():
            logger.info(
                "[NotificationService] SMTP não configurado — pulando envio para %s", to
            )
            return False
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as server:
                server.starttls()
                server.login(self.user, self.password)
                message = f"From: {self.user}\nTo: {to}\nSubject: {subject}\n\n{body}"
                server.sendmail(self.user, to, message)
            logger.info("Email enviado para %s", to)
            return True
        except Exception:
            logger.exception("Erro ao enviar email para %s", to)
            return False

    def notify_task_assigned(self, user, task) -> None:
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)

    def notify_task_overdue(self, user, task) -> None:
        subject = f"Task atrasada: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n"
            f"Data limite: {task.due_date}\n"
            f"Notificado em: {datetime.now(timezone.utc).isoformat()}"
        )
        self.send_email(user.email, subject, body)
