"""
Log generator — creates realistic application logs for banking services.
Generates both normal operational logs and failure-scenario logs.
"""

import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

SERVICES = [
    "payment-service", "account-service", "customer-service",
    "transaction-service", "authentication-service", "notification-service",
]

LOG_LEVELS = ["INFO", "WARN", "ERROR", "FATAL"]

# Normal operation log templates
NORMAL_LOGS = {
    "payment-service": [
        ("INFO", "Payment {ref} initiated for ${amount}"),
        ("INFO", "Payment {ref} processed successfully"),
        ("INFO", "Payment validation passed for account {account}"),
        ("INFO", "Payment gateway response received in {latency}ms"),
        ("WARN", "Payment processing slow — {latency}ms"),
    ],
    "account-service": [
        ("INFO", "Account {account} balance retrieved"),
        ("INFO", "Account {account} updated successfully"),
        ("INFO", "Account validation passed for customer {customer}"),
        ("WARN", "Account {account} approaching daily limit"),
    ],
    "customer-service": [
        ("INFO", "Customer profile {customer} loaded"),
        ("INFO", "Customer search completed in {latency}ms"),
        ("WARN", "Customer {customer} has elevated risk score"),
    ],
    "transaction-service": [
        ("INFO", "Transaction {ref} recorded"),
        ("INFO", "Transaction batch processed: {count} records"),
        ("INFO", "Transaction ledger reconciliation complete"),
    ],
    "authentication-service": [
        ("INFO", "User {user} authenticated successfully"),
        ("INFO", "Token refreshed for user {user}"),
        ("WARN", "Failed login attempt for user {user}"),
    ],
    "notification-service": [
        ("INFO", "Email notification sent to {email}"),
        ("INFO", "SMS notification queued"),
        ("WARN", "Notification delivery delayed"),
    ],
}

# Failure scenario log templates
FAILURE_LOGS = {
    "db_connection_exhaustion": [
        ("ERROR", "payment-service", "Database connection pool exhausted — 498/500 connections in use"),
        ("ERROR", "payment-service", "Failed to acquire database connection — pool timeout after 30000ms"),
        ("ERROR", "payment-service", "java.sql.SQLTransientConnectionException: HikariPool-1 — Connection is not available"),
        ("FATAL", "payment-service", "Payment processing halted — no available database connections"),
        ("ERROR", "payment-service", "Transaction rollback — database connection unavailable"),
        ("WARN", "payment-service", "Database connection pool utilization at 99.6%"),
        ("ERROR", "account-service", "Database connection timeout — unable to query account balance"),
    ],
    "ssl_certificate_expiry": [
        ("ERROR", "authentication-service", "SSL certificate expired for auth.bank.internal"),
        ("ERROR", "authentication-service", "javax.net.ssl.SSLHandshakeException: Certificate expired"),
        ("ERROR", "payment-service", "TLS handshake failed connecting to authentication-service"),
        ("FATAL", "authentication-service", "Service unable to accept connections — SSL certificate invalid"),
        ("ERROR", "customer-service", "Upstream authentication-service connection refused — SSL error"),
    ],
    "payment_api_timeout": [
        ("ERROR", "payment-service", "Payment gateway timeout after 30000ms — {ref}"),
        ("ERROR", "payment-service", "java.net.SocketTimeoutException: Read timed out"),
        ("WARN", "payment-service", "Payment API response time degraded — avg 12500ms"),
        ("ERROR", "payment-service", "Circuit breaker opened for payment-gateway endpoint"),
        ("ERROR", "payment-service", "Retry exhausted for payment {ref} — 3/3 attempts failed"),
    ],
    "database_unavailable": [
        ("FATAL", "payment-service", "Database connection refused — Connection refused: connect"),
        ("FATAL", "account-service", "Unable to connect to PostgreSQL at db.bank.internal:5432"),
        ("ERROR", "transaction-service", "Database health check failed — connection refused"),
        ("ERROR", "payment-service", "All database replicas unreachable"),
        ("FATAL", "customer-service", "Application cannot start — database unavailable"),
    ],
    "high_cpu": [
        ("WARN", "payment-service", "CPU usage at 87% — approaching threshold"),
        ("ERROR", "payment-service", "Request processing delayed — CPU contention detected"),
        ("WARN", "payment-service", "GC pause time exceeded 500ms — 872ms recorded"),
        ("ERROR", "payment-service", "Thread pool exhausted — 200/200 threads busy"),
        ("WARN", "payment-service", "Response time degradation detected — p99 latency 8200ms"),
    ],
    "memory_leak": [
        ("WARN", "payment-service", "Heap memory usage at 82% — 3.28GB/4.0GB"),
        ("WARN", "payment-service", "Heap memory usage at 89% — 3.56GB/4.0GB"),
        ("ERROR", "payment-service", "Heap memory usage at 95% — 3.80GB/4.0GB"),
        ("FATAL", "payment-service", "java.lang.OutOfMemoryError: Java heap space"),
        ("ERROR", "payment-service", "GC overhead limit exceeded — 98% time in garbage collection"),
    ],
    "kafka_consumer_failure": [
        ("ERROR", "transaction-service", "Kafka consumer group rebalance failed"),
        ("ERROR", "transaction-service", "Unable to connect to Kafka broker at kafka.bank.internal:9092"),
        ("WARN", "transaction-service", "Kafka consumer lag: 45000 messages behind"),
        ("ERROR", "transaction-service", "Message deserialization failed — offset 1234567"),
        ("ERROR", "notification-service", "Kafka event processing timeout — consumer stalled"),
    ],
    "auth_service_failure": [
        ("FATAL", "authentication-service", "Authentication service health check failed"),
        ("ERROR", "authentication-service", "Token validation endpoint returning 503"),
        ("ERROR", "payment-service", "Unable to validate bearer token — auth service unreachable"),
        ("ERROR", "customer-service", "Authentication middleware timeout after 5000ms"),
        ("WARN", "authentication-service", "Active session store unreachable — Redis connection failed"),
    ],
    "third_party_outage": [
        ("ERROR", "payment-service", "Third-party payment processor returning 503"),
        ("ERROR", "payment-service", "External API https://api.payprocessor.com/v2/process unreachable"),
        ("WARN", "payment-service", "Circuit breaker opened for third-party payment API"),
        ("ERROR", "payment-service", "Fallback payment processor also unavailable"),
        ("ERROR", "notification-service", "External SMS gateway returning timeout errors"),
    ],
    "bad_deployment": [
        ("ERROR", "payment-service", "Application startup failed — missing configuration key 'db.pool.maxSize'"),
        ("ERROR", "payment-service", "NullPointerException in PaymentProcessor.processPayment()"),
        ("FATAL", "payment-service", "Spring context initialization failed — bean creation error"),
        ("ERROR", "payment-service", "Configuration mismatch — expected v2.8 schema but found v2.7"),
        ("WARN", "payment-service", "Rollback initiated for deployment v2.8.0"),
    ],
}


def generate_normal_logs(
    minutes: int = 60,
    logs_per_minute: int = 10,
) -> list[dict]:
    """Generate normal operation logs."""
    logs = []
    now = datetime.now(timezone.utc)

    for m in range(minutes, 0, -1):
        ts_base = now - timedelta(minutes=m)
        num_logs = random.randint(max(1, logs_per_minute - 3), logs_per_minute + 3)

        for _ in range(num_logs):
            service = random.choice(SERVICES)
            templates = NORMAL_LOGS[service]
            level, template = random.choice(templates)

            message = template.format(
                ref=f"PAY-{random.randint(1000000, 9999999)}",
                amount=f"{random.uniform(10, 5000):.2f}",
                account=f"ACC-{random.randint(100000, 999999)}",
                customer=f"CUST-{random.randint(100000, 999999)}",
                latency=random.randint(10, 500),
                user=f"user_{random.randint(1, 100)}",
                email=f"user{random.randint(1, 100)}@example.com",
                count=random.randint(10, 500),
            )

            ts = ts_base + timedelta(seconds=random.randint(0, 59))
            logs.append({
                "timestamp": ts.isoformat(),
                "level": level,
                "service": service,
                "message": message,
                "correlation_id": str(uuid4()),
                "thread": f"thread-{random.randint(1, 50)}",
                "class": f"com.bank.{service.replace('-', '.')}.handler",
            })

    return sorted(logs, key=lambda l: l["timestamp"])


def generate_incident_logs(
    scenario: str,
    incident_start: datetime | None = None,
    pre_incident_minutes: int = 30,
    during_incident_minutes: int = 15,
) -> list[dict]:
    """Generate logs for a specific incident scenario.
    Includes normal logs before the incident + failure logs during.
    """
    if incident_start is None:
        incident_start = datetime.now(timezone.utc) - timedelta(minutes=during_incident_minutes)

    logs = []

    # Pre-incident normal logs
    for m in range(pre_incident_minutes, 0, -1):
        ts = incident_start - timedelta(minutes=m)
        service = random.choice(SERVICES)
        templates = NORMAL_LOGS[service]
        level, template = random.choice(templates)
        message = template.format(
            ref=f"PAY-{random.randint(1000000, 9999999)}",
            amount=f"{random.uniform(10, 5000):.2f}",
            account=f"ACC-{random.randint(100000, 999999)}",
            customer=f"CUST-{random.randint(100000, 999999)}",
            latency=random.randint(10, 200),
            user=f"user_{random.randint(1, 100)}",
            email=f"user{random.randint(1, 100)}@example.com",
            count=random.randint(10, 500),
        )
        logs.append({
            "timestamp": ts.isoformat(),
            "level": level,
            "service": service,
            "message": message,
            "correlation_id": str(uuid4()),
        })

    # Incident logs
    failure_templates = FAILURE_LOGS.get(scenario, [])
    if failure_templates:
        for m in range(during_incident_minutes):
            ts_base = incident_start + timedelta(minutes=m)
            # Increasing error frequency over time
            num_errors = min(2 + m, 8)
            for _ in range(num_errors):
                level, service, template = random.choice(failure_templates)
                message = template.format(
                    ref=f"PAY-{random.randint(1000000, 9999999)}",
                )
                ts = ts_base + timedelta(seconds=random.randint(0, 59))
                logs.append({
                    "timestamp": ts.isoformat(),
                    "level": level,
                    "service": service,
                    "message": message,
                    "correlation_id": str(uuid4()),
                })

    return sorted(logs, key=lambda l: l["timestamp"])
