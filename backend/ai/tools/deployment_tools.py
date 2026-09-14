"""
Deployment tools — callable by Deployment Analysis Agent.
Queries recent releases, config diffs, and rollback status.
"""

from typing import Any
from simulator.deployment_history import get_deployment_history, get_latest_deployment


def get_recent_deployments(service: str, limit: int = 5) -> list[dict[str, Any]]:
    """Retrieve recent deployment events and config changes."""
    return get_deployment_history(service=service, limit=limit)


def analyze_deployment_correlation(service: str, incident_time_iso: str | None = None) -> dict[str, Any]:
    """Correlate the most recent deployment with incident symptoms."""
    latest = get_latest_deployment(service)
    if not latest:
        return {"correlated": False, "reason": "No recent deployments found"}

    has_config = bool(latest.get("config_changes"))
    return {
        "correlated": has_config or latest.get("status") != "SUCCESS",
        "latest_version": latest.get("version"),
        "deployed_at": latest.get("deployed_at"),
        "config_changes": latest.get("config_changes", []),
        "previous_version": latest.get("previous_version"),
        "recommendation": "Rollback to previous version if errors started immediately following deployment",
    }
