"""
Orchestrator Agent — master coordinator for banking incident investigations.
Sequences specialized agents, collects evidence, streams progress, and synthesizes RCA.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from ai.agents.api_analysis import ApiAnalysisAgent
from ai.agents.database_analysis import DatabaseAnalysisAgent
from ai.agents.deployment_analysis import DeploymentAnalysisAgent
from ai.agents.infrastructure_analysis import InfrastructureAnalysisAgent
from ai.agents.knowledge_rag import KnowledgeRAGAgent
from ai.agents.log_analysis import LogAnalysisAgent
from ai.agents.remediation import RemediationAgent
from ai.agents.root_cause_analysis import RootCauseAnalysisAgent
from ai.agents.verification import VerificationAgent
from app.models.incident import Incident, IncidentStatus
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Coordinates the full multi-agent investigation lifecycle."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.log_agent = LogAnalysisAgent()
        self.infra_agent = InfrastructureAnalysisAgent()
        self.db_agent = DatabaseAnalysisAgent()
        self.api_agent = ApiAnalysisAgent()
        self.deployment_agent = DeploymentAnalysisAgent()
        self.rag_agent = KnowledgeRAGAgent()
        self.rca_agent = RootCauseAnalysisAgent()
        self.remediation_agent = RemediationAgent()
        self.verification_agent = VerificationAgent()

    async def investigate_incident(
        self,
        incident: Incident,
        scenario_key: str | None = None,
    ) -> dict[str, Any]:
        """Execute the complete multi-agent investigation synchronously or background."""
        context: dict[str, Any] = {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value,
            "affected_service": incident.affected_service,
            "scenario_key": scenario_key or self._guess_scenario(incident),
            "agent_results": [],
        }

        incident_svc = IncidentService(self.db) if self.db else None
        audit_svc = AuditService(self.db) if self.db else None

        # Update status to INVESTIGATING
        if incident_svc:
            await incident_svc.transition_status(incident.id, IncidentStatus.INVESTIGATING)
            if audit_svc:
                await audit_svc.log(
                    action="investigation.started",
                    description=f"AI Multi-Agent investigation initiated for {incident.incident_number}",
                    actor="ai-orchestrator",
                    actor_type="agent",
                    incident_id=incident.id,
                )

        # Sequence of investigation agents
        agents = [
            ("Log Analysis", self.log_agent, "LOGS"),
            ("Infrastructure & ML Metrics", self.infra_agent, "METRICS"),
            ("Database Diagnostic", self.db_agent, "DATABASE"),
            ("API & Network Latency", self.api_agent, "API"),
            ("Deployment & CI/CD History", self.deployment_agent, "DEPLOYMENT"),
            ("RAG Runbook & Knowledge Retrieval", self.rag_agent, "KNOWLEDGE_BASE"),
        ]

        for step_idx, (step_name, agent, evidence_type) in enumerate(agents, 1):
            logger.info(f"Running agent step {step_idx}: {step_name}")
            result = await agent.investigate(context)
            context["agent_results"].append(result.to_dict())

            # Record step in database
            if incident_svc:
                step = await incident_svc.add_investigation_step(
                    incident_id=incident.id,
                    step_order=step_idx,
                    agent_name=agent.name,
                    description=f"Investigate {step_name}",
                    tool_name=agent.name,
                )
                await incident_svc.update_investigation_step(
                    step_id=step.id,
                    status="completed",
                    result_summary=result.hypothesis,
                    duration_ms=250,
                )
                # Attach primary evidence
                for ev_text in result.evidence[:3]:
                    await incident_svc.add_evidence(
                        incident_id=incident.id,
                        source_agent=agent.name,
                        evidence_type=evidence_type,
                        title=f"Evidence from {agent.name}",
                        content=ev_text,
                        confidence=result.confidence,
                    )

        # Final RCA Synthesis
        logger.info("Running Root Cause Analysis Agent synthesis...")
        rca_result = await self.rca_agent.investigate(context)

        rca_data = rca_result.data
        root_cause = rca_data.get("root_cause", rca_result.hypothesis)
        confidence = rca_result.confidence
        remediation = rca_data.get("recommended_remediation", "Restart affected service")
        risk = rca_data.get("risk_level", "MEDIUM")
        summary = rca_data.get("summary", "Investigation complete")

        if incident_svc:
            await incident_svc.update_rca(
                incident_id=incident.id,
                root_cause=root_cause,
                confidence=confidence,
                remediation=remediation,
                risk=risk,
                summary=summary,
            )
            if audit_svc:
                await audit_svc.log(
                    action="investigation.completed",
                    description=f"RCA completed for {incident.incident_number}: {root_cause}",
                    actor="ai-orchestrator",
                    actor_type="agent",
                    incident_id=incident.id,
                    output_data={"confidence": confidence},
                    decision="awaiting_human_approval",
                )

        return {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "root_cause": root_cause,
            "confidence": confidence,
            "remediation": remediation,
            "risk": risk,
            "summary": summary,
            "steps_completed": len(agents),
            "agent_results": context["agent_results"],
        }

    async def stream_investigation(
        self,
        incident: Incident,
        scenario_key: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream real-time investigation steps for SSE."""
        context: dict[str, Any] = {
            "incident_id": incident.id,
            "incident_number": incident.incident_number,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value,
            "affected_service": incident.affected_service,
            "scenario_key": scenario_key or self._guess_scenario(incident),
            "agent_results": [],
        }

        yield {
            "type": "STATUS",
            "message": f"Starting investigation for {incident.incident_number}",
            "status": "INVESTIGATING",
        }

        incident_svc = IncidentService(self.db) if self.db else None
        audit_svc = AuditService(self.db) if self.db else None

        if incident_svc:
            try:
                await incident_svc.transition_status(incident.id, IncidentStatus.INVESTIGATING)
                if self.db:
                    await self.db.commit()
            except Exception as e:
                logger.warning(f"Could not transition status: {e}")

        agents = [
            ("Log Analysis Agent", self.log_agent, "LOGS"),
            ("Infrastructure Analysis Agent", self.infra_agent, "METRICS"),
            ("Database Analysis Agent", self.db_agent, "DATABASE"),
            ("API Analysis Agent", self.api_agent, "API"),
            ("Deployment Analysis Agent", self.deployment_agent, "DEPLOYMENT"),
            ("Knowledge RAG Agent", self.rag_agent, "KNOWLEDGE_BASE"),
        ]

        for step_idx, (name, agent, ev_type) in enumerate(agents, 1):
            yield {
                "type": "STEP_START",
                "step": step_idx,
                "agent": name,
                "message": f"Agent '{name}' analyzing telemetry...",
            }
            await asyncio.sleep(0.3)
            result = await agent.investigate(context)
            context["agent_results"].append(result.to_dict())

            if incident_svc:
                try:
                    step = await incident_svc.add_investigation_step(
                        incident_id=incident.id,
                        step_order=step_idx,
                        agent_name=agent.name,
                        description=f"Investigate {name}",
                        tool_name=agent.name,
                    )
                    await incident_svc.update_investigation_step(
                        step_id=step.id,
                        status="completed",
                        result_summary=result.hypothesis,
                        duration_ms=250,
                    )
                    for ev_text in result.evidence[:3]:
                        await incident_svc.add_evidence(
                            incident_id=incident.id,
                            source_agent=agent.name,
                            evidence_type=ev_type,
                            title=f"Evidence from {agent.name}",
                            content=ev_text,
                            confidence=result.confidence,
                        )
                    if self.db:
                        await self.db.commit()
                except Exception as e:
                    logger.warning(f"Error persisting step {step_idx}: {e}")

            yield {
                "type": "STEP_COMPLETE",
                "step": step_idx,
                "agent": name,
                "hypothesis": result.hypothesis,
                "confidence": result.confidence,
                "evidence": result.evidence[:3],
            }

        yield {
            "type": "SYNTHESIS_START",
            "agent": "RootCauseAnalysisAgent",
            "message": "Synthesizing cross-agent evidence into definitive Root Cause...",
        }
        rca_result = await self.rca_agent.investigate(context)
        rca_data = rca_result.data

        root_cause = rca_data.get("root_cause", rca_result.hypothesis)
        confidence = rca_result.confidence
        remediation = rca_data.get("recommended_remediation") or rca_result.recommendation or "Restart affected service and scale instances"
        risk = rca_data.get("risk_level", "MEDIUM")
        summary = rca_data.get("summary", f"AI RCA completed for {incident.incident_number}")


        if incident_svc:
            try:
                await incident_svc.update_rca(
                    incident_id=incident.id,
                    root_cause=root_cause,
                    confidence=confidence,
                    remediation=remediation,
                    risk=risk,
                    summary=summary,
                )
                if audit_svc:
                    await audit_svc.log(
                        action="investigation.completed",
                        description=f"RCA completed for {incident.incident_number}: {root_cause}",
                        actor="ai-orchestrator",
                        actor_type="agent",
                        incident_id=incident.id,
                    )
                if self.db:
                    await self.db.commit()
            except Exception as e:
                logger.warning(f"Error persisting RCA: {e}")

        yield {
            "type": "INVESTIGATION_COMPLETE",
            "root_cause": root_cause,
            "confidence": confidence,
            "risk_level": risk,
            "recommended_remediation": remediation,
            "summary": summary,
            "status": "AWAITING_APPROVAL",
        }

    async def execute_remediation_and_verify(
        self,
        incident: Incident,
        approved_by: str,
    ) -> dict[str, Any]:
        """Execute remediation post-approval and automatically verify."""
        incident_svc = IncidentService(self.db) if self.db else None
        audit_svc = AuditService(self.db) if self.db else None

        # 1. Transition to REMEDIATING (if not already in REMEDIATING)
        if incident_svc and incident.status != IncidentStatus.REMEDIATING:
            await incident_svc.transition_status(incident.id, IncidentStatus.REMEDIATING)
        if audit_svc:
            await audit_svc.log(
                    action="remediation.started",
                    description=f"Executing remediation for {incident.incident_number}",
                    actor=approved_by,
                    actor_type="user",
                    incident_id=incident.id,
                )

        # 2. Execute fix
        rem_result = await self.remediation_agent.investigate({
            "affected_service": incident.affected_service,
            "remediation_action": incident.recommended_remediation or "restart",
        })

        # 3. Transition to VERIFYING
        if incident_svc:
            await incident_svc.transition_status(incident.id, IncidentStatus.VERIFYING)

        # 4. Verify fix
        ver_result = await self.verification_agent.investigate({
            "affected_service": incident.affected_service,
            "remediation": incident.recommended_remediation,
        })

        ver_data = ver_result.data
        is_healthy = ver_data.get("is_healthy", True)

        # 5. Transition to RESOLVED or REOPENED
        new_status = IncidentStatus.RESOLVED if is_healthy else IncidentStatus.REOPENED
        if incident_svc:
            await incident_svc.transition_status(incident.id, new_status)
            if audit_svc:
                await audit_svc.log(
                    action="verification.completed",
                    description=f"Verification verdict: {ver_data.get('verdict')} for {incident.incident_number}",
                    actor="ai-verification-agent",
                    actor_type="agent",
                    incident_id=incident.id,
                    decision="resolved" if is_healthy else "reopened",
                )

        return {
            "incident_id": incident.id,
            "remediation": rem_result.to_dict(),
            "verification": ver_result.to_dict(),
            "final_status": new_status.value,
        }

    @staticmethod
    def _guess_scenario(incident: Incident) -> str | None:
        from simulator.incident_scenarios import INCIDENT_SCENARIOS

        title = (incident.title or "").lower()
        desc = (incident.description or "").lower()
        text = f"{title} {desc}"

        # 1. Exact or partial title / scenario_key match against definitions
        for sc in INCIDENT_SCENARIOS:
            sc_key = sc["scenario_key"].lower()
            sc_title = sc["title"].lower()
            if sc_key in text or sc_title in title or sc_title in text:
                return sc["scenario_key"]

        # 2. Heuristic domain keyword matching
        if "ssl" in text or "cert" in text or "handshake" in text or "tls" in text:
            return "ssl_certificate_expiry"
        elif "redis" in text or ("auth" in text and "503" in text) or "authentication service outage" in text or "auth_service" in text:
            return "auth_service_failure"
        elif "third-party" in text or "third_party" in text or "payprocessor" in text or "processor outage" in text:
            return "third_party_outage"
        elif "bad deployment" in text or "v2.8" in text or "config mismatch" in text or "missing configuration key" in text:
            return "bad_deployment"
        elif "database unavailable" in text or "refused: connect" in text or "connection refused" in text or "server unreachable" in text:
            return "database_unavailable"
        elif "498/500" in text or "hikaripool" in text or ("pool" in text and "exhaust" in text) or ("db" in text and "pool" in text):
            return "db_connection_exhaustion"
        elif "timeout" in text or "slow" in text or "gateway" in text or "sockettimeout" in text:
            return "payment_api_timeout"
        elif "cpu" in text or "thread pool" in text:
            return "high_cpu"
        elif "memory" in text or "leak" in text or "heap" in text or "oom" in text or "outofmemory" in text:
            return "memory_leak"
        elif "kafka" in text or "consumer" in text or "deserialization" in text or "lag" in text:
            return "kafka_consumer_failure"

        return None

