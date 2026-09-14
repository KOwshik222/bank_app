"""
Deployment Analysis Agent — correlates recent software releases and configuration changes with incidents.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import DEPLOYMENT_PROMPT, SYSTEM_BASE_PROMPT
from ai.tools.deployment_tools import analyze_deployment_correlation, get_recent_deployments


class DeploymentAnalysisAgent(BaseAgent):
    """Specialized agent for CI/CD deployment correlation and rollback assessment."""

    def __init__(self):
        super().__init__(
            name="DeploymentAnalysisAgent",
            role_description="Correlates code deployments, configuration pushes, and release history.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        deployments = get_recent_deployments(service, limit=3)
        correlation = analyze_deployment_correlation(service)

        deploys_text = "\n".join([
            f"- {d.get('version')} at {d.get('deployed_at')} by {d.get('deployed_by')} [{d.get('status')}] "
            f"Config changes: {d.get('config_changes')}"
            for d in deployments
        ])

        user_prompt = DEPLOYMENT_PROMPT.format(
            service=service,
            deployments=deploys_text or "No deployments recorded",
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        evidence = []
        if correlation.get("correlated"):
            evidence.append(
                f"Recent deployment '{correlation.get('latest_version')}' detected with config changes: "
                f"{correlation.get('config_changes')}"
            )
            if correlation.get("previous_version"):
                evidence.append(f"Safe rollback target identified: '{correlation.get('previous_version')}'")
        else:
            evidence.append("No suspicious configuration changes in recent deployment window")

        confidence = 0.92 if correlation.get("correlated") else 0.80

        return AgentResult(
            agent_name=self.name,
            hypothesis=llm_response.get("hypothesis", "Deployment correlation analyzed"),
            confidence=confidence,
            evidence=evidence,
            data={"correlation": correlation, "recent_deployments": deployments},
            recommendation=correlation.get("recommendation"),
        )
