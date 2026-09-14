"""
Database tools — callable by Database Analysis Agent.
Queries connection pool utilization, query latencies, locks, and connectivity.
"""

from typing import Any


def get_connection_pool_status(service: str, scenario: str | None = None) -> dict[str, Any]:
    """Inspect active vs max database connections and pool wait queues."""
    if scenario == "db_connection_exhaustion":
        return {
            "active_connections": 498,
            "max_connections": 500,
            "utilization_pct": 99.6,
            "waiting_threads": 47,
            "average_wait_time_ms": 4210.5,
            "status": "CRITICAL_EXHAUSTION",
        }
    elif scenario == "database_unavailable":
        return {
            "active_connections": 0,
            "max_connections": 500,
            "utilization_pct": 0.0,
            "waiting_threads": 120,
            "average_wait_time_ms": 30000.0,
            "status": "SERVER_UNREACHABLE",
        }
    return {
        "active_connections": 38,
        "max_connections": 500,
        "utilization_pct": 7.6,
        "waiting_threads": 0,
        "average_wait_time_ms": 4.2,
        "status": "HEALTHY",
    }


def get_query_latency(service: str, scenario: str | None = None) -> dict[str, Any]:
    """Retrieve query latency statistics."""
    if scenario in ("db_connection_exhaustion", "database_unavailable"):
        return {
            "p50_latency_ms": 1250.0,
            "p95_latency_ms": 4800.0,
            "p99_latency_ms": 8900.0,
            "slow_queries_count": 89,
            "top_slow_query": "SELECT * FROM payments WHERE status = 'PENDING' FOR UPDATE",
        }
    return {
        "p50_latency_ms": 8.5,
        "p95_latency_ms": 22.0,
        "p99_latency_ms": 45.0,
        "slow_queries_count": 0,
        "top_slow_query": None,
    }


def get_db_locks(service: str, scenario: str | None = None) -> dict[str, Any]:
    """Inspect row or table locks."""
    if scenario == "database_deadlock":
        return {
            "deadlocks_detected": True,
            "deadlock_count": 14,
            "blocked_pids": [1042, 1048],
            "blocking_relation": "accounts",
        }
    return {
        "deadlocks_detected": False,
        "deadlock_count": 0,
        "blocked_pids": [],
        "blocking_relation": None,
    }
