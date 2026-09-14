"""
Infrastructure Analysis Agent — monitors CPU, memory, disk, and integrates ML anomaly scores.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import INFRASTRUCTURE_PROMPT, SYSTEM_BASE_PROMPT
from ai.tools.metric_tools import classify_incident_metrics, get_service_metrics, run_anomaly_detection


class InfrastructureAnalysisAgent(BaseAgent):
    """Specialized agent for host, container, and resource metrics."""

    def __init__(self):
        super().__init__(
            name="InfrastructureAnalysisAgent",
            role_description="Examines telemetry metrics, CPU, memory, and ML anomaly detector scores.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        scenario = context.get("scenario_key")

        # Fetch telemetry
        metrics = get_service_metrics(service=service, scenario=scenario, minutes=15)
        ad_result = run_anomaly_detection(metrics)
        cls_result = classify_incident_metrics(metrics)

        latest_metric = metrics[-1] if metrics else {}

        user_prompt = INFRASTRUCTURE_PROMPT.format(
            service=service,
            metrics=f"CPU: {latest_metric.get('cpu_percent')}% | Memory: {latest_metric.get('memory_percent')}% | DB Conns: {latest_metric.get('db_connections')}",
            anomaly_score=ad_result.get("anomaly_score", 0.0),
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        evidence = []
        if ad_result.get("is_anomaly"):
            evidence.append(f"Isolation Forest flagged anomaly with score {ad_result.get('anomaly_score'):.2f}")
            for expl in ad_result.get("explanation", []):
                evidence.append(expl)

        predicted_class = cls_result.get("predicted_class")
        cls_conf = cls_result.get("confidence", 0.0)
        evidence.append(f"XGBoost classifier predicts '{predicted_class}' (confidence: {cls_conf*100:.1f}%)")

        return AgentResult(
            agent_name=self.name,
            hypothesis=llm_response.get("hypothesis", f"Resource anomaly detected for {service}"),
            confidence=max(float(ad_result.get("anomaly_score", 0.8)), float(cls_conf)),
            evidence=evidence,
            data={
                "anomaly_detector": ad_result,
                "incident_classifier": cls_result,
                "latest_telemetry": latest_metric,
            },
            recommendation=llm_response.get("recommended_remediation"),
        )
