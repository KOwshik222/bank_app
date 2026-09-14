"""
Database Analysis Agent — evaluates connection pools, slow queries, deadlocks, and database health.
"""

from typing import Any
from ai.agents.base_agent import AgentResult, BaseAgent
from ai.llm.prompt_templates import DATABASE_PROMPT, SYSTEM_BASE_PROMPT
from ai.tools.db_tools import get_connection_pool_status, get_db_locks, get_query_latency


class DatabaseAnalysisAgent(BaseAgent):
    """Specialized agent for database and connection pool investigation."""

    def __init__(self):
        super().__init__(
            name="DatabaseAnalysisAgent",
            role_description="Analyzes connection pool saturation, query performance, and transactional locks.",
        )

    async def investigate(self, context: dict[str, Any]) -> AgentResult:
        service = context.get("affected_service", "payment-service")
        scenario = context.get("scenario_key")
        incident_id = context.get("incident_id", "INC-CURRENT")

        pool_status = get_connection_pool_status(service, scenario)
        query_latency = get_query_latency(service, scenario)
        locks = get_db_locks(service, scenario)

        db_summary = (
            f"Pool: {pool_status['active_connections']}/{pool_status['max_connections']} ({pool_status['utilization_pct']}%) | "
            f"Wait threads: {pool_status['waiting_threads']} | P99 Latency: {query_latency['p99_latency_ms']}ms | "
            f"Deadlocks: {locks['deadlocks_detected']}"
        )

        user_prompt = DATABASE_PROMPT.format(
            incident_id=incident_id,
            service=service,
            db_data=db_summary,
        )

        llm_response = await self.llm.chat(SYSTEM_BASE_PROMPT, user_prompt)

        evidence = []
        is_db_anomaly = False

        if pool_status["utilization_pct"] > 80.0:
            is_db_anomaly = True
            evidence.append(
                f"Connection pool critical: {pool_status['active_connections']}/{pool_status['max_connections']} "
                f"({pool_status['utilization_pct']}% utilized) with {pool_status['waiting_threads']} queued requests"
            )
        elif pool_status["status"] == "SERVER_UNREACHABLE":
            is_db_anomaly = True
            evidence.append("Primary database unreachable: Connection refused on port 5432")

        if query_latency["p99_latency_ms"] > 1000:
            is_db_anomaly = True
            evidence.append(f"P99 query latency elevated to {query_latency['p99_latency_ms']}ms")
        if locks["deadlocks_detected"]:
            is_db_anomaly = True
            evidence.append(f"Deadlock detected on relation '{locks['blocking_relation']}'")

        if not is_db_anomaly:
            evidence.append(f"Database connection pool normal ({pool_status['active_connections']}/{pool_status['max_connections']} active, {pool_status['utilization_pct']}%)")
            evidence.append("Database query latencies and locks within standard baseline limits")
            default_hypothesis = f"Database metrics healthy: {pool_status['active_connections']}/{pool_status['max_connections']} connections in use, 0 deadlocks"
        else:
            if pool_status["utilization_pct"] > 80.0:
                default_hypothesis = f"Database connection pool exhaustion: {pool_status['active_connections']}/{pool_status['max_connections']} connections utilized"
            elif pool_status["status"] == "SERVER_UNREACHABLE":
                default_hypothesis = "Primary database server unreachable: Connection refused on port 5432"
            else:
                default_hypothesis = "Database performance degradation detected"

        confidence = 0.95 if is_db_anomaly else 0.90

        return AgentResult(
            agent_name=self.name,
            hypothesis=llm_response.get("hypothesis") or default_hypothesis,
            confidence=confidence,
            evidence=evidence,
            data={
                "pool_status": pool_status,
                "query_latency": query_latency,
                "locks": locks,
            },
            recommendation=llm_response.get("recommended_remediation"),
        )

