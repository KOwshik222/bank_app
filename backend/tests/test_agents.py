import pytest
from ai.tools.log_tools import get_service_logs, search_logs_by_pattern, get_error_summary
from ai.tools.metric_tools import get_service_metrics, run_anomaly_detection, classify_incident_metrics
from ai.tools.db_tools import get_connection_pool_status, get_query_latency, get_db_locks
from ai.tools.deployment_tools import get_recent_deployments, analyze_deployment_correlation
from ai.tools.remediation_tools import restart_service, rollback_deployment, rotate_ssl_certificate, scale_service
from ai.tools.verification_tools import check_api_health, verify_error_rate, verify_transaction_throughput

def test_log_tools():
    logs = get_service_logs("payment-service", minutes=10)
    assert isinstance(logs, list)
    assert len(logs) > 0
    
    summary = get_error_summary(logs)
    assert "total_errors" in summary
    assert "top_signatures" in summary
    
    matches = search_logs_by_pattern("payment-service", "Payment", logs=logs)
    assert isinstance(matches, list)

def test_metric_tools():
    metrics = get_service_metrics("account-service", minutes=10)
    assert isinstance(metrics, list)
    assert len(metrics) > 0
    
    detection = run_anomaly_detection(metrics)
    assert "anomaly_score" in detection
    
    classification = classify_incident_metrics(metrics)
    assert "predicted_class" in classification

def test_db_tools():
    pool = get_connection_pool_status("postgres-primary")
    assert "active_connections" in pool
    
    latency = get_query_latency("postgres-primary")
    assert "p95_latency_ms" in latency

def test_deployment_tools():
    deps = get_recent_deployments("payment-service")
    assert isinstance(deps, list)
    
    analysis = analyze_deployment_correlation("payment-service")
    assert "correlated" in analysis

def test_remediation_and_verification_tools():
    restart = restart_service("payment-service")
    assert restart["status"] == "SUCCESS"
    
    rollback = rollback_deployment("payment-service")
    assert rollback["status"] == "SUCCESS"
    assert "restored_version" in rollback
    
    ssl = rotate_ssl_certificate("auth-service")
    assert ssl["status"] == "SUCCESS"
    
    scale = scale_service("api-gateway", replicas=4)
    assert scale["status"] == "SUCCESS"
    assert scale["new_replica_count"] == 4
    
    api_health = check_api_health("payment-service")
    assert api_health["status"] == "UP"
    assert api_health["is_healthy"] is True
    
    err_rate = verify_error_rate("payment-service")
    assert err_rate["within_limits"] is True
    
    tx_throughput = verify_transaction_throughput("payment-service")
    assert tx_throughput["status"] == "NORMAL"
