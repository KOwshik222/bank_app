"""
API tools — callable by API Analysis Agent.
Checks HTTP status codes, latency percentiles, dependencies, and circuit breakers.
"""

from typing import Any


def get_endpoint_health(service: str, scenario: str | None = None) -> dict[str, Any]:
    """Retrieve service health endpoints status."""
    if scenario == "ssl_certificate_expiry" and service in ("authentication-service", "payment-service"):
        return {
            "service": service,
            "status": "DOWN",
            "http_code": 503,
            "tls_handshake_status": "EXPIRED_CERTIFICATE",
            "last_check_ms": 150,
        }
    elif scenario == "payment_api_timeout" and service == "payment-service":
        return {
            "service": service,
            "status": "DEGRADED",
            "http_code": 504,
            "tls_handshake_status": "OK",
            "last_check_ms": 15400,
        }
    elif scenario == "auth_service_failure" and service in ("authentication-service", "payment-service"):
        return {
            "service": service,
            "status": "DOWN",
            "http_code": 503,
            "tls_handshake_status": "OK",
            "last_check_ms": 5200,
        }
    elif scenario == "third_party_outage" and service == "payment-service":
        return {
            "service": service,
            "status": "DEGRADED",
            "http_code": 503,
            "tls_handshake_status": "OK",
            "last_check_ms": 8400,
        }
    elif scenario == "database_unavailable":
        return {
            "service": service,
            "status": "DOWN",
            "http_code": 500,
            "tls_handshake_status": "OK",
            "last_check_ms": 30000,
        }
    return {
        "service": service,
        "status": "UP",
        "http_code": 200,
        "tls_handshake_status": "OK",
        "last_check_ms": 12,
    }


def get_circuit_breaker_status(service: str, scenario: str | None = None) -> dict[str, Any]:
    """Inspect circuit breaker state."""
    if scenario == "payment_api_timeout":
        return {
            "service": service,
            "circuit_breaker_name": "payment-gateway-cb",
            "state": "HALF_OPEN",
            "consecutive_failures": 18,
            "failure_rate_threshold_pct": 50.0,
            "current_failure_rate_pct": 82.5,
        }
    elif scenario == "third_party_outage":
        return {
            "service": service,
            "circuit_breaker_name": "third-party-processor-cb",
            "state": "OPEN",
            "consecutive_failures": 35,
            "failure_rate_threshold_pct": 50.0,
            "current_failure_rate_pct": 96.0,
        }
    return {
        "service": service,
        "circuit_breaker_name": "payment-gateway-cb",
        "state": "CLOSED",
        "consecutive_failures": 0,
        "failure_rate_threshold_pct": 50.0,
        "current_failure_rate_pct": 0.2,
    }

