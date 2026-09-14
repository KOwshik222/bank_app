"""
Incident management API routes — the core of the AI agent platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import IncidentStatus
from app.schemas.incident import (
    DashboardStats,
    IncidentApproval,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
)
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new incident."""
    service = IncidentService(db)
    audit = AuditService(db)
    incident = await service.create_incident(data)
    await audit.log(
        action="incident.created",
        description=f"Incident {incident.incident_number} created: {incident.title}",
        actor=data.reported_by or "system",
        actor_type="user" if data.reported_by else "system",
        incident_id=incident.id,
        correlation_id=incident.correlation_id,
        resource_type="incident",
        resource_id=incident.id,
    )
    return IncidentResponse.model_validate(incident)


@router.get("/", response_model=list[IncidentListResponse])
async def list_incidents(
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = None,
    service: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List incidents with optional filters."""
    svc = IncidentService(db)
    incidents = await svc.list_incidents(
        status=status_filter, severity=severity, service=service, skip=skip, limit=limit
    )
    return [IncidentListResponse.model_validate(i) for i in incidents]


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    service = IncidentService(db)
    return await service.get_dashboard_stats()


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get incident details with evidence and investigation steps."""
    service = IncidentService(db)
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(incident)


@router.post("/{incident_id}/approve", response_model=IncidentResponse)
async def approve_remediation(
    incident_id: str, approval: IncidentApproval, db: AsyncSession = Depends(get_db)
):
    """Approve, reject, or request more investigation for an incident."""
    service = IncidentService(db)
    audit = AuditService(db)

    try:
        if approval.decision == "approve":
            incident = await service.approve_remediation(incident_id, approval.approved_by)
            await audit.log(
                action="remediation.approved",
                description=f"Remediation approved for {incident.incident_number}",
                actor=approval.approved_by,
                actor_type="user",
                incident_id=incident_id,
                correlation_id=incident.correlation_id,
                decision="approved",
            )
        elif approval.decision == "reject":
            incident = await service.reject_remediation(
                incident_id, approval.approved_by, approval.reason or "No reason provided"
            )
            await audit.log(
                action="remediation.rejected",
                description=f"Remediation rejected for {incident.incident_number}: {approval.reason}",
                actor=approval.approved_by,
                actor_type="user",
                incident_id=incident_id,
                correlation_id=incident.correlation_id,
                decision="rejected",
            )
        elif approval.decision == "request_more_investigation":
            incident = await service.request_more_investigation(incident_id)
            await audit.log(
                action="investigation.requested",
                description=f"More investigation requested for {incident.incident_number}",
                actor=approval.approved_by,
                actor_type="user",
                incident_id=incident_id,
                correlation_id=incident.correlation_id,
                decision="more_investigation",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid decision: {approval.decision}. "
                       f"Must be 'approve', 'reject', or 'request_more_investigation'",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IncidentResponse.model_validate(incident)
