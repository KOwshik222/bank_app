"""
API Analysis Agent — investigates HTTP status codes, latency percentiles, and circuit breakers.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import API_PROMPT, SYSTEM_BASE_PROMPT
from ai.tools.api_tools import get_circuit_breaker_status, get_endpoint_health


class ApiAnalysisAgent(BaseAgent):
    """Specialized agent for API endpoints and network latency."""

    def __init__(self):
        super().__init__(
            name="ApiAnalysisAgent",
            role_description="Analyzes API status codes, endpoint latencies, and circuit breaker trip states.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        scenario = context.get("scenario_key")

        health = get_endpoint_health(service, scenario)
        cb = get_circuit_breaker_status(service, scenario)

        api_summary = (
            f"Service: {service} | Status: {health['status']} ({health['http_code']}) | "
            f"TLS Status: {health['tls_handshake_status']} | Circuit Breaker: {cb['state']} "
            f"({cb['current_failure_rate_pct']}% failure rate)"
        )

        user_prompt = API_PROMPT.format(
            service=service,
            api_data=api_summary,
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        evidence = []
        if health["http_code"] != 200:
            evidence.append(f"Service health check returned HTTP {health['http_code']} ({health['status']})")
        if health["tls_handshake_status"] != "OK":
            evidence.append(f"TLS Handshake verification error: {health['tls_handshake_status']}")
        if cb["state"] != "CLOSED":
            evidence.append(f"Circuit breaker '{cb['circuit_breaker_name']}' tripped to {cb['state']}")

        if not evidence:
            evidence.append("All API health endpoints and circuit breakers operating normally")

        confidence = 0.94 if health["http_code"] != 200 else 0.85

        return AgentResult(
            agent_name=self.name,
            hypothesis=llm_response.get("hypothesis", f"API health issue observed on {service}"),
            confidence=confidence,
            evidence=evidence,
            data={"health": health, "circuit_breaker": cb},
            recommendation=llm_response.get("recommended_remediation"),
        )
