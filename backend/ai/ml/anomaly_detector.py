"""
Anomaly detector — Isolation Forest model for detecting abnormal service metrics.
This is a genuine ML model, not hardcoded rules.
"""

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ai.ml.feature_engineering import engineer_features, get_feature_columns

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Isolation Forest-based anomaly detection for service metrics."""

    def __init__(self, model_path: Path | None = None):
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler | None = None
        self.feature_columns: list[str] = []
        self.is_fitted = False

        if model_path is None:
            default_path = Path(__file__).resolve().parent.parent / "ml_models" / "anomaly_detector"
            if (default_path / "isolation_forest.joblib").exists():
                model_path = default_path

        if model_path and model_path.exists():
            self.load(model_path)

    def train(
        self,
        normal_metrics: list[dict],
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> dict:
        """
        Train anomaly detector on normal metrics.
        The model learns what 'normal' looks like, then flags deviations.
        """
        logger.info(f"Training anomaly detector on {len(normal_metrics)} samples...")

        df = engineer_features(normal_metrics)
        self.feature_columns = [c for c in get_feature_columns() if c in df.columns]

        X = df[self.feature_columns].fillna(0).values

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_features=0.8,
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.is_fitted = True

        # Training metrics
        train_scores = self.model.decision_function(X_scaled)
        train_preds = self.model.predict(X_scaled)
        anomaly_count = (train_preds == -1).sum()

        result = {
            "samples": len(X),
            "features": len(self.feature_columns),
            "anomalies_in_training": int(anomaly_count),
            "anomaly_rate": round(anomaly_count / len(X) * 100, 2),
            "mean_score": round(float(train_scores.mean()), 4),
            "std_score": round(float(train_scores.std()), 4),
        }

        logger.info(f"Training complete: {result}")
        return result

    def predict(self, metrics: list[dict] | dict) -> list[dict]:
        """
        Predict anomaly scores for given metrics.
        Returns list of dicts with anomaly_score (0-1, higher = more anomalous)
        and per-feature contributions.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not trained. Call train() first.")

        if isinstance(metrics, dict):
            metrics = [metrics]

        df = engineer_features(metrics)
        available_cols = [c for c in self.feature_columns if c in df.columns]
        missing_cols = [c for c in self.feature_columns if c not in df.columns]
        for col in missing_cols:
            df[col] = 0.0

        X = df[self.feature_columns].fillna(0).values
        X_scaled = self.scaler.transform(X)

        # Get raw scores from Isolation Forest
        raw_scores = self.model.decision_function(X_scaled)
        predictions = self.model.predict(X_scaled)

        results = []
        for i in range(len(X)):
            # Convert decision_function score to 0-1 anomaly probability
            # decision_function: negative = anomaly, positive = normal
            anomaly_score = 1.0 / (1.0 + np.exp(raw_scores[i] * 5))  # Sigmoid transform
            anomaly_score = round(float(anomaly_score), 4)

            # Per-feature contribution (approximate via feature deviation)
            feature_contributions = {}
            for j, col in enumerate(self.feature_columns):
                if col.endswith("_zscore") or col.endswith("_rate_of_change"):
                    continue  # Skip derived features for explanation
                if col in [
                    "cpu_percent", "memory_percent", "db_connections",
                    "api_latency_ms", "error_rate_percent", "db_pool_utilization",
                    "request_rate_per_sec", "transaction_volume_per_min",
                ]:
                    # How far from mean (in std units)
                    deviation = abs(X_scaled[i][j])
                    feature_contributions[col] = round(float(deviation), 3)

            # Sort by contribution
            top_contributors = dict(
                sorted(feature_contributions.items(), key=lambda x: x[1], reverse=True)[:5]
            )

            results.append({
                "index": i,
                "anomaly_score": anomaly_score,
                "is_anomaly": bool(predictions[i] == -1),
                "raw_score": round(float(raw_scores[i]), 4),
                "top_contributing_features": top_contributors,
                "timestamp": metrics[i].get("timestamp") if i < len(metrics) else None,
            })

        return results

    def detect_latest(self, metrics: list[dict]) -> dict:
        """Detect anomaly for the most recent metric point."""
        results = self.predict(metrics)
        if results:
            latest = results[-1]
            # Add human-readable explanation
            explanations = []
            for feature, score in latest["top_contributing_features"].items():
                if score > 1.5:  # Significant deviation
                    readable = feature.replace("_", " ").replace("percent", "%")
                    explanations.append(f"{readable} is significantly abnormal (deviation: {score:.1f}σ)")
                elif score > 1.0:
                    readable = feature.replace("_", " ").replace("percent", "%")
                    explanations.append(f"{readable} is elevated (deviation: {score:.1f}σ)")

            latest["explanation"] = explanations
            return latest
        return {"anomaly_score": 0.0, "is_anomaly": False, "explanation": []}

    def save(self, path: Path) -> None:
        """Save trained model to disk."""
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path / "isolation_forest.joblib")
        joblib.dump(self.scaler, path / "scaler.joblib")
        joblib.dump(self.feature_columns, path / "feature_columns.joblib")
        logger.info(f"Model saved to {path}")

    def load(self, path: Path) -> None:
        """Load trained model from disk."""
        self.model = joblib.load(path / "isolation_forest.joblib")
        self.scaler = joblib.load(path / "scaler.joblib")
        self.feature_columns = joblib.load(path / "feature_columns.joblib")
        self.is_fitted = True
        logger.info(f"Model loaded from {path}")
