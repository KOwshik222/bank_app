"""
Log Analysis Agent — examines service logs for error spikes, exceptions, and anomalies.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import LOG_ANALYSIS_PROMPT, SYSTEM_BASE_PROMPT
from ai.tools.log_tools import get_error_summary, get_service_logs


class LogAnalysisAgent(BaseAgent):
    """Specialized agent for application log analysis."""

    def __init__(self):
        super().__init__(
            name="LogAnalysisAgent",
            role_description="Analyzes application logs, stack traces, and error patterns.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        scenario = context.get("scenario_key")
        incident_id = context.get("incident_id", "INC-CURRENT")

        # Call log tool
        logs = get_service_logs(service=service, scenario=scenario, minutes=15)
        error_summary = get_error_summary(logs)

        # Build prompt
        user_prompt = LOG_ANALYSIS_PROMPT.format(
            incident_id=incident_id,
            service=service,
            logs="\n".join([f"[{l.get('timestamp')}] {l.get('level')}: {l.get('message')}" for l in logs[:10]]),
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        hypothesis = llm_response.get("hypothesis") or (
            f"Spike of {error_summary['total_errors']} errors observed in {service} logs."
        )
        confidence = float(llm_response.get("confidence", 0.90))
        evidence = llm_response.get("evidence", [])
        if not evidence and error_summary["top_signatures"]:
            for sig, cnt in error_summary["top_signatures"].items():
                evidence.append(f"{cnt}x: {sig}")

        return AgentResult(
            agent_name=self.name,
            hypothesis=hypothesis,
            confidence=confidence,
            evidence=evidence,
            data=error_summary,
            recommendation=llm_response.get("recommended_remediation"),
        )
