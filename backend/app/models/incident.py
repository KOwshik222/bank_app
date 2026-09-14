"""
Incident model — full incident lifecycle with investigation state.
This is the core domain model for the AI agent platform.
"""

import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class IncidentSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    REMEDIATING = "REMEDIATING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"


class IncidentCategory(str, enum.Enum):
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    APPLICATION = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    SECURITY = "SECURITY"
    DEPLOYMENT = "DEPLOYMENT"
    THIRD_PARTY = "THIRD_PARTY"
    UNKNOWN = "UNKNOWN"


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity))
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), default=IncidentStatus.OPEN, index=True
    )
    category: Mapped[IncidentCategory] = mapped_column(
        Enum(IncidentCategory), default=IncidentCategory.UNKNOWN
    )
    affected_service: Mapped[str] = mapped_column(String(100))
    reported_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    correlation_id: Mapped[str] = mapped_column(
        String(36), default=lambda: str(uuid4()), index=True
    )

    # AI Investigation fields
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval fields
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    evidence_items = relationship(
        "Evidence", back_populates="incident", lazy="selectin", cascade="all, delete-orphan"
    )
    investigation_steps = relationship(
        "InvestigationStep",
        back_populates="incident",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="InvestigationStep.step_order",
    )

    def __repr__(self) -> str:
        return f"<Incident {self.incident_number} [{self.severity.value}] {self.status.value}>"

    def resolve(self) -> None:
        """Mark incident as resolved."""
        now = datetime.now(timezone.utc)
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = now
        if self.created_at:
            created = self.created_at
            if created.tzinfo is None and now.tzinfo is not None:
                created = created.replace(tzinfo=timezone.utc)
            elif created.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            self.resolution_time_seconds = max(1, int((now - created).total_seconds()))

    def reopen(self, reason: str) -> None:
        """Reopen a resolved incident."""
        self.status = IncidentStatus.REOPENED
        self.resolved_at = None
        self.resolution_time_seconds = None
        self.resolution_notes = f"Reopened: {reason}"


class Evidence(Base, TimestampMixin):
    """Evidence collected during AI investigation."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    source_agent: Mapped[str] = mapped_column(String(50))  # e.g., "log_analysis", "db_analysis"
    evidence_type: Mapped[str] = mapped_column(String(50))  # e.g., "log_entry", "metric", "config"
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-serialized raw data

    # Relationships
    incident = relationship("Incident", back_populates="evidence_items")

    def __repr__(self) -> str:
        return f"<Evidence [{self.source_agent}] {self.title}>"


class InvestigationStep(Base, TimestampMixin):
    """Tracks each step the AI takes during investigation."""

    __tablename__ = "investigation_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    agent_name: Mapped[str] = mapped_column(String(50))
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="investigation_steps")

    def __repr__(self) -> str:
        return f"<InvestigationStep #{self.step_order} [{self.agent_name}] {self.status}>"
