"""
Audit model — immutable audit trail for all consequential actions.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), index=True
    )
    incident_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    actor: Mapped[str] = mapped_column(String(100))  # user or agent name
    actor_type: Mapped[str] = mapped_column(String(20))  # "user", "agent", "system"
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failure, pending

    def __repr__(self) -> str:
        return f"<AuditEntry [{self.action}] by {self.actor} at {self.timestamp}>"
