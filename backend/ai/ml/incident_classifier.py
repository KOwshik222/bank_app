"""
Incident classifier — XGBoost multi-class classifier for incident categorization.
Predicts the type of incident based on metric features.
"""

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from xgboost import XGBClassifier

from ai.ml.feature_engineering import engineer_features, get_feature_columns

logger = logging.getLogger(__name__)

# Incident class labels
INCIDENT_CLASSES = [
    "db_connection_exhaustion",
    "ssl_certificate_expiry",
    "payment_api_timeout",
    "database_unavailable",
    "high_cpu",
    "memory_leak",
    "kafka_consumer_failure",
    "auth_service_failure",
    "third_party_outage",
    "bad_deployment",
]

CLASS_TO_IDX = {c: i for i, c in enumerate(INCIDENT_CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(INCIDENT_CLASSES)}


class IncidentClassifier:
    """XGBoost-based incident type classifier."""

    def __init__(self, model_path: Path | None = None):
        self.model: XGBClassifier | None = None
        self.feature_columns: list[str] = []
        self.is_fitted = False

        if model_path is None:
            default_path = Path(__file__).resolve().parent.parent / "ml_models" / "incident_classifier"
            if (default_path / "xgboost_classifier.json").exists():
                model_path = default_path

        if model_path and model_path.exists():
            self.load(model_path)

    def train(
        self,
        training_data: list[tuple[list[dict], str]],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict:
        """
        Train incident classifier.

        Args:
            training_data: list of (metrics_list, incident_class) tuples
            test_size: fraction of data for evaluation
            random_state: random seed
        """
        logger.info(f"Training incident classifier on {len(training_data)} scenarios...")

        all_features = []
        all_labels = []

        for metrics, incident_class in training_data:
            df = engineer_features(metrics)
            if not self.feature_columns:
                self.feature_columns = [c for c in get_feature_columns() if c in df.columns]

            # Use the last N rows (most representative of the incident state)
            incident_rows = df.tail(min(10, len(df)))
            for _, row in incident_rows.iterrows():
                features = [row.get(c, 0.0) for c in self.feature_columns]
                all_features.append(features)
                all_labels.append(CLASS_TO_IDX.get(incident_class, 0))

        X = np.array(all_features)
        y = np.array(all_labels)

        # Split for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Train XGBoost
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            min_child_weight=2,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric="mlogloss",
            verbosity=0,
        )
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self.is_fitted = True

        # Evaluation
        y_pred = self.model.predict(X_test)
        report = classification_report(
            y_test, y_pred,
            target_names=[IDX_TO_CLASS[i] for i in range(len(INCIDENT_CLASSES))],
            output_dict=True,
            zero_division=0,
        )

        result = {
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(report["accuracy"], 4),
            "macro_f1": round(report["macro avg"]["f1-score"], 4),
            "weighted_f1": round(report["weighted avg"]["f1-score"], 4),
            "per_class": {
                IDX_TO_CLASS[i]: {
                    "precision": round(report[IDX_TO_CLASS[i]]["precision"], 4),
                    "recall": round(report[IDX_TO_CLASS[i]]["recall"], 4),
                    "f1": round(report[IDX_TO_CLASS[i]]["f1-score"], 4),
                }
                for i in range(len(INCIDENT_CLASSES))
                if IDX_TO_CLASS[i] in report
            },
        }

        logger.info(f"Training complete: accuracy={result['accuracy']}, f1={result['macro_f1']}")
        return result

    def predict(self, metrics: list[dict] | dict) -> dict:
        """
        Predict incident type from metrics.
        Returns predicted class, confidence, and top-3 predictions.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not trained. Call train() first.")

        if isinstance(metrics, dict):
            metrics = [metrics]

        df = engineer_features(metrics)
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0

        # Use latest metric points for prediction
        latest_rows = df.tail(min(5, len(df)))
        X = latest_rows[self.feature_columns].fillna(0).values

        # Get probabilities
        probabilities = self.model.predict_proba(X)
        avg_probs = probabilities.mean(axis=0)

        # Top-3 predictions
        top_indices = np.argsort(avg_probs)[::-1][:3]
        predictions = []
        for idx in top_indices:
            predictions.append({
                "incident_type": IDX_TO_CLASS[idx],
                "confidence": round(float(avg_probs[idx]), 4),
                "human_readable": IDX_TO_CLASS[idx].replace("_", " ").title(),
            })

        return {
            "predicted_class": predictions[0]["incident_type"],
            "confidence": predictions[0]["confidence"],
            "top_predictions": predictions,
        }

    def save(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        self.model.save_model(str(path / "xgboost_classifier.json"))
        joblib.dump(self.feature_columns, path / "classifier_features.joblib")
        logger.info(f"Classifier saved to {path}")

    def load(self, path: Path) -> None:
        self.model = XGBClassifier()
        self.model.load_model(str(path / "xgboost_classifier.json"))
        self.feature_columns = joblib.load(path / "classifier_features.joblib")
        self.is_fitted = True
        logger.info(f"Classifier loaded from {path}")
