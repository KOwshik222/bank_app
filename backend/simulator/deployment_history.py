"""
Deployment history module — tracks simulated deployment events, configuration changes,
and rollback capabilities for banking microservices.
"""

from datetime import datetime, timezone
from typing import Any
from simulator.data_generator import generate_deployment_history, SERVICES, DEPLOYMENT_VERSIONS

# In-memory store for active deployments and deployment history
_deployment_store: list[dict[str, Any]] = []


def initialize_deployment_history(days: int = 30) -> list[dict[str, Any]]:
    """Initialize or reset deployment history."""
    global _deployment_store
    _deployment_store = generate_deployment_history(days=days)
    return _deployment_store


def get_deployment_history(service: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve deployment history, optionally filtered by service."""
    global _deployment_store
    if not _deployment_store:
        initialize_deployment_history()
    
    deployments = _deployment_store
    if service:
        deployments = [d for d in deployments if d.get("service") == service]
    
    # Return most recent first
    return sorted(deployments, key=lambda d: d["deployed_at"], reverse=True)[:limit]


def get_latest_deployment(service: str) -> dict[str, Any] | None:
    """Get the most recent deployment for a given service."""
    deployments = get_deployment_history(service=service, limit=1)
    return deployments[0] if deployments else None


def record_deployment(
    service: str,
    version: str,
    deployed_by: str = "ai-remediation-agent",
    config_changes: list[str] | None = None,
    status: str = "SUCCESS",
    notes: str | None = None,
) -> dict[str, Any]:
    """Record a new deployment or rollback."""
    global _deployment_store
    if not _deployment_store:
        initialize_deployment_history()

    latest = get_latest_deployment(service)
    prev_version = latest["version"] if latest else None

    entry = {
        "service": service,
        "version": version,
        "previous_version": prev_version,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "deployed_by": deployed_by,
        "status": status,
        "config_changes": config_changes or [],
        "commit_hash": "rb-" + datetime.now(timezone.utc).strftime("%H%M%S"),
        "notes": notes or f"Deployment of {version} by {deployed_by}",
    }
    _deployment_store.append(entry)
    return entry


def rollback_service(service: str, rolled_back_by: str = "ai-remediation-agent") -> dict[str, Any]:
    """Simulate a rollback of the service to its previous stable version."""
    latest = get_latest_deployment(service)
    if not latest or not latest.get("previous_version"):
        # Fallback to base version if no previous version
        versions = DEPLOYMENT_VERSIONS.get(service, ["v1.0.0"])
        target_version = versions[0]
    else:
        target_version = latest["previous_version"]

    return record_deployment(
        service=service,
        version=target_version,
        deployed_by=rolled_back_by,
        config_changes=["Reverted config changes to stable baseline", "max_connections: restored to 100"],
        status="ROLLED_BACK",
        notes=f"Emergency rollback from {latest['version'] if latest else 'unknown'} to {target_version}",
    )
