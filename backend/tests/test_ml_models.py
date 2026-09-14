import pytest
from ai.ml.feature_engineering import engineer_features
from ai.ml.anomaly_detector import AnomalyDetector
from ai.ml.incident_classifier import IncidentClassifier

def test_feature_engineering_single_and_list():
    raw_metric = {
        "cpu_percent": 88.5,
        "memory_percent": 92.0,
        "db_connections": 98,
        "db_max_connections": 100,
        "api_latency_ms": 450.0,
        "error_rate_percent": 12.0,
        "request_rate_per_sec": 150
    }
    df = engineer_features(raw_metric)
    assert "cpu_percent" in df.columns
    assert "db_pool_utilization" in df.columns
    assert df["db_pool_utilization"].iloc[0] == 0.98

    # Test list of metric dicts
    series = [raw_metric, {**raw_metric, "cpu_percent": 95.0, "api_latency_ms": 600.0}]
    df_series = engineer_features(series)
    assert len(df_series) == 2
    assert "cpu_percent" in df_series.columns

def test_anomaly_detector_scoring():
    detector = AnomalyDetector()
    
    # Normal metrics baseline
    normal_metrics = [
        {
            "cpu_percent": 25.0,
            "memory_percent": 35.0,
            "db_connections": 15,
            "db_max_connections": 100,
            "api_latency_ms": 45.0,
            "error_rate_percent": 0.1,
            "request_rate_per_sec": 50,
            "transaction_volume_per_min": 300
        }
    ]
    normal_preds = detector.predict(normal_metrics)
    assert len(normal_preds) == 1
    assert "anomaly_score" in normal_preds[0]
    
    # Anomalous metrics (DB exhaustion)
    anomalous_metrics = [
        {
            "cpu_percent": 98.0,
            "memory_percent": 95.0,
            "db_connections": 100,
            "db_max_connections": 100,
            "api_latency_ms": 5200.0,
            "error_rate_percent": 65.0,
            "request_rate_per_sec": 20,
            "transaction_volume_per_min": 5
        }
    ]
    anom_preds = detector.predict(anomalous_metrics)
    assert len(anom_preds) == 1
    assert anom_preds[0]["anomaly_score"] > normal_preds[0]["anomaly_score"]
    assert anom_preds[0]["anomaly_score"] > 0.5

def test_incident_classifier_prediction():
    classifier = IncidentClassifier()
    
    sample_metrics = [
        {
            "cpu_percent": 95.0,
            "memory_percent": 85.0,
            "db_connections": 100,
            "db_max_connections": 100,
            "api_latency_ms": 3500.0,
            "error_rate_percent": 45.0,
            "request_rate_per_sec": 10,
            "transaction_volume_per_min": 15
        }
    ]
    prediction = classifier.predict(sample_metrics)
    assert "predicted_class" in prediction
    assert "confidence" in prediction
    assert "top_predictions" in prediction
    assert prediction["confidence"] > 0.0
