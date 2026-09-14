"""
Audit trail API routes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.audit import AuditEntryResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.get("/", response_model=list[AuditEntryResponse])
async def list_audit_entries(
    action: str | None = None,
    actor: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List audit entries with optional filters."""
    service = AuditService(db)
    entries = await service.list_entries(action=action, actor=actor, skip=skip, limit=limit)
    return [AuditEntryResponse.model_validate(e) for e in entries]


@router.get("/incident/{incident_id}", response_model=list[AuditEntryResponse])
async def get_incident_audit(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get all audit entries for a specific incident."""
    service = AuditService(db)
    entries = await service.get_entries_for_incident(incident_id)
    return [AuditEntryResponse.model_validate(e) for e in entries]
