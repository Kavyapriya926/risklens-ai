"""Risk threshold simulator endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.schemas.dashboard import SimulatorInput, SimulatorResult
from app.services.risk_engine import simulate_thresholds

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.get("/thresholds")
def get_current_thresholds():
    """Return current threshold configuration."""
    from app.config import settings
    return {
        "low_threshold": settings.low_risk_threshold,
        "high_threshold": settings.medium_risk_threshold,
        "description": "Transactions with risk score >= high_threshold are flagged for review",
    }


@router.post("/simulate", response_model=SimulatorResult)
def run_simulation(payload: SimulatorInput, db: Session = Depends(get_db)):
    """
    Simulate fraud detection outcomes at given thresholds.

    Requires transactions with known ground-truth labels (is_fraud_actual).
    Returns confusion matrix components and estimated costs.
    """
    if payload.low_threshold >= payload.high_threshold:
        raise HTTPException(status_code=400, detail="low_threshold must be less than high_threshold")

    # Load transactions with ground truth
    rows = (
        db.query(Transaction.risk_score, Transaction.is_fraud_actual)
        .filter(Transaction.risk_score != None, Transaction.is_fraud_actual != None)  # noqa: E711
        .all()
    )

    if len(rows) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 10 transactions with ground-truth labels. Found {len(rows)}. "
                   "Upload a CSV with an 'is_fraud_actual' column to run the simulator.",
        )

    scores = [float(r[0]) for r in rows]
    labels = [int(r[1]) for r in rows]

    sim = simulate_thresholds(
        risk_scores=scores,
        actual_labels=labels,
        low_threshold=payload.low_threshold,
        high_threshold=payload.high_threshold,
        review_cost=payload.review_cost_per_case,
        fraud_loss=payload.fraud_loss_per_case,
    )

    # Compute baseline at default thresholds for comparison
    from app.config import settings
    baseline = simulate_thresholds(
        risk_scores=scores,
        actual_labels=labels,
        low_threshold=settings.low_risk_threshold,
        high_threshold=settings.medium_risk_threshold,
        review_cost=payload.review_cost_per_case,
        fraud_loss=payload.fraud_loss_per_case,
    )

    return SimulatorResult(
        threshold_config=payload,
        total_transactions=len(rows),
        detected_fraud=sim["detected_fraud"],
        missed_fraud=sim["missed_fraud"],
        false_positives=sim["false_positives"],
        true_negatives=sim["true_negatives"],
        precision=sim["precision"],
        recall=sim["recall"],
        f1_score=sim["f1_score"],
        estimated_review_cost=sim["estimated_review_cost"],
        estimated_fraud_loss=sim["estimated_fraud_loss"],
        total_cost=sim["total_cost"],
        comparison_baseline=baseline,
    )
