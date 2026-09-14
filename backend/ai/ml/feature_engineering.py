"""
Feature engineering — extracts ML features from raw service metrics.
Computes rolling statistics, rate-of-change, and z-scores.
"""

import numpy as np
import pandas as pd


def engineer_features(metrics: list[dict] | dict) -> pd.DataFrame:
    """
    Transform raw metrics into ML-ready features.

    Input: list of metric dicts with keys like cpu_percent, memory_percent, etc.
    Output: DataFrame with original + engineered features.
    """
    if isinstance(metrics, dict):
        metrics = [metrics]
    df = pd.DataFrame(metrics)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

    # Core numeric features
    numeric_cols = [
        "cpu_percent", "memory_percent", "disk_percent",
        "db_connections", "api_latency_ms", "error_rate_percent",
        "request_rate_per_sec", "transaction_volume_per_min",
    ]

    # Ensure all numeric columns exist
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Connection pool utilization ratio
    if "db_max_connections" in df.columns:
        df["db_pool_utilization"] = (
            df["db_connections"] / df["db_max_connections"].replace(0, 1)
        )
    else:
        df["db_pool_utilization"] = 0.0

    # Rolling statistics (window=5 for smoothing)
    window = min(5, len(df))
    if window >= 2:
        for col in numeric_cols:
            df[f"{col}_rolling_mean"] = df[col].rolling(window=window, min_periods=1).mean()
            df[f"{col}_rolling_std"] = df[col].rolling(window=window, min_periods=1).std().fillna(0)

        # Rate of change
        for col in numeric_cols:
            df[f"{col}_rate_of_change"] = df[col].diff().fillna(0)

        # Z-scores (how many standard deviations from rolling mean)
        for col in numeric_cols:
            std = df[f"{col}_rolling_std"]
            mean = df[f"{col}_rolling_mean"]
            df[f"{col}_zscore"] = ((df[col] - mean) / std.replace(0, 1)).fillna(0)

    # Binary flags
    df["high_cpu"] = (df["cpu_percent"] > 80).astype(int)
    df["high_memory"] = (df["memory_percent"] > 85).astype(int)
    df["high_error_rate"] = (df["error_rate_percent"] > 5).astype(int)
    df["high_latency"] = (df["api_latency_ms"] > 1000).astype(int)
    df["db_pool_critical"] = (df["db_pool_utilization"] > 0.9).astype(int)

    return df


def get_feature_columns() -> list[str]:
    """Return the list of feature columns used for ML models."""
    base_features = [
        "cpu_percent", "memory_percent", "disk_percent",
        "db_connections", "api_latency_ms", "error_rate_percent",
        "request_rate_per_sec", "transaction_volume_per_min",
        "db_pool_utilization",
    ]

    engineered = []
    for col in [
        "cpu_percent", "memory_percent", "disk_percent",
        "db_connections", "api_latency_ms", "error_rate_percent",
        "request_rate_per_sec", "transaction_volume_per_min",
    ]:
        engineered.extend([
            f"{col}_rolling_mean",
            f"{col}_rolling_std",
            f"{col}_rate_of_change",
            f"{col}_zscore",
        ])

    flags = [
        "high_cpu", "high_memory", "high_error_rate",
        "high_latency", "db_pool_critical",
    ]

    return base_features + engineered + flags


def prepare_training_data(
    normal_metrics: list[dict],
    anomalous_metrics: list[dict],
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Prepare labeled training data from normal and anomalous metrics.
    Returns (features_df, labels) where labels: 0=normal, 1=anomalous.
    """
    normal_df = engineer_features(normal_metrics)
    anomalous_df = engineer_features(anomalous_metrics)

    normal_df["label"] = 0
    anomalous_df["label"] = 1

    combined = pd.concat([normal_df, anomalous_df], ignore_index=True)

    feature_cols = get_feature_columns()
    # Only use columns that exist
    available_cols = [c for c in feature_cols if c in combined.columns]

    X = combined[available_cols].fillna(0)
    y = combined["label"].values

    return X, y
