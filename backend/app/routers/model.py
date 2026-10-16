"""Model evaluation and monitoring endpoints."""
from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.evaluator import get_evaluation_report
from app.schemas.dashboard import ModelEvaluationReport, DriftReport

router = APIRouter(prefix="/api/model", tags=["model"])
logger = logging.getLogger(__name__)


@router.get("/evaluation", response_model=ModelEvaluationReport)
def get_model_evaluation(model_name: str = Query("best", pattern="^(best|logistic_regression|random_forest)$")):
    """Return evaluation metrics for the trained model."""
    report = get_evaluation_report(model_name)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="No trained model found. POST /api/model/train to train a model first.",
        )
    return report


@router.get("/monitoring")
def get_model_monitoring(db: Session = Depends(get_db)):
    """Return model version info and data drift report."""
    from app.ml.pipeline import load_metadata
    from app.services.drift_monitor import compute_drift_report
    from app.models.transaction import Transaction
    from datetime import datetime, timedelta, timezone

    meta = load_metadata()
    if not meta:
        raise HTTPException(status_code=404, detail="No trained model found.")

    # Get recent transactions for drift detection
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent = (
        db.query(Transaction)
        .filter(Transaction.created_at >= thirty_days_ago)
        .limit(500)
        .all()
    )

    recent_dicts = [
        {
            "amount": t.amount,
            "merchant_category": t.merchant_category,
            "hour_of_day": t.hour_of_day,
            "day_of_week": t.day_of_week,
            "is_international": t.is_international,
            "is_new_merchant": t.is_new_merchant,
            "card_age_days": t.card_age_days or 365,
            "velocity_24h": t.velocity_24h,
            "distance_from_home_km": t.distance_from_home_km or 0,
        }
        for t in recent
    ]

    drift = compute_drift_report(recent_dicts)

    return {
        "model_version": meta.get("version"),
        "trained_at": meta.get("trained_at"),
        "best_model": meta.get("best_model"),
        "dataset_size": meta.get("dataset_size"),
        "fraud_rate_pct": meta.get("fraud_rate_pct"),
        "data_source": meta.get("data_source"),
        "disclaimer": meta.get("disclaimer"),
        "drift_report": drift,
    }


@router.post("/train")
def train_model(background_tasks: BackgroundTasks):
    """Trigger model re-training in the background."""
    from app.ml.predictor import invalidate_cache

    def _train():
        from app.ml.pipeline import train_models, load_dataset
        from app.config import settings
        from pathlib import Path
        csv_path = Path(settings.data_dir) / "fraud_dataset.csv"
        df = load_dataset(csv_path if csv_path.exists() else None)
        train_models(df, settings.model_dir)
        invalidate_cache()
        logger.info("Re-training complete")

    background_tasks.add_task(_train)
    return {"message": "Model training started in background. Check /api/model/evaluation once complete."}


@router.get("/versions")
def list_model_versions():
    """Return available model versions."""
    meta = get_evaluation_report()
    if not meta:
        return {"versions": []}
    return {
        "versions": [
            {"name": "logistic_regression", "description": "Linear baseline"},
            {"name": "random_forest", "description": "Tree-based ensemble"},
        ],
        "best_model": meta.model_name,
        "version": meta.model_version,
    }
