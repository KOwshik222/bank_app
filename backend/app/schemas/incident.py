"""
Pydantic schemas for incident management — the core of the AI agent platform.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Incident Schemas ─────────────────────────────────────────────
class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    affected_service: str = Field(..., max_length=100)
    category: str = "UNKNOWN"
    reported_by: str | None = None


class IncidentResponse(BaseModel):
    id: str
    incident_number: str
    title: str
    description: str
    severity: str
    status: str
    category: str
    affected_service: str
    reported_by: str | None = None
    assigned_to: str | None = None
    correlation_id: str
    root_cause: str | None = None
    root_cause_confidence: float | None = None
    recommended_remediation: str | None = None
    remediation_risk: str | None = None
    ai_summary: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    resolution_time_seconds: int | None = None
    evidence_items: list["EvidenceResponse"] = []
    investigation_steps: list["InvestigationStepResponse"] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    """Lightweight incident for list views."""
    id: str
    incident_number: str
    title: str
    severity: str
    status: str
    category: str
    affected_service: str
    root_cause_confidence: float | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_time_seconds: int | None = None

    model_config = {"from_attributes": True}


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    category: str | None = None
    assigned_to: str | None = None


class IncidentStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class IncidentApproval(BaseModel):
    decision: str  # "approve", "reject", "request_more_investigation"
    reason: str | None = None
    approved_by: str


# ── Evidence Schemas ─────────────────────────────────────────────
class EvidenceResponse(BaseModel):
    id: str
    source_agent: str
    evidence_type: str
    title: str
    content: str
    severity: str | None = None
    confidence: float | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Investigation Step Schemas ───────────────────────────────────
class InvestigationStepResponse(BaseModel):
    id: str
    step_order: int
    agent_name: str
    tool_name: str | None = None
    description: str
    status: str
    result_summary: str | None = None
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Dashboard Stats ──────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_incidents: int = 0
    open_incidents: int = 0
    critical_incidents: int = 0
    investigating_incidents: int = 0
    awaiting_approval: int = 0
    resolved_incidents: int = 0
    avg_resolution_time_seconds: float | None = None
    ai_success_rate: float | None = None
    incidents_by_service: dict[str, int] = {}
    incidents_by_severity: dict[str, int] = {}
    incidents_by_status: dict[str, int] = {}
