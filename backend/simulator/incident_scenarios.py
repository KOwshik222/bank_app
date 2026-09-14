"""
Incident scenarios — 10 predefined incident definitions with expected root causes.
Used for simulation, testing, and evaluation.
The expected_root_cause is ONLY for evaluation — agents must discover it independently.
"""

INCIDENT_SCENARIOS = [
    {
        "id": "scenario_01",
        "title": "Database Connection Pool Exhaustion",
        "description": (
            "Payment Service is returning HTTP 500 errors. Multiple customers reporting "
            "failed transactions. Error rate has spiked to 31% in the last 15 minutes."
        ),
        "severity": "CRITICAL",
        "affected_service": "payment-service",
        "category": "DATABASE",
        "scenario_key": "db_connection_exhaustion",
        "expected_root_cause": "Database connection pool exhaustion — active connections at 498/500",
        "expected_remediation": "Increase connection pool size or rollback recent configuration change",
        "expected_confidence": 0.94,
        "investigation_hints": [
            "Check database connection metrics",
            "Review recent deployment/configuration changes",
            "Analyze error logs for connection timeout patterns",
            "Check historical incidents with similar symptoms",
        ],
    },
    {
        "id": "scenario_02",
        "title": "SSL Certificate Expiry — Authentication Service",
        "description": (
            "Authentication Service is unreachable. All services depending on auth are "
            "failing. Users cannot log in. TLS handshake errors in downstream services."
        ),
        "severity": "CRITICAL",
        "affected_service": "authentication-service",
        "category": "SECURITY",
        "scenario_key": "ssl_certificate_expiry",
        "expected_root_cause": "SSL certificate expired for authentication service endpoint",
        "expected_remediation": "Rotate SSL certificate using certificate management tool",
        "expected_confidence": 0.97,
        "investigation_hints": [
            "Check SSL certificate validity",
            "Review authentication service logs for TLS errors",
            "Check downstream service error patterns",
        ],
    },
    {
        "id": "scenario_03",
        "title": "Payment API Gateway Timeout",
        "description": (
            "Payment processing is extremely slow. Customers experiencing 30+ second "
            "wait times. Payment gateway returning timeout errors."
        ),
        "severity": "HIGH",
        "affected_service": "payment-service",
        "category": "NETWORK",
        "scenario_key": "payment_api_timeout",
        "expected_root_cause": "Payment gateway endpoint experiencing high latency — network/API issue",
        "expected_remediation": "Enable circuit breaker, switch to fallback payment processor",
        "expected_confidence": 0.88,
        "investigation_hints": [
            "Check API latency metrics",
            "Test payment gateway connectivity",
            "Review circuit breaker status",
            "Check network metrics",
        ],
    },
    {
        "id": "scenario_04",
        "title": "Primary Database Unavailable",
        "description": (
            "All services reporting database connection failures. No transactions are "
            "being processed. Database health checks failing across all services."
        ),
        "severity": "CRITICAL",
        "affected_service": "payment-service",
        "category": "DATABASE",
        "scenario_key": "database_unavailable",
        "expected_root_cause": "Primary database server unreachable — connection refused",
        "expected_remediation": "Failover to database replica, investigate primary server",
        "expected_confidence": 0.96,
        "investigation_hints": [
            "Check database connectivity",
            "Verify database server status",
            "Check all service health statuses",
        ],
    },
    {
        "id": "scenario_05",
        "title": "Payment Service High CPU Utilization",
        "description": (
            "Payment Service response times degrading. CPU utilization consistently "
            "above 90%. Thread pool exhaustion warnings appearing in logs."
        ),
        "severity": "HIGH",
        "affected_service": "payment-service",
        "category": "INFRASTRUCTURE",
        "scenario_key": "high_cpu",
        "expected_root_cause": "CPU exhaustion on payment-service — likely due to recent deployment or traffic spike",
        "expected_remediation": "Scale service horizontally, investigate CPU-intensive operations",
        "expected_confidence": 0.85,
        "investigation_hints": [
            "Check CPU metrics trend",
            "Review recent deployments",
            "Check request rate changes",
            "Look for CPU-intensive code changes",
        ],
    },
    {
        "id": "scenario_06",
        "title": "Payment Service Memory Leak",
        "description": (
            "Payment Service heap memory growing steadily. GC pauses increasing. "
            "OutOfMemoryError observed in logs. Service restarts every few hours."
        ),
        "severity": "HIGH",
        "affected_service": "payment-service",
        "category": "APPLICATION",
        "scenario_key": "memory_leak",
        "expected_root_cause": "Memory leak in payment-service — heap usage growing unbounded",
        "expected_remediation": "Restart service, investigate memory allocation in recent code changes",
        "expected_confidence": 0.90,
        "investigation_hints": [
            "Check memory usage trend",
            "Review GC metrics",
            "Check for recent code changes",
            "Analyze heap dump if available",
        ],
    },
    {
        "id": "scenario_07",
        "title": "Kafka Consumer Failure — Transaction Service",
        "description": (
            "Transaction events not being processed. Kafka consumer lag growing. "
            "Transaction reconciliation failing. Notifications not being sent."
        ),
        "severity": "HIGH",
        "affected_service": "transaction-service",
        "category": "APPLICATION",
        "scenario_key": "kafka_consumer_failure",
        "expected_root_cause": "Kafka consumer group failure — unable to connect to broker or deserialization error",
        "expected_remediation": "Restart Kafka consumer, verify broker connectivity, check message schema",
        "expected_confidence": 0.87,
        "investigation_hints": [
            "Check Kafka consumer metrics",
            "Verify broker connectivity",
            "Check message deserialization errors",
            "Review consumer group status",
        ],
    },
    {
        "id": "scenario_08",
        "title": "Authentication Service Outage",
        "description": (
            "Authentication service returning 503 errors. All API calls requiring "
            "authentication are failing. Login functionality completely broken."
        ),
        "severity": "CRITICAL",
        "affected_service": "authentication-service",
        "category": "APPLICATION",
        "scenario_key": "auth_service_failure",
        "expected_root_cause": "Authentication service failure — service unhealthy, possibly Redis session store unavailable",
        "expected_remediation": "Restart authentication service, verify Redis connectivity",
        "expected_confidence": 0.91,
        "investigation_hints": [
            "Check auth service health",
            "Verify Redis connectivity",
            "Check auth service logs",
            "Review downstream impact",
        ],
    },
    {
        "id": "scenario_09",
        "title": "Third-Party Payment Processor Outage",
        "description": (
            "External payment processor API returning 503 errors. All card payments "
            "failing. ACH and wire transfers unaffected."
        ),
        "severity": "HIGH",
        "affected_service": "payment-service",
        "category": "THIRD_PARTY",
        "scenario_key": "third_party_outage",
        "expected_root_cause": "Third-party payment processor API outage — external service unavailable",
        "expected_remediation": "Switch to backup payment processor, notify customers of delays",
        "expected_confidence": 0.93,
        "investigation_hints": [
            "Check external API health",
            "Verify internal service health is OK",
            "Review circuit breaker status",
            "Check third-party status page",
        ],
    },
    {
        "id": "scenario_10",
        "title": "Bad Deployment — Payment Service v2.8.0",
        "description": (
            "Payment Service errors began immediately after deployment of v2.8.0. "
            "Configuration mismatch errors in logs. Error rate jumped from 1% to 45%."
        ),
        "severity": "CRITICAL",
        "affected_service": "payment-service",
        "category": "DEPLOYMENT",
        "scenario_key": "bad_deployment",
        "expected_root_cause": "Bad deployment — v2.8.0 introduced configuration errors causing application failures",
        "expected_remediation": "Rollback to previous version v2.7.1",
        "expected_confidence": 0.95,
        "investigation_hints": [
            "Check recent deployments",
            "Compare deployment timestamps with error onset",
            "Review configuration changes in v2.8.0",
            "Check error logs for configuration-related failures",
        ],
    },
]


def get_scenario(scenario_key: str) -> dict | None:
    """Get a scenario by its key."""
    for s in INCIDENT_SCENARIOS:
        if s["scenario_key"] == scenario_key:
            return s
    return None


def get_all_scenarios() -> list[dict]:
    """Get all predefined incident scenarios."""
    return INCIDENT_SCENARIOS
