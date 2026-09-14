"""
Root Cause Analysis (RCA) Agent — lead investigator that synthesizes all specialized agent evidence.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import ROOT_CAUSE_ANALYSIS_PROMPT, SYSTEM_BASE_PROMPT


class RootCauseAnalysisAgent(BaseAgent):
    """Lead investigator that synthesizes findings from all domain agents."""

    def __init__(self):
        super().__init__(
            name="RootCauseAnalysisAgent",
            role_description="Synthesizes cross-domain findings into definitive root cause, risk, and remediation plan.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        incident_number = context.get("incident_number", "INC-0000")
        title = context.get("title", "Banking Incident")
        service = context.get("affected_service", "payment-service")
        agent_results: list[dict[str, Any]] = context.get("agent_results", [])
        ml_results = context.get("ml_results", {})

        evidence_blocks = []
        for res in agent_results:
            agent_name = res.get("agent_name")
            hyp = res.get("hypothesis")
            ev_list = res.get("evidence", [])
            evidence_blocks.append(f"[{agent_name}] Hypothesis: {hyp}\nEvidence:\n" + "\n".join([f"  - {e}" for e in ev_list]))

        scenario_key = context.get("scenario_key")
        title_with_scenario = f"{title} [Scenario: {scenario_key}]" if scenario_key else title

        user_prompt = ROOT_CAUSE_ANALYSIS_PROMPT.format(
            incident_number=incident_number,
            title=title_with_scenario,
            service=service,
            all_evidence="\n\n".join(evidence_blocks) or "No agent evidence supplied",
            ml_results=str(ml_results),
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        root_cause = llm_response.get("root_cause") or llm_response.get("root_cause_identified") or (
            f"Service degradation in {service} detected by automated telemetry"
        )
        summary = llm_response.get("summary", f"AI RCA completed for {incident_number}")
        confidence = float(llm_response.get("confidence", 0.92))
        risk_level = llm_response.get("risk_level", "MEDIUM")
        remediation = llm_response.get("recommended_remediation") or "Restart affected service and verify telemetry"
        primary_evidence = llm_response.get("primary_evidence") or llm_response.get("evidence", [])


        if not primary_evidence:
            for r in agent_results:
                primary_evidence.extend(r.get("evidence", [])[:2])

        return AgentResult(
            agent_name=self.name,
            hypothesis=root_cause,
            confidence=confidence,
            evidence=primary_evidence,
            data={
                "summary": summary,
                "root_cause": root_cause,
                "confidence": confidence,
                "risk_level": risk_level,
                "recommended_remediation": remediation,
                "remediation_type": llm_response.get("remediation_type", "ROLLBACK"),
                "alternative_hypotheses": llm_response.get("alternative_hypotheses", []),
            },
            recommendation=remediation,
        )
