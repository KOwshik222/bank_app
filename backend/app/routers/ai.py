"""
AI Investigation Router — exposes multi-agent orchestration, SSE stream, and remediation.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ai.agents.orchestrator import OrchestratorAgent
from app.database import get_db
from app.schemas.incident import IncidentResponse
from app.services.incident_service import IncidentService
from simulator.incident_scenarios import INCIDENT_SCENARIOS

router = APIRouter(prefix="/api/ai", tags=["AI Investigation"])


@router.get("/scenarios")
async def list_incident_scenarios():
    """List available simulated incident scenarios for demonstration."""
    return [
        {
            "id": sc["id"],
            "title": sc["title"],
            "description": sc["description"],
            "severity": sc["severity"],
            "affected_service": sc["affected_service"],
            "scenario_key": sc["scenario_key"],
        }
        for sc in INCIDENT_SCENARIOS
    ]


@router.post("/investigate/{incident_id}")
async def investigate_incident(
    incident_id: str,
    scenario_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Trigger complete AI multi-agent investigation for an incident."""
    incident_svc = IncidentService(db)
    incident = await incident_svc.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    orchestrator = OrchestratorAgent(db=db)
    result = await orchestrator.investigate_incident(incident, scenario_key=scenario_key)
    return result


@router.get("/investigate/{incident_id}/stream")
async def stream_investigation(
    incident_id: str,
    scenario_key: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Stream real-time multi-agent investigation events via Server-Sent Events (SSE)."""
    incident_svc = IncidentService(db)
    incident = await incident_svc.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    orchestrator = OrchestratorAgent(db=db)

    async def event_generator():
        async for event in orchestrator.stream_investigation(incident, scenario_key=scenario_key):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/remediate/{incident_id}")
async def execute_remediation(
    incident_id: str,
    approved_by: str = Query("incident-commander"),
    db: AsyncSession = Depends(get_db),
):
    """Execute remediation post-approval and run automated verification."""
    incident_svc = IncidentService(db)
    incident = await incident_svc.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not incident.approved_by:
        raise HTTPException(
            status_code=400,
            detail="Incident must have human approval before remediation can execute",
        )

    orchestrator = OrchestratorAgent(db=db)
    result = await orchestrator.execute_remediation_and_verify(incident, approved_by=approved_by)
    return result
