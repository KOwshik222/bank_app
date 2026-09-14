"""
Verification Agent — conducts post-remediation validation tests to confirm incident recovery.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.tools.verification_tools import check_api_health, verify_error_rate, verify_transaction_throughput


class VerificationAgent(BaseAgent):
    """Specialized agent that executes health checks and verifies recovery."""

    def __init__(self):
        super().__init__(
            name="VerificationAgent",
            role_description="Performs post-remediation verification checks across health endpoints and metrics.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        simulate_failure = context.get("simulate_verification_failure", False)

        health = check_api_health(service)
        error_check = verify_error_rate(service)
        throughput = verify_transaction_throughput(service)

        is_healthy = health["is_healthy"] and error_check["within_limits"] and not simulate_failure

        evidence = [
            f"Health check: {health['status']} (HTTP {health['http_code']})",
            f"Error rate: {error_check['current_error_rate_pct']}% (threshold: {error_check['threshold_pct']}%)",
            f"Transaction latency: P99 {throughput['p99_latency_ms']}ms",
        ]

        if is_healthy:
            verdict = "VERIFIED_RESOLVED"
            explanation = "All service health metrics have normalized. Incident can be safely closed."
        else:
            verdict = "VERIFICATION_FAILED_REOPEN"
            explanation = "Service continues to experience errors post-remediation. Incident must be reopened."

        return AgentResult(
            agent_name=self.name,
            hypothesis=f"Verification status: {verdict}",
            confidence=0.99,
            evidence=evidence,
            data={
                "verdict": verdict,
                "is_healthy": is_healthy,
                "explanation": explanation,
                "health": health,
                "error_check": error_check,
                "throughput": throughput,
            },
            recommendation=explanation,
        )
