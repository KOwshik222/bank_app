"""
Audit service — immutable audit trail for all consequential actions.
Every important action is recorded here for traceability and compliance.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEntry
from app.schemas.audit import AuditEntryCreate

logger = logging.getLogger(__name__)


class AuditService:
    """Records immutable audit entries for all consequential actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        description: str,
        actor: str = "system",
        actor_type: str = "system",
        incident_id: str | None = None,
        correlation_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        input_data: dict | None = None,
        output_data: dict | None = None,
        evidence: dict | None = None,
        decision: str | None = None,
        status: str = "success",
    ) -> AuditEntry:
        """Create an audit entry."""
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            incident_id=incident_id,
            correlation_id=correlation_id,
            actor=actor,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            input_data=json.dumps(input_data) if input_data else None,
            output_data=json.dumps(output_data) if output_data else None,
            evidence=json.dumps(evidence) if evidence else None,
            decision=decision,
            status=status,
        )
        self.db.add(entry)
        await self.db.flush()

        logger.info(
            f"Audit: [{action}] by {actor} — {description}",
            extra={
                "incident_id": incident_id,
                "correlation_id": correlation_id,
            },
        )
        return entry

    async def get_entries_for_incident(self, incident_id: str) -> list[AuditEntry]:
        """Get all audit entries for an incident, ordered by timestamp."""
        result = await self.db.execute(
            select(AuditEntry)
            .where(AuditEntry.incident_id == incident_id)
            .order_by(AuditEntry.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_entries_by_correlation_id(self, correlation_id: str) -> list[AuditEntry]:
        result = await self.db.execute(
            select(AuditEntry)
            .where(AuditEntry.correlation_id == correlation_id)
            .order_by(AuditEntry.timestamp.asc())
        )
        return list(result.scalars().all())

    async def list_entries(
        self,
        action: str | None = None,
        actor: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditEntry]:
        query = select(AuditEntry).offset(skip).limit(limit).order_by(AuditEntry.timestamp.desc())
        if action:
            query = query.where(AuditEntry.action == action)
        if actor:
            query = query.where(AuditEntry.actor == actor)
        result = await self.db.execute(query)
        return list(result.scalars().all())
