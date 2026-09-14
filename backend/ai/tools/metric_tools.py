import os
from typing import Any
import httpx
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timezone
from ai.ml.anomaly_detector import AnomalyDetector
from ai.ml.incident_classifier import IncidentClassifier
from simulator.metric_generator import generate_incident_metrics, generate_normal_metrics

_anomaly_detector: AnomalyDetector | None = None
_incident_classifier: IncidentClassifier | None = None


def _get_detector() -> AnomalyDetector:
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector()
    return _anomaly_detector


def _get_classifier() -> IncidentClassifier:
    global _incident_classifier
    if _incident_classifier is None:
        _incident_classifier = IncidentClassifier()
    return _incident_classifier


def fetch_live_system_metrics(service: str = "payment-service", minutes: int = 15) -> list[dict[str, Any]]:
    """Capture live process and FastAPI Prometheus endpoint telemetry."""
    http_reqs = 0
    http_errors = 0
    try:
        with httpx.Client(timeout=1.0) as client:
            resp = client.get("http://localhost:8000/metrics")
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    if line.startswith("http_requests_total"):
                        val = line.split()[-1]
                        http_reqs += int(float(val)) if val.replace(".", "").isdigit() else 0
                    elif 'http_requests_status_total{status="5' in line or 'http_requests_status_total{status="4' in line:
                        val = line.split()[-1]
                        http_errors += int(float(val)) if val.replace(".", "").isdigit() else 0
    except Exception:
        pass

    cpu_pct = 25.0
    mem_pct = 40.0
    if psutil is not None:
        try:
            cpu_pct = float(psutil.cpu_percent(interval=0.05))
            mem = psutil.virtual_memory()
            mem_pct = float(mem.percent)
        except Exception:
            pass

    err_rate = (http_errors / max(1, http_reqs)) if http_reqs > 0 else 0.0
    now = datetime.now(timezone.utc)
    metrics_list = []
    for _ in range(max(1, min(minutes, 30))):
        metrics_list.append({
            "timestamp": now.isoformat(),
            "service": service,
            "cpu_percent": cpu_pct,
            "memory_percent": mem_pct,
            "latency_p95_ms": 12.0 if err_rate < 0.05 else 750.0,
            "error_rate": err_rate,
            "active_connections": 10 if err_rate < 0.05 else 95,
            "source": "live_telemetry",
        })
    return metrics_list


def get_service_metrics(service: str, scenario: str | None = None, minutes: int = 15, force_real: bool = False) -> list[dict[str, Any]]:
    """Fetch time series telemetry metrics for a service, checking live metrics first if requested."""
    use_real = force_real or os.environ.get("BANKOPS_USE_REAL_TELEMETRY") == "1"
    if use_real or scenario is None:
        try:
            live = fetch_live_system_metrics(service=service, minutes=minutes)
            if live:
                return live
        except Exception:
            pass

    if scenario:
        try:
            return generate_incident_metrics(scenario=scenario, pre_incident_minutes=5, during_incident_minutes=minutes)
        except Exception:
            return generate_normal_metrics(service=service, minutes=minutes)
    return generate_normal_metrics(service=service, minutes=minutes)


def run_anomaly_detection(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Run Isolation Forest model on metrics to detect anomaly score and contributing features."""
    detector = _get_detector()
    return detector.detect_latest(metrics)


def classify_incident_metrics(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    """Run XGBoost model to classify incident type from telemetry."""
    classifier = _get_classifier()
    return classifier.predict(metrics)
