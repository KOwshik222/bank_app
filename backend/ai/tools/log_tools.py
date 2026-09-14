import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from simulator.log_generator import generate_incident_logs, generate_normal_logs


def _find_real_log_file() -> Path | None:
    """Discover real banking application log file if present."""
    candidates = [
        Path("logs/banking_app.log"),
        Path("backend/logs/banking_app.log"),
        Path(__file__).resolve().parent.parent.parent / "logs" / "banking_app.log",
        Path("app.log"),
    ]
    for c in candidates:
        if c.exists() and c.is_file() and c.stat().st_size > 0:
            return c
    return None


def read_real_logs(log_file_path: Path | str | None = None, minutes: int = 15, max_lines: int = 500) -> list[dict[str, Any]]:
    """Read and parse real log records from persistent disk log."""
    target_path = Path(log_file_path) if log_file_path else _find_real_log_file()
    if not target_path or not target_path.exists():
        return []

    parsed_logs: list[dict[str, Any]] = []
    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-max_lines:]

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Attempt JSON parse
            try:
                data = json.loads(line_str)
                if isinstance(data, dict):
                    level = str(data.get("level") or data.get("log_level") or "INFO").upper()
                    service = str(data.get("service") or data.get("logger") or "banking-service")
                    msg = str(data.get("message") or data.get("event") or "")
                    exc = data.get("exception") or data.get("exc_info") or ""
                    ts = data.get("timestamp") or datetime.now(timezone.utc).isoformat()
                    parsed_logs.append({
                        "timestamp": ts,
                        "level": level,
                        "service": service,
                        "message": msg,
                        "exception": str(exc) if exc else None,
                        "source": "live_log_file",
                    })
                    continue
            except json.JSONDecodeError:
                pass

            # Fallback text parse
            level = "INFO"
            for lvl in ("CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "DEBUG"):
                if lvl in line_str.upper():
                    level = "ERROR" if lvl in ("CRITICAL", "FATAL", "ERROR") else lvl
                    break

            parsed_logs.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "service": "banking-service",
                "message": line_str,
                "exception": line_str if level in ("ERROR", "CRITICAL", "FATAL") else None,
                "source": "live_log_file",
            })
    except Exception:
        return []

    return parsed_logs


def get_service_logs(
    service: str,
    scenario: str | None = None,
    minutes: int = 15,
    level: str | None = None,
    force_real: bool = False,
) -> list[dict[str, Any]]:
    """Retrieve structured logs for a service, checking real log file first if available."""
    use_real = force_real or os.environ.get("BANKOPS_USE_REAL_TELEMETRY") == "1"
    real_logs: list[dict[str, Any]] = []

    if use_real or scenario is None:
        real_logs = read_real_logs(minutes=minutes)

    if real_logs:
        logs = real_logs
    elif scenario:
        try:
            logs = generate_incident_logs(scenario=scenario, during_incident_minutes=minutes)
        except Exception:
            logs = generate_normal_logs(minutes=minutes)
    else:
        logs = generate_normal_logs(minutes=minutes)

    if service and any(l.get("service") == service for l in logs):
        service_logs = [l for l in logs if l.get("service") == service]
        if service_logs:
            logs = service_logs

    if level:
        logs = [l for l in logs if l.get("level") == level.upper()]

    return logs


def search_logs_by_pattern(service: str, pattern: str, logs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Search log messages matching regex or keyword pattern."""
    if logs is None:
        logs = get_service_logs(service=service, minutes=20)

    pattern_lower = pattern.lower()
    matches = [
        l for l in logs
        if pattern_lower in (l.get("message") or "").lower() or pattern_lower in (l.get("exception") or "").lower()
    ]
    return matches


def get_error_summary(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate error frequencies and identify top exception signatures."""
    error_counts: dict[str, int] = {}
    fatal_count = 0
    error_count = 0

    for l in logs:
        level = l.get("level", "INFO")
        if level in ("ERROR", "FATAL", "CRITICAL"):
            if level == "FATAL":
                fatal_count += 1
            else:
                error_count += 1
            exc = l.get("exception") or l.get("message", "Unknown error")
            exc_sig = exc.split(":")[0][:60]
            error_counts[exc_sig] = error_counts.get(exc_sig, 0) + 1

    return {
        "total_errors": error_count + fatal_count,
        "fatal_count": fatal_count,
        "error_count": error_count,
        "top_signatures": dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]),
    }
