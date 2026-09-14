"""
Remediation Agent — coordinates execution of remediation actions upon human approval.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.tools.remediation_tools import (
    increase_connection_pool,
    restart_service,
    rollback_deployment,
    rotate_ssl_certificate,
    scale_service,
    trip_circuit_breaker,
)


class RemediationAgent(BaseAgent):
    """Specialized agent that executes automated fixes post-approval."""

    def __init__(self):
        super().__init__(
            name="RemediationAgent",
            role_description="Executes remediation actions in simulated infrastructure after human approval.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        remediation_action = context.get("remediation_action", "restart_service")

        action_result = {}
        if "rollback" in remediation_action.lower():
            action_result = rollback_deployment(service)
        elif "cert" in remediation_action.lower() or "ssl" in remediation_action.lower():
            action_result = rotate_ssl_certificate(service)
        elif "pool" in remediation_action.lower() or "connection" in remediation_action.lower():
            action_result = increase_connection_pool(service, new_max=500)
        elif "circuit" in remediation_action.lower() or "breaker" in remediation_action.lower():
            action_result = trip_circuit_breaker(service)
        elif "scale" in remediation_action.lower():
            action_result = scale_service(service, replicas=3)
        else:
            action_result = restart_service(service)

        evidence = [
            f"Executed action: {action_result.get('action')}",
            action_result.get("message", "Remediation command succeeded"),
        ]

        return AgentResult(
            agent_name=self.name,
            hypothesis=f"Remediation action successfully applied to {service}",
            confidence=0.98,
            evidence=evidence,
            data=action_result,
            recommendation=action_result.get("message"),
        )
