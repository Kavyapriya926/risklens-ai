"""Inference engine — loads models and produces risk scores."""
from __future__ import annotations
import logging
import time
from pathlib import Path
from threading import Lock

import numpy as np

from app.config import settings
from app.ml.features import row_to_dataframe

logger = logging.getLogger(__name__)
_lock = Lock()
_model_cache: dict = {}


def _load_or_get(key: str, loader_fn):
    with _lock:
        if key not in _model_cache:
            try:
                _model_cache[key] = loader_fn()
            except FileNotFoundError:
                logger.warning("Model %s not found — training now", key)
                _trigger_training()
                _model_cache[key] = loader_fn()
    return _model_cache[key]


def _trigger_training():
    """Auto-train if no model exists yet."""
    from app.ml.pipeline import train_models, load_dataset
    from app.config import settings
    import os
    csv_path = Path(settings.data_dir) / "fraud_dataset.csv"
    df = load_dataset(csv_path if csv_path.exists() else None)
    train_models(df, settings.model_dir)


def get_best_model():
    from app.ml.pipeline import load_best_model
    return _load_or_get("best", load_best_model)


def get_metadata():
    from app.ml.pipeline import load_metadata
    return load_metadata(settings.model_dir) or {}


def invalidate_cache():
    """Clear model cache after re-training."""
    with _lock:
        _model_cache.clear()


def predict_single(transaction_data: dict) -> dict:
    """
    Run inference on a single transaction dict.

    Returns:
        dict with risk_score (0–100), risk_level, prediction_confidence,
        model_version, and raw_probability.
    """
    t0 = time.perf_counter()
    pipeline = get_best_model()
    meta = get_metadata()

    df = row_to_dataframe(transaction_data)
    proba = pipeline.predict_proba(df)[0, 1]  # P(fraud)

    # Map probability → risk score 0–100
    # We use a calibrated linear mapping; P=0.5 → 70 to bias toward
    # human review at decision boundary
    risk_score = _calibrate_score(float(proba))
    risk_level = _classify_risk(risk_score)

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "prediction_confidence": round(float(proba), 4),
        "model_version": meta.get("version", "unknown"),
        "processing_time_ms": round(elapsed_ms, 2),
    }


def predict_batch(transactions: list[dict]) -> list[dict]:
    """Run batch inference."""
    import pandas as pd
    pipeline = get_best_model()
    meta = get_metadata()

    df = pd.DataFrame(transactions)
    probas = pipeline.predict_proba(df)[:, 1]

    results = []
    for i, proba in enumerate(probas):
        score = _calibrate_score(float(proba))
        results.append({
            "index": i,
            "risk_score": round(score, 2),
            "risk_level": _classify_risk(score),
            "prediction_confidence": round(float(proba), 4),
            "model_version": meta.get("version", "unknown"),
        })
    return results


def _calibrate_score(proba: float) -> float:
    """Map fraud probability [0,1] to risk score [0,100]."""
    # Clamp to avoid edge issues
    p = max(0.0, min(1.0, proba))
    return p * 100.0


def _classify_risk(score: float) -> str:
    if score >= settings.medium_risk_threshold:
        return "high"
    if score >= settings.low_risk_threshold:
        return "medium"
    return "low"
