"""
Metric generator — creates time-series metrics for banking services.
Generates normal baselines and anomalous patterns for incident scenarios.
"""

import math
import random
from datetime import datetime, timedelta, timezone


SERVICES = [
    "payment-service", "account-service", "customer-service",
    "transaction-service", "authentication-service", "notification-service",
]

# Normal baseline ranges per service
NORMAL_BASELINES = {
    "payment-service": {
        "cpu_percent": (15, 45),
        "memory_percent": (40, 65),
        "disk_percent": (30, 50),
        "db_connections": (20, 80),
        "db_max_connections": 500,
        "api_latency_ms": (50, 200),
        "error_rate_percent": (0.1, 1.5),
        "request_rate_per_sec": (50, 200),
        "transaction_volume_per_min": (100, 500),
    },
    "account-service": {
        "cpu_percent": (10, 30),
        "memory_percent": (35, 55),
        "disk_percent": (25, 45),
        "db_connections": (10, 40),
        "db_max_connections": 200,
        "api_latency_ms": (30, 150),
        "error_rate_percent": (0.05, 0.8),
        "request_rate_per_sec": (30, 120),
        "transaction_volume_per_min": (50, 200),
    },
    "authentication-service": {
        "cpu_percent": (10, 35),
        "memory_percent": (30, 50),
        "disk_percent": (20, 40),
        "db_connections": (5, 25),
        "db_max_connections": 100,
        "api_latency_ms": (20, 100),
        "error_rate_percent": (0.1, 1.0),
        "request_rate_per_sec": (40, 180),
        "transaction_volume_per_min": (0, 0),
    },
}

# Add defaults for remaining services
for svc in SERVICES:
    if svc not in NORMAL_BASELINES:
        NORMAL_BASELINES[svc] = {
            "cpu_percent": (10, 30),
            "memory_percent": (30, 55),
            "disk_percent": (25, 45),
            "db_connections": (8, 30),
            "db_max_connections": 200,
            "api_latency_ms": (30, 150),
            "error_rate_percent": (0.05, 0.8),
            "request_rate_per_sec": (20, 100),
            "transaction_volume_per_min": (30, 150),
        }


def _add_noise(value: float, noise_pct: float = 0.05) -> float:
    """Add small random noise to a metric value."""
    return value * (1 + random.uniform(-noise_pct, noise_pct))


def generate_normal_metrics(
    service: str = "payment-service",
    minutes: int = 60,
    interval_seconds: int = 60,
) -> list[dict]:
    """Generate normal metrics for a service."""
    baselines = NORMAL_BASELINES[service]
    metrics = []
    now = datetime.now(timezone.utc)

    for m in range(minutes, 0, -1):
        ts = now - timedelta(minutes=m)

        # Add time-of-day pattern (busier during business hours)
        hour = ts.hour
        load_factor = 0.5 + 0.5 * math.sin(math.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 0.3

        cpu_low, cpu_high = baselines["cpu_percent"]
        mem_low, mem_high = baselines["memory_percent"]

        metrics.append({
            "timestamp": ts.isoformat(),
            "service": service,
            "cpu_percent": round(_add_noise(cpu_low + (cpu_high - cpu_low) * load_factor), 1),
            "memory_percent": round(_add_noise(mem_low + (mem_high - mem_low) * 0.7), 1),
            "disk_percent": round(_add_noise(random.uniform(*baselines["disk_percent"])), 1),
            "db_connections": int(_add_noise(random.uniform(*baselines["db_connections"]))),
            "db_max_connections": baselines["db_max_connections"],
            "api_latency_ms": round(_add_noise(random.uniform(*baselines["api_latency_ms"])), 1),
            "error_rate_percent": round(_add_noise(random.uniform(*baselines["error_rate_percent"])), 2),
            "request_rate_per_sec": int(_add_noise(random.uniform(*baselines["request_rate_per_sec"]) * load_factor)),
            "transaction_volume_per_min": int(_add_noise(random.uniform(*baselines["transaction_volume_per_min"]) * load_factor)),
            "service_healthy": True,
        })

    return metrics


# Anomaly profiles per incident scenario
ANOMALY_PROFILES = {
    "db_connection_exhaustion": {
        "target_service": "payment-service",
        "anomalies": {
            "db_connections": lambda t, max_conn: min(int(80 + t * 30), max_conn - 2),
            "cpu_percent": lambda t, _: min(50 + t * 3, 95),
            "api_latency_ms": lambda t, _: 200 + t * 300,
            "error_rate_percent": lambda t, _: min(1 + t * 2.5, 45),
        },
    },
    "ssl_certificate_expiry": {
        "target_service": "authentication-service",
        "anomalies": {
            "error_rate_percent": lambda t, _: min(5 + t * 8, 100),
            "api_latency_ms": lambda t, _: 100 + t * 50,
            "service_healthy": lambda t, _: False,
        },
    },
    "payment_api_timeout": {
        "target_service": "payment-service",
        "anomalies": {
            "api_latency_ms": lambda t, _: 500 + t * 1500,
            "error_rate_percent": lambda t, _: min(2 + t * 4, 60),
            "cpu_percent": lambda t, _: 30 + t * 2,
        },
    },
    "database_unavailable": {
        "target_service": "payment-service",
        "anomalies": {
            "db_connections": lambda t, _: 0,
            "error_rate_percent": lambda t, _: min(20 + t * 10, 100),
            "api_latency_ms": lambda t, _: 30000,
            "service_healthy": lambda t, _: False,
        },
    },
    "high_cpu": {
        "target_service": "payment-service",
        "anomalies": {
            "cpu_percent": lambda t, _: min(60 + t * 3, 98),
            "api_latency_ms": lambda t, _: 200 + t * 500,
            "error_rate_percent": lambda t, _: min(1 + t * 1.5, 30),
        },
    },
    "memory_leak": {
        "target_service": "payment-service",
        "anomalies": {
            "memory_percent": lambda t, _: min(65 + t * 2.5, 99),
            "cpu_percent": lambda t, _: min(40 + t * 2, 85),
            "api_latency_ms": lambda t, _: 150 + t * 200,
        },
    },
    "kafka_consumer_failure": {
        "target_service": "transaction-service",
        "anomalies": {
            "error_rate_percent": lambda t, _: min(5 + t * 5, 70),
            "transaction_volume_per_min": lambda t, _: max(100 - t * 15, 0),
        },
    },
    "auth_service_failure": {
        "target_service": "authentication-service",
        "anomalies": {
            "error_rate_percent": lambda t, _: min(10 + t * 10, 100),
            "api_latency_ms": lambda t, _: 5000 + t * 1000,
            "service_healthy": lambda t, _: False,
        },
    },
    "third_party_outage": {
        "target_service": "payment-service",
        "anomalies": {
            "error_rate_percent": lambda t, _: min(5 + t * 5, 80),
            "api_latency_ms": lambda t, _: 30000,
        },
    },
    "bad_deployment": {
        "target_service": "payment-service",
        "anomalies": {
            "error_rate_percent": lambda t, _: min(15 + t * 8, 90),
            "cpu_percent": lambda t, _: min(55 + t * 4, 95),
            "api_latency_ms": lambda t, _: 300 + t * 400,
        },
    },
}


def generate_incident_metrics(
    scenario: str,
    pre_incident_minutes: int = 30,
    during_incident_minutes: int = 15,
    incident_start: datetime | None = None,
) -> list[dict]:
    """Generate metrics for an incident scenario.
    Returns normal metrics before the incident + anomalous metrics during.
    """
    profile = ANOMALY_PROFILES.get(scenario)
    if not profile:
        raise ValueError(f"Unknown scenario: {scenario}")

    target_service = profile["target_service"]
    anomalies = profile["anomalies"]

    if incident_start is None:
        incident_start = datetime.now(timezone.utc) - timedelta(minutes=during_incident_minutes)

    # Normal metrics before incident
    metrics = []
    for m in range(pre_incident_minutes, 0, -1):
        ts = incident_start - timedelta(minutes=m)
        baselines = NORMAL_BASELINES[target_service]
        metrics.append({
            "timestamp": ts.isoformat(),
            "service": target_service,
            "cpu_percent": round(random.uniform(*baselines["cpu_percent"]), 1),
            "memory_percent": round(random.uniform(*baselines["memory_percent"]), 1),
            "disk_percent": round(random.uniform(*baselines["disk_percent"]), 1),
            "db_connections": int(random.uniform(*baselines["db_connections"])),
            "db_max_connections": baselines["db_max_connections"],
            "api_latency_ms": round(random.uniform(*baselines["api_latency_ms"]), 1),
            "error_rate_percent": round(random.uniform(*baselines["error_rate_percent"]), 2),
            "request_rate_per_sec": int(random.uniform(*baselines["request_rate_per_sec"])),
            "transaction_volume_per_min": int(random.uniform(*baselines["transaction_volume_per_min"])),
            "service_healthy": True,
        })

    # Anomalous metrics during incident
    baselines = NORMAL_BASELINES[target_service]
    for m in range(during_incident_minutes):
        ts = incident_start + timedelta(minutes=m)
        metric = {
            "timestamp": ts.isoformat(),
            "service": target_service,
            "cpu_percent": round(random.uniform(*baselines["cpu_percent"]), 1),
            "memory_percent": round(random.uniform(*baselines["memory_percent"]), 1),
            "disk_percent": round(random.uniform(*baselines["disk_percent"]), 1),
            "db_connections": int(random.uniform(*baselines["db_connections"])),
            "db_max_connections": baselines["db_max_connections"],
            "api_latency_ms": round(random.uniform(*baselines["api_latency_ms"]), 1),
            "error_rate_percent": round(random.uniform(*baselines["error_rate_percent"]), 2),
            "request_rate_per_sec": int(random.uniform(*baselines["request_rate_per_sec"])),
            "transaction_volume_per_min": int(random.uniform(*baselines["transaction_volume_per_min"])),
            "service_healthy": True,
        }

        # Apply anomalies
        max_conn = baselines["db_max_connections"]
        for key, anomaly_fn in anomalies.items():
            value = anomaly_fn(m, max_conn)
            if isinstance(value, float):
                metric[key] = round(value, 2)
            else:
                metric[key] = value

        metrics.append(metric)

    return metrics
