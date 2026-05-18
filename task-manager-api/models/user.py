from datetime import datetime, timezone

from database import db
from infra.security import hash_password, verify_password


def _now_utc():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_now_utc)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "created_at": str(self.created_at),
        }

    def set_password(self, plain: str) -> None:
        self.password = hash_password(plain)

    def check_password(self, plain: str) -> bool:
        return verify_password(plain, self.password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
