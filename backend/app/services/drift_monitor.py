"""Basic data drift detection using reference vs. current feature distributions."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from app.config import settings
from app.ml.features import FEATURE_NAMES, FEATURE_LABELS

logger = logging.getLogger(__name__)

# PSI thresholds (Population Stability Index)
PSI_LOW = 0.1
PSI_HIGH = 0.25


def _load_reference_stats() -> dict | None:
    path = Path(settings.model_dir) / "reference_stats.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """Compute Population Stability Index between two distributions."""
    min_val = min(expected.min(), actual.min())
    max_val = max(expected.max(), actual.max())
    if max_val == min_val:
        return 0.0

    breakpoints = np.linspace(min_val, max_val, buckets + 1)
    expected_pcts = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_pcts = np.histogram(actual, breakpoints)[0] / len(actual)

    # Avoid log(0)
    expected_pcts = np.where(expected_pcts == 0, 1e-4, expected_pcts)
    actual_pcts = np.where(actual_pcts == 0, 1e-4, actual_pcts)

    return float(np.sum((actual_pcts - expected_pcts) * np.log(actual_pcts / expected_pcts)))


def compute_drift_report(recent_transactions: list[dict]) -> dict:
    """
    Compare recent transaction feature distributions against training reference.

    Returns a drift report with per-feature PSI values and recommendations.
    """
    ref = _load_reference_stats()
    if ref is None:
        return {"error": "No reference statistics found. Train a model first."}

    if len(recent_transactions) < 20:
        return {
            "model_version": "unknown",
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "reference_period": "training data",
            "current_period": "last 30 days",
            "feature_drift": [],
            "overall_drift_detected": False,
            "drift_severity": "insufficient_data",
            "recommendation": f"Only {len(recent_transactions)} recent transactions found. Need at least 20 for drift analysis.",
        }

    import pandas as pd
    from app.ml.features import FraudFeatureTransformer, row_to_dataframe

    # Build feature matrix from recent transactions
    df = pd.DataFrame(recent_transactions)
    transformer = FraudFeatureTransformer()
    # Use reference stats for z-score (to be comparable)
    transformer._category_stats = {}  # bare transform without per-category fit
    try:
        recent_features = transformer.fit_transform(df)
    except Exception as e:
        logger.warning("Drift transform error: %s", e)
        recent_features = np.zeros((len(recent_transactions), len(FEATURE_NAMES)))

    ref_means = np.array(ref["mean"])
    ref_stds = np.array(ref["std"])

    feature_drift = []
    high_drift_count = 0

    for i, fname in enumerate(FEATURE_NAMES):
        ref_dist = np.random.normal(ref_means[i], max(ref_stds[i], 1e-6), 1000)
        current_dist = recent_features[:, i]

        psi = _psi(ref_dist, current_dist)
        mean_shift = abs(float(current_dist.mean()) - ref_means[i])
        severity = "high" if psi >= PSI_HIGH else "medium" if psi >= PSI_LOW else "low"

        if severity in ("medium", "high"):
            high_drift_count += 1

        feature_drift.append({
            "feature": fname,
            "label": FEATURE_LABELS.get(fname, fname),
            "psi": round(psi, 4),
            "severity": severity,
            "ref_mean": round(ref_means[i], 4),
            "current_mean": round(float(current_dist.mean()), 4),
            "mean_shift": round(mean_shift, 4),
        })

    overall_drift = high_drift_count >= 3
    if high_drift_count >= 5:
        drift_severity = "high"
        recommendation = "Significant drift detected in multiple features. Consider retraining the model."
    elif high_drift_count >= 2:
        drift_severity = "medium"
        recommendation = "Moderate drift detected. Monitor closely and consider retraining if performance degrades."
    else:
        drift_severity = "low"
        recommendation = "No significant drift detected. Model appears stable."

    from app.ml.pipeline import load_metadata
    meta = load_metadata() or {}

    return {
        "model_version": meta.get("version", "unknown"),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_period": f"Training data ({meta.get('trained_at', 'unknown')[:10]})",
        "current_period": "Last 30 days",
        "feature_drift": feature_drift,
        "overall_drift_detected": overall_drift,
        "drift_severity": drift_severity,
        "recommendation": recommendation,
    }
