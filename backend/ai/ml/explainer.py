"""
Explainable AI — SHAP-based explanations for ML model predictions.
Provides human-readable feature importance and explanations.
"""

import logging

import numpy as np
import shap

logger = logging.getLogger(__name__)


class ModelExplainer:
    """SHAP-based model explainability for anomaly detection and classification."""

    def __init__(self):
        self._anomaly_explainer = None
        self._classifier_explainer = None

    def explain_anomaly(
        self,
        model,
        scaler,
        feature_columns: list[str],
        X_sample: np.ndarray,
        top_k: int = 5,
    ) -> dict:
        """
        Explain anomaly detection prediction using SHAP.

        Args:
            model: Trained IsolationForest
            scaler: Fitted StandardScaler
            feature_columns: Feature names
            X_sample: Single sample to explain (unscaled)
            top_k: Number of top features to return
        """
        try:
            X_scaled = scaler.transform(X_sample.reshape(1, -1))

            # Use TreeExplainer for Isolation Forest
            if self._anomaly_explainer is None:
                self._anomaly_explainer = shap.TreeExplainer(model)

            shap_values = self._anomaly_explainer.shap_values(X_scaled)

            if isinstance(shap_values, list):
                shap_values = shap_values[0]

            # Get absolute SHAP values for feature importance
            abs_shap = np.abs(shap_values[0])
            top_indices = np.argsort(abs_shap)[::-1][:top_k]

            contributions = []
            for idx in top_indices:
                feature_name = feature_columns[idx] if idx < len(feature_columns) else f"feature_{idx}"
                contributions.append({
                    "feature": feature_name,
                    "shap_value": round(float(shap_values[0][idx]), 4),
                    "abs_importance": round(float(abs_shap[idx]), 4),
                    "feature_value": round(float(X_sample[idx]), 4),
                    "direction": "increases anomaly" if shap_values[0][idx] > 0 else "decreases anomaly",
                })

            return {
                "base_value": round(float(self._anomaly_explainer.expected_value), 4) if hasattr(self._anomaly_explainer, 'expected_value') else 0.0,
                "contributions": contributions,
                "explanation": self._generate_explanation(contributions),
            }

        except Exception as e:
            logger.warning(f"SHAP explanation failed: {e}")
            return {
                "base_value": 0.0,
                "contributions": [],
                "explanation": ["SHAP explanation unavailable for this prediction"],
            }

    def explain_classification(
        self,
        model,
        feature_columns: list[str],
        X_sample: np.ndarray,
        class_names: list[str],
        top_k: int = 5,
    ) -> dict:
        """
        Explain classification prediction using SHAP.
        """
        try:
            if self._classifier_explainer is None:
                self._classifier_explainer = shap.TreeExplainer(model)

            shap_values = self._classifier_explainer.shap_values(X_sample.reshape(1, -1))

            # For multi-class, shap_values is list of arrays
            predicted_class = int(model.predict(X_sample.reshape(1, -1))[0])
            class_name = class_names[predicted_class] if predicted_class < len(class_names) else f"class_{predicted_class}"

            if isinstance(shap_values, list) and len(shap_values) > predicted_class:
                class_shap = shap_values[predicted_class][0]
            elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
                class_shap = shap_values[0, :, predicted_class]
            else:
                class_shap = shap_values[0] if isinstance(shap_values, np.ndarray) else shap_values

            abs_shap = np.abs(class_shap)
            top_indices = np.argsort(abs_shap)[::-1][:top_k]

            contributions = []
            for idx in top_indices:
                feature_name = feature_columns[idx] if idx < len(feature_columns) else f"feature_{idx}"
                contributions.append({
                    "feature": feature_name,
                    "shap_value": round(float(class_shap[idx]), 4),
                    "abs_importance": round(float(abs_shap[idx]), 4),
                    "feature_value": round(float(X_sample[idx]), 4),
                    "direction": f"supports {class_name}" if class_shap[idx] > 0 else f"opposes {class_name}",
                })

            return {
                "predicted_class": class_name,
                "contributions": contributions,
                "explanation": self._generate_explanation(contributions),
            }

        except Exception as e:
            logger.warning(f"SHAP classification explanation failed: {e}")
            return {
                "predicted_class": "unknown",
                "contributions": [],
                "explanation": ["SHAP explanation unavailable"],
            }

    @staticmethod
    def _generate_explanation(contributions: list[dict]) -> list[str]:
        """Generate human-readable explanations from SHAP contributions."""
        explanations = []
        for contrib in contributions:
            feature = contrib["feature"].replace("_", " ")
            value = contrib["feature_value"]
            importance = contrib["abs_importance"]

            if importance > 0.1:
                direction = "increased" if contrib["shap_value"] > 0 else "decreased"
                explanations.append(
                    f"{feature.capitalize()} (value: {value:.1f}) significantly "
                    f"{direction} the prediction (importance: {importance:.3f})"
                )
            elif importance > 0.01:
                explanations.append(
                    f"{feature.capitalize()} (value: {value:.1f}) moderately contributed "
                    f"(importance: {importance:.3f})"
                )

        if not explanations:
            explanations = ["No significant feature contributions identified"]

        return explanations
