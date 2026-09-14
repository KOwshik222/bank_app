"""
Pydantic schemas for audit trail.
"""

from datetime import datetime

from pydantic import BaseModel


class AuditEntryCreate(BaseModel):
    incident_id: str | None = None
    correlation_id: str | None = None
    actor: str
    actor_type: str = "system"  # user, agent, system
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    description: str
    input_data: str | None = None  # JSON string
    output_data: str | None = None  # JSON string
    evidence: str | None = None  # JSON string
    decision: str | None = None
    status: str = "success"


class AuditEntryResponse(BaseModel):
    id: str
    timestamp: datetime
    incident_id: str | None = None
    correlation_id: str | None = None
    actor: str
    actor_type: str
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    description: str
    input_data: str | None = None
    output_data: str | None = None
    evidence: str | None = None
    decision: str | None = None
    status: str

    model_config = {"from_attributes": True}
