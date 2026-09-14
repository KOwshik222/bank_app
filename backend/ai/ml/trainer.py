"""
ML Training pipeline — trains and evaluates anomaly detection and classification models.
Uses synthetic data from the simulator for training.
"""

import logging
from pathlib import Path

from simulator.metric_generator import (
    ANOMALY_PROFILES,
    generate_incident_metrics,
    generate_normal_metrics,
)
from ai.ml.anomaly_detector import AnomalyDetector
from ai.ml.incident_classifier import IncidentClassifier

logger = logging.getLogger(__name__)


def train_anomaly_detector(
    model_dir: Path,
    normal_hours: int = 24,
) -> dict:
    """
    Train the Isolation Forest anomaly detector on synthetic normal metrics.
    """
    logger.info("Generating normal training data...")
    all_normal = []
    services = ["payment-service", "account-service", "authentication-service"]

    for service in services:
        metrics = generate_normal_metrics(
            service=service,
            minutes=normal_hours * 60,
        )
        all_normal.extend(metrics)

    logger.info(f"Generated {len(all_normal)} normal metric samples")

    detector = AnomalyDetector()
    result = detector.train(all_normal)
    detector.save(model_dir / "anomaly_detector")

    logger.info(f"Anomaly detector trained and saved: {result}")
    return result


def train_incident_classifier(
    model_dir: Path,
    samples_per_scenario: int = 5,
) -> dict:
    """
    Train the XGBoost incident classifier on synthetic incident metrics.
    """
    logger.info("Generating incident training data...")
    training_data = []

    for scenario_key in ANOMALY_PROFILES:
        for _ in range(samples_per_scenario):
            metrics = generate_incident_metrics(
                scenario=scenario_key,
                pre_incident_minutes=15,
                during_incident_minutes=10,
            )
            training_data.append((metrics, scenario_key))

    logger.info(f"Generated {len(training_data)} incident training scenarios")

    classifier = IncidentClassifier()
    result = classifier.train(training_data)
    classifier.save(model_dir / "incident_classifier")

    logger.info(f"Incident classifier trained and saved: {result}")
    return result


def train_all_models(model_dir: Path) -> dict:
    """Train all ML models."""
    model_dir.mkdir(parents=True, exist_ok=True)

    anomaly_result = train_anomaly_detector(model_dir)
    classifier_result = train_incident_classifier(model_dir)

    return {
        "anomaly_detector": anomaly_result,
        "incident_classifier": classifier_result,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    base_dir = Path(__file__).resolve().parent.parent
    model_dir = base_dir / "ml_models"

    print("=" * 60)
    print("Training ML Models for Banking Incident Resolution Agent")
    print("=" * 60)

    results = train_all_models(model_dir)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nAnomaly Detector:")
    for k, v in results["anomaly_detector"].items():
        print(f"  {k}: {v}")

    print(f"\nIncident Classifier:")
    for k, v in results["incident_classifier"].items():
        if k != "per_class":
            print(f"  {k}: {v}")
        else:
            print(f"  Per-class metrics:")
            for cls, metrics in v.items():
                print(f"    {cls}: P={metrics['precision']:.3f} R={metrics['recall']:.3f} F1={metrics['f1']:.3f}")
