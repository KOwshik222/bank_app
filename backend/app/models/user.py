"""
User & Role models for authentication and RBAC.
"""

import enum
from uuid import uuid4

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    SUPPORT_ENGINEER = "SUPPORT_ENGINEER"
    INCIDENT_MANAGER = "INCIDENT_MANAGER"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.SUPPORT_ENGINEER)
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role.value}>"
