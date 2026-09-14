"""
Incident service — full incident lifecycle management.
State machine: OPEN → INVESTIGATING → AWAITING_APPROVAL → REMEDIATING → VERIFYING → RESOLVED/REOPENED
"""

import logging
import random
import string
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident import (
    Evidence,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    InvestigationStep,
)
from app.schemas.incident import DashboardStats, IncidentCreate

logger = logging.getLogger(__name__)

# Valid state transitions
VALID_TRANSITIONS: dict[IncidentStatus, set[IncidentStatus]] = {
    IncidentStatus.OPEN: {IncidentStatus.INVESTIGATING},
    IncidentStatus.INVESTIGATING: {IncidentStatus.AWAITING_APPROVAL, IncidentStatus.OPEN},
    IncidentStatus.AWAITING_APPROVAL: {
        IncidentStatus.REMEDIATING,
        IncidentStatus.INVESTIGATING,
        IncidentStatus.OPEN,
    },
    IncidentStatus.REMEDIATING: {IncidentStatus.VERIFYING},
    IncidentStatus.VERIFYING: {IncidentStatus.RESOLVED, IncidentStatus.REOPENED},
    IncidentStatus.RESOLVED: {IncidentStatus.CLOSED, IncidentStatus.REOPENED},
    IncidentStatus.REOPENED: {IncidentStatus.INVESTIGATING},
    IncidentStatus.CLOSED: set(),
}


class IncidentService:
    """Manages the complete incident lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _generate_incident_number() -> str:
        num = random.randint(10000, 99999)
        return f"INC-{num}"

    # ── CRUD ─────────────────────────────────────────────────────

    async def create_incident(self, data: IncidentCreate) -> Incident:
        incident = Incident(
            incident_number=self._generate_incident_number(),
            title=data.title,
            description=data.description,
            severity=IncidentSeverity(data.severity),
            category=IncidentCategory(data.category),
            affected_service=data.affected_service,
            reported_by=data.reported_by,
            status=IncidentStatus.OPEN,
        )
        self.db.add(incident)
        await self.db.flush()
        logger.info(
            f"Incident created: {incident.incident_number} [{incident.severity.value}] "
            f"service={incident.affected_service}"
        )
        # Re-fetch with eager loading for response serialization
        return await self.get_incident(incident.id)

    async def get_incident(self, incident_id: str) -> Incident | None:
        result = await self.db.execute(
            select(Incident)
            .where(Incident.id == incident_id)
            .execution_options(populate_existing=True)
            .options(selectinload(Incident.evidence_items), selectinload(Incident.investigation_steps))
        )
        return result.scalar_one_or_none()

    async def get_incident_by_number(self, incident_number: str) -> Incident | None:
        result = await self.db.execute(
            select(Incident).where(Incident.incident_number == incident_number)
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        service: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Incident]:
        query = (
            select(Incident)
            .options(selectinload(Incident.evidence_items), selectinload(Incident.investigation_steps))
            .offset(skip).limit(limit).order_by(Incident.created_at.desc())
        )
        if status:
            query = query.where(Incident.status == IncidentStatus(status))
        if severity:
            query = query.where(Incident.severity == IncidentSeverity(severity))
        if service:
            query = query.where(Incident.affected_service == service)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── State Transitions ────────────────────────────────────────

    async def transition_status(
        self, incident_id: str, new_status: IncidentStatus, reason: str | None = None
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        current = incident.status
        if new_status not in VALID_TRANSITIONS.get(current, set()):
            raise ValueError(
                f"Invalid transition: {current.value} → {new_status.value}. "
                f"Valid transitions: {[s.value for s in VALID_TRANSITIONS.get(current, set())]}"
            )

        incident.status = new_status

        if new_status == IncidentStatus.RESOLVED:
            incident.resolve()
        elif new_status == IncidentStatus.REOPENED:
            incident.reopen(reason or "Verification failed")

        await self.db.flush()
        logger.info(
            f"Incident {incident.incident_number}: {current.value} → {new_status.value}"
        )
        return incident

    # ── Approval ─────────────────────────────────────────────────

    async def approve_remediation(self, incident_id: str, approved_by: str) -> Incident:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        if incident.status != IncidentStatus.AWAITING_APPROVAL:
            raise ValueError(f"Incident not awaiting approval: {incident.status.value}")

        incident.approved_by = approved_by
        incident.approved_at = datetime.now(timezone.utc)
        incident.status = IncidentStatus.REMEDIATING
        await self.db.flush()

        logger.info(f"Remediation approved for {incident.incident_number} by {approved_by}")
        return incident

    async def reject_remediation(
        self, incident_id: str, rejected_by: str, reason: str
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")
        if incident.status != IncidentStatus.AWAITING_APPROVAL:
            raise ValueError(f"Incident not awaiting approval: {incident.status.value}")

        incident.rejection_reason = reason
        incident.status = IncidentStatus.OPEN
        await self.db.flush()

        logger.info(
            f"Remediation rejected for {incident.incident_number} by {rejected_by}: {reason}"
        )
        return incident

    async def request_more_investigation(self, incident_id: str) -> Incident:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.status = IncidentStatus.INVESTIGATING
        await self.db.flush()
        return incident

    # ── Evidence ─────────────────────────────────────────────────

    async def add_evidence(
        self,
        incident_id: str,
        source_agent: str,
        evidence_type: str,
        title: str,
        content: str,
        severity: str | None = None,
        confidence: float | None = None,
        raw_data: str | None = None,
    ) -> Evidence:
        evidence = Evidence(
            incident_id=incident_id,
            source_agent=source_agent,
            evidence_type=evidence_type,
            title=title,
            content=content,
            severity=severity,
            confidence=confidence,
            raw_data=raw_data,
        )
        self.db.add(evidence)
        await self.db.flush()
        return evidence

    # ── Investigation Steps ──────────────────────────────────────

    async def add_investigation_step(
        self,
        incident_id: str,
        step_order: int,
        agent_name: str,
        description: str,
        tool_name: str | None = None,
    ) -> InvestigationStep:
        step = InvestigationStep(
            incident_id=incident_id,
            step_order=step_order,
            agent_name=agent_name,
            tool_name=tool_name,
            description=description,
            status="pending",
        )
        self.db.add(step)
        await self.db.flush()
        return step

    async def update_investigation_step(
        self,
        step_id: str,
        status: str,
        result_summary: str | None = None,
        duration_ms: int | None = None,
    ) -> InvestigationStep:
        result = await self.db.execute(
            select(InvestigationStep).where(InvestigationStep.id == step_id)
        )
        step = result.scalar_one_or_none()
        if not step:
            raise ValueError(f"Investigation step not found: {step_id}")

        step.status = status
        if status == "running":
            step.started_at = datetime.now(timezone.utc)
        elif status in ("completed", "failed"):
            step.completed_at = datetime.now(timezone.utc)
        if result_summary:
            step.result_summary = result_summary
        if duration_ms is not None:
            step.duration_ms = duration_ms

        await self.db.flush()
        return step

    # ── RCA Update ───────────────────────────────────────────────

    async def update_rca(
        self,
        incident_id: str,
        root_cause: str,
        confidence: float,
        remediation: str,
        risk: str,
        summary: str,
    ) -> Incident:
        incident = await self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        incident.root_cause = root_cause
        incident.root_cause_confidence = confidence
        incident.recommended_remediation = remediation
        incident.remediation_risk = risk
        incident.ai_summary = summary
        incident.status = IncidentStatus.AWAITING_APPROVAL
        await self.db.flush()
        return incident

    # ── Dashboard Stats ──────────────────────────────────────────

    async def get_dashboard_stats(self) -> DashboardStats:
        all_incidents = await self.db.execute(select(Incident))
        incidents = list(all_incidents.scalars().all())

        if not incidents:
            return DashboardStats()

        by_status: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_service: dict[str, int] = {}
        resolution_times: list[int] = []

        for inc in incidents:
            by_status[inc.status.value] = by_status.get(inc.status.value, 0) + 1
            by_severity[inc.severity.value] = by_severity.get(inc.severity.value, 0) + 1
            by_service[inc.affected_service] = by_service.get(inc.affected_service, 0) + 1
            if inc.resolution_time_seconds:
                resolution_times.append(inc.resolution_time_seconds)

        resolved_count = by_status.get("RESOLVED", 0) + by_status.get("CLOSED", 0)
        total = len(incidents)
        ai_success = (resolved_count / total * 100) if total > 0 else None

        return DashboardStats(
            total_incidents=total,
            open_incidents=by_status.get("OPEN", 0) + by_status.get("REOPENED", 0),
            critical_incidents=by_severity.get("CRITICAL", 0),
            investigating_incidents=by_status.get("INVESTIGATING", 0),
            awaiting_approval=by_status.get("AWAITING_APPROVAL", 0),
            resolved_incidents=resolved_count,
            avg_resolution_time_seconds=(
                sum(resolution_times) / len(resolution_times) if resolution_times else None
            ),
            ai_success_rate=ai_success,
            incidents_by_service=by_service,
            incidents_by_severity=by_severity,
            incidents_by_status=by_status,
        )
