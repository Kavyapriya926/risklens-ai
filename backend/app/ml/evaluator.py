"""Load and format saved evaluation metrics for API responses."""
from __future__ import annotations
from app.ml.pipeline import load_metadata
from app.schemas.dashboard import ModelEvaluationReport


def get_evaluation_report(model_name: str = "best") -> ModelEvaluationReport | None:
    """Return evaluation metrics for the specified model."""
    meta = load_metadata()
    if not meta:
        return None

    best = meta.get("best_model", "random_forest")
    if model_name == "best":
        model_name = best

    key = "lr_metrics" if model_name == "logistic_regression" else "rf_metrics"
    metrics_data = meta.get(key, {})

    # Build feature importance list
    import json
    from pathlib import Path
    from app.config import settings
    import joblib

    feature_importances = []
    try:
        if model_name == "random_forest":
            rf = joblib.load(Path(settings.model_dir) / "rf_model.pkl")
            clf = rf.named_steps["clf"]
            from app.ml.features import FEATURE_NAMES, FEATURE_LABELS
            importances = clf.feature_importances_
            feature_importances = [
                {
                    "feature": FEATURE_NAMES[i],
                    "label": FEATURE_LABELS.get(FEATURE_NAMES[i], FEATURE_NAMES[i]),
                    "importance": round(float(importances[i]), 4),
                }
                for i in np.argsort(importances)[::-1]
            ]
        elif model_name == "logistic_regression":
            lr = joblib.load(Path(settings.model_dir) / "lr_model.pkl")
            clf = lr.named_steps["clf"]
            from app.ml.features import FEATURE_NAMES, FEATURE_LABELS
            import numpy as np
            coefs = np.abs(clf.coef_[0])
            feature_importances = [
                {
                    "feature": FEATURE_NAMES[i],
                    "label": FEATURE_LABELS.get(FEATURE_NAMES[i], FEATURE_NAMES[i]),
                    "importance": round(float(coefs[i]), 4),
                }
                for i in np.argsort(coefs)[::-1]
            ]
    except Exception:
        pass

    metrics_summary = {
        "precision": metrics_data.get("precision", 0),
        "recall": metrics_data.get("recall", 0),
        "f1_score": metrics_data.get("f1_score", 0),
        "pr_auc": metrics_data.get("pr_auc", 0),
        "false_positive_rate": metrics_data.get("false_positive_rate", 0),
    }

    return ModelEvaluationReport(
        model_name=model_name,
        model_version=meta.get("version", "unknown"),
        trained_at=meta.get("trained_at", ""),
        dataset_size=meta.get("dataset_size", 0),
        train_size=meta.get("train_size", 0),
        test_size=meta.get("test_size", 0),
        fraud_rate_pct=meta.get("fraud_rate_pct", 0),
        metrics=metrics_summary,
        confusion_matrix=metrics_data.get("confusion_matrix", [[0, 0], [0, 0]]),
        threshold_used=metrics_data.get("threshold_used", 0.5),
        pr_curve_points=metrics_data.get("pr_curve_points", []),
        feature_importances=feature_importances,
        disclaimer=meta.get("disclaimer", ""),
    )


import numpy as np  # noqa: E402 (needed by evaluator above)
