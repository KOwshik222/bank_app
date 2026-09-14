import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.schemas.incident import IncidentCreate
from app.services.incident_service import IncidentService
from ai.agents.orchestrator import OrchestratorAgent

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_end_to_end_incident_investigation_and_remediation(db_session: AsyncSession):
    # 1. Initialize services
    incident_service = IncidentService(db_session)
    orchestrator = OrchestratorAgent(db=db_session)
    
    # 2. Create an incident
    incident_data = IncidentCreate(
        title="PostgreSQL connection pool exhausted on payment-service",
        description="All 100/100 connections in pool are active. HTTP 500 spike observed across checkout endpoints.",
        severity="CRITICAL",
        affected_service="payment-service",
        category="DATABASE",
        reported_by="automated-prometheus-alert"
    )
    incident = await incident_service.create_incident(incident_data)
    assert incident.id is not None
    assert incident.status == IncidentStatus.OPEN
    
    # 3. Execute AI investigation
    investigation_result = await orchestrator.investigate_incident(
        incident=incident,
        scenario_key="db_connection_exhaustion"
    )
    await db_session.commit()
    
    # Reload incident from db
    updated_incident = await incident_service.get_incident(incident.id)
    assert updated_incident is not None
    assert updated_incident.status == IncidentStatus.AWAITING_APPROVAL
    assert updated_incident.root_cause is not None
    assert updated_incident.root_cause_confidence is not None
    assert updated_incident.root_cause_confidence > 0.5
    assert len(updated_incident.investigation_steps) >= 5
    assert len(updated_incident.evidence_items) >= 4
    
    # 4. Human Approval Gate
    approved_incident = await incident_service.approve_remediation(
        incident_id=incident.id,
        approved_by="lead-sre@bankops.internal"
    )
    assert approved_incident.status == IncidentStatus.REMEDIATING
    assert approved_incident.approved_by == "lead-sre@bankops.internal"
    
    # 5. Execute remediation & automated verification
    rem_result = await orchestrator.execute_remediation_and_verify(
        incident=approved_incident,
        approved_by="lead-sre@bankops.internal"
    )
    assert rem_result["final_status"] == IncidentStatus.RESOLVED.value
    
    # Final check on incident state
    final_incident = await incident_service.get_incident(incident.id)
    assert final_incident.status == IncidentStatus.RESOLVED
    assert final_incident.resolved_at is not None
