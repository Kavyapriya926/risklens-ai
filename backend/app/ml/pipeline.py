"""Training pipeline — trains, evaluates, and persists fraud detection models."""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    auc,
    f1_score,
)

from app.config import settings
from app.ml.features import FraudFeatureTransformer, FEATURE_NAMES

logger = logging.getLogger(__name__)

MODEL_VERSION_FILE = "model_metadata.json"


def load_dataset(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load dataset from CSV or fall back to synthetic data."""
    if csv_path and Path(csv_path).exists():
        df = pd.read_csv(csv_path)
        logger.info("Loaded dataset from %s (%d rows)", csv_path, len(df))
        return df
    # Fall back to generated synthetic data
    from data.generate_data import generate_synthetic_dataset
    logger.info("Generating synthetic dataset for training")
    return generate_synthetic_dataset(n_samples=20000, fraud_rate=0.05, random_state=42)


def train_models(df: pd.DataFrame, model_dir: str | None = None) -> dict:
    """
    Train Logistic Regression and Random Forest models.

    Returns a dict with evaluation metrics and saves models to disk.
    Uses a strict 80/20 stratified train/test split — test set is locked
    before any preprocessing is fit, preventing data leakage.
    """
    model_dir = Path(model_dir or settings.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    if "is_fraud" not in df.columns:
        raise ValueError("Dataset must have an 'is_fraud' column")

    X = df.drop(columns=["is_fraud"])
    y = df["is_fraud"].astype(int)

    # Stratified split — test set locked here, never touched during training
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    logger.info(
        "Split: train=%d (fraud=%d), test=%d (fraud=%d)",
        len(X_train), y_train.sum(), len(X_test), y_test.sum()
    )

    transformer = FraudFeatureTransformer()

    # --- Logistic Regression ---
    lr_pipeline = Pipeline([
        ("features", transformer),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            C=0.1,
            random_state=42,
        )),
    ])
    lr_pipeline.fit(X_train, y_train)

    # --- Random Forest ---
    rf_transformer = FraudFeatureTransformer()
    rf_pipeline = Pipeline([
        ("features", rf_transformer),
        ("clf", RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            class_weight="balanced",
            min_samples_leaf=10,
            random_state=42,
            n_jobs=1,
        )),
    ])
    rf_pipeline.fit(X_train, y_train)

    # --- Evaluate on held-out test set only ---
    lr_metrics = _evaluate(lr_pipeline, X_test, y_test, "logistic_regression")
    rf_metrics = _evaluate(rf_pipeline, X_test, y_test, "random_forest")

    # Select best model by F1-score
    best_name = "random_forest" if rf_metrics["f1_score"] >= lr_metrics["f1_score"] else "logistic_regression"
    best_pipeline = rf_pipeline if best_name == "random_forest" else lr_pipeline

    # Persist models
    joblib.dump(lr_pipeline, model_dir / "lr_model.pkl")
    joblib.dump(rf_pipeline, model_dir / "rf_model.pkl")
    joblib.dump(best_pipeline, model_dir / "best_model.pkl")

    # Save reference statistics for drift detection (from training data only)
    X_train_features = transformer.transform(X_train)
    ref_stats = {
        "mean": X_train_features.mean(axis=0).tolist(),
        "std": X_train_features.std(axis=0).tolist(),
        "feature_names": FEATURE_NAMES,
    }
    with open(model_dir / "reference_stats.json", "w") as f:
        json.dump(ref_stats, f)

    # Save metadata
    version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")
    metadata = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "best_model": best_name,
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "fraud_rate_pct": round(float(y.mean() * 100), 2),
        "lr_metrics": lr_metrics,
        "rf_metrics": rf_metrics,
        "feature_names": FEATURE_NAMES,
        "data_source": "synthetic_demo",
        "disclaimer": (
            "Metrics computed on a genuinely held-out 20% test set. "
            "This model is trained on synthetic demo data for demonstration purposes only. "
            "Do not use for real financial decisions."
        ),
    }
    with open(model_dir / MODEL_VERSION_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Training complete. Best model: %s (F1=%.3f)", best_name, max(rf_metrics["f1_score"], lr_metrics["f1_score"]))
    return metadata


def _evaluate(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series, name: str) -> dict:
    """Compute evaluation metrics on the test set."""
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    threshold = 0.5
    y_pred = (y_proba >= threshold).astype(int)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    precision_vals, recall_vals, pr_thresholds = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(recall_vals, precision_vals)

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    # Sample PR curve (20 points for API response)
    n_points = min(20, len(precision_vals))
    indices = np.linspace(0, len(precision_vals) - 1, n_points, dtype=int)
    pr_curve_points = [
        {"precision": round(float(precision_vals[i]), 4), "recall": round(float(recall_vals[i]), 4)}
        for i in indices
    ]

    return {
        "name": name,
        "precision": round(float(report.get("1", {}).get("precision", 0)), 4),
        "recall": round(float(report.get("1", {}).get("recall", 0)), 4),
        "f1_score": round(float(report.get("1", {}).get("f1-score", 0)), 4),
        "pr_auc": round(float(pr_auc), 4),
        "false_positive_rate": round(float(fpr), 4),
        "confusion_matrix": cm.tolist(),
        "pr_curve_points": pr_curve_points,
        "threshold_used": threshold,
        "support_fraud": int(y_test.sum()),
        "support_total": int(len(y_test)),
    }


def load_metadata(model_dir: str | None = None) -> dict | None:
    """Load saved model metadata."""
    path = Path(model_dir or settings.model_dir) / MODEL_VERSION_FILE
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_best_model(model_dir: str | None = None):
    """Load the best trained model pipeline."""
    path = Path(model_dir or settings.model_dir) / "best_model.pkl"
    if not path.exists():
        raise FileNotFoundError(f"No trained model found at {path}. Run training first.")
    return joblib.load(path)


def load_lr_model(model_dir: str | None = None):
    path = Path(model_dir or settings.model_dir) / "lr_model.pkl"
    return joblib.load(path) if path.exists() else None


def load_rf_model(model_dir: str | None = None):
    path = Path(model_dir or settings.model_dir) / "rf_model.pkl"
    return joblib.load(path) if path.exists() else None
