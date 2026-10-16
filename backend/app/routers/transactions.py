"""Transaction analysis endpoints."""
from __future__ import annotations
import csv
import io
import logging
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.investigation import Investigation
from app.models.transaction import Transaction
from app.ml.explainer import explain_prediction
from app.ml.predictor import get_best_model, predict_single
from app.schemas.transaction import (
    TransactionInput, TransactionResult, TransactionDetail, BatchUploadResult,
)
from app.services.risk_engine import priority_from_risk

router = APIRouter(prefix="/api/transactions", tags=["transactions"])
logger = logging.getLogger(__name__)

ALLOWED_CSV_COLUMNS = {
    "transaction_id", "amount", "merchant_category", "merchant_id",
    "hour_of_day", "day_of_week", "is_international", "is_new_merchant",
    "card_age_days", "velocity_24h", "distance_from_home_km", "is_fraud_actual",
}


@router.post("/analyze", response_model=TransactionResult)
def analyze_transaction(payload: TransactionInput, db: Session = Depends(get_db)):
    """Analyze a single transaction and return a risk score with explanation.

    Returns **409 Conflict** if the supplied ``transaction_id`` already exists.
    Omit ``transaction_id`` (or pass null) to let the server generate a UUID.
    """
    # ── Pre-check: reject duplicates before running expensive ML inference ──
    existing = db.query(Transaction.transaction_id).filter(
        Transaction.transaction_id == payload.transaction_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"transaction_id '{payload.transaction_id}' already exists. "
                "Each transaction must have a unique ID. "
                "Omit transaction_id to have the server generate one automatically."
            ),
        )

    raw = payload.model_dump()

    # Get prediction
    result = predict_single(raw)
    risk_score = result["risk_score"]
    risk_level = result["risk_level"]

    # Generate explanation
    pipeline = get_best_model()
    explanation = explain_prediction(pipeline, raw, risk_score)

    # Persist to DB — wrap commit in IntegrityError guard as a safety net
    # (handles the race-condition window between the pre-check query and the
    # insert in high-concurrency scenarios).
    txn = Transaction(
        transaction_id=payload.transaction_id,
        amount=payload.amount,
        merchant_category=payload.merchant_category,
        merchant_id=payload.merchant_id,
        hour_of_day=payload.hour_of_day,
        day_of_week=payload.day_of_week,
        is_international=payload.is_international,
        is_new_merchant=payload.is_new_merchant,
        card_age_days=payload.card_age_days,
        velocity_24h=payload.velocity_24h,
        distance_from_home_km=payload.distance_from_home_km,
        risk_score=risk_score,
        risk_level=risk_level,
        model_version=result["model_version"],
        prediction_confidence=result["prediction_confidence"],
        feature_contributions={f.feature: f.contribution for f in explanation.factors},
        explanation_text=explanation.evidence_summary,
        is_fraud_actual=payload.is_fraud_actual,
        status="pending_review" if risk_level in ("medium", "high") else "auto_cleared",
    )
    db.add(txn)

    # Create investigation for medium/high risk
    if risk_level in ("medium", "high"):
        inv = Investigation(
            transaction_id=payload.transaction_id,
            status="open",
            priority=priority_from_risk(risk_level, payload.amount),
            risk_score=risk_score,
            risk_level=risk_level,
        )
        db.add(inv)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"transaction_id '{payload.transaction_id}' already exists. "
                "Each transaction must have a unique ID. "
                "Omit transaction_id to have the server generate one automatically."
            ),
        )

    return TransactionResult(
        transaction_id=payload.transaction_id,
        risk_score=risk_score,
        risk_level=risk_level,
        prediction_confidence=result["prediction_confidence"],
        model_version=result["model_version"],
        explanation=explanation,
        processing_time_ms=result["processing_time_ms"],
    )


@router.post("/upload-csv", response_model=BatchUploadResult)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV of transactions for batch analysis."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    # Decode safely
    try:
        text = content.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="Empty or malformed CSV")

    # Validate columns
    unknown_cols = set(reader.fieldnames) - ALLOWED_CSV_COLUMNS
    if unknown_cols:
        logger.warning("Unknown CSV columns (will be ignored): %s", unknown_cols)

    batch_id = str(uuid.uuid4())
    pipeline = get_best_model()
    processed = failed = high_risk = medium_risk = low_risk = 0
    errors: list[str] = []

    rows = list(reader)
    if len(rows) > settings.max_csv_rows:
        raise HTTPException(
            status_code=400,
            detail=f"CSV exceeds {settings.max_csv_rows} rows limit",
        )

    for row_num, row in enumerate(rows, start=2):
        try:
            txn_input = _parse_csv_row(row, row_num)

            # Skip duplicate IDs gracefully (record as a per-row error, not a crash)
            existing = db.query(Transaction.transaction_id).filter(
                Transaction.transaction_id == txn_input.transaction_id
            ).first()
            if existing:
                failed += 1
                errors.append(
                    f"Row {row_num}: transaction_id '{txn_input.transaction_id}' already exists — skipped"
                )
                continue

            raw = txn_input.model_dump()
            result = predict_single(raw)
            explanation = explain_prediction(pipeline, raw, result["risk_score"])

            txn = Transaction(
                transaction_id=txn_input.transaction_id,
                amount=txn_input.amount,
                merchant_category=txn_input.merchant_category,
                merchant_id=txn_input.merchant_id,
                hour_of_day=txn_input.hour_of_day,
                day_of_week=txn_input.day_of_week,
                is_international=txn_input.is_international,
                is_new_merchant=txn_input.is_new_merchant,
                card_age_days=txn_input.card_age_days,
                velocity_24h=txn_input.velocity_24h,
                distance_from_home_km=txn_input.distance_from_home_km,
                risk_score=result["risk_score"],
                risk_level=result["risk_level"],
                model_version=result["model_version"],
                prediction_confidence=result["prediction_confidence"],
                feature_contributions={f.feature: f.contribution for f in explanation.factors},
                explanation_text=explanation.evidence_summary,
                is_fraud_actual=txn_input.is_fraud_actual,
                status="pending_review" if result["risk_level"] in ("medium", "high") else "auto_cleared",
                batch_id=batch_id,
            )
            db.add(txn)

            if result["risk_level"] in ("medium", "high"):
                inv = Investigation(
                    transaction_id=txn_input.transaction_id,
                    status="open",
                    priority=priority_from_risk(result["risk_level"], txn_input.amount),
                    risk_score=result["risk_score"],
                    risk_level=result["risk_level"],
                )
                db.add(inv)

            try:
                if processed % 100 == 0:
                    db.flush()
            except IntegrityError:
                # Race condition: another request inserted the same ID between
                # our pre-check and flush. Roll back this row and continue.
                db.rollback()
                failed += 1
                errors.append(
                    f"Row {row_num}: transaction_id '{txn_input.transaction_id}' "
                    "conflicted on flush — skipped"
                )
                continue

            if result["risk_level"] == "high":
                high_risk += 1
            elif result["risk_level"] == "medium":
                medium_risk += 1
            else:
                low_risk += 1
            processed += 1

        except Exception as e:
            failed += 1
            errors.append(f"Row {row_num}: {str(e)[:100]}")
            if len(errors) > 20:
                errors.append("... additional errors truncated")
                break

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # This should not happen since we pre-check each row, but guard it anyway
        logger.warning("IntegrityError on final CSV commit — some rows may have been lost")

    return BatchUploadResult(
        batch_id=batch_id,
        total_rows=len(rows),
        processed=processed,
        failed=failed,
        high_risk_count=high_risk,
        medium_risk_count=medium_risk,
        low_risk_count=low_risk,
        errors=errors,
    )


@router.get("", response_model=list[TransactionDetail])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    risk_level: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    db: Session = Depends(get_db),
):
    """List transactions with optional risk level filter."""
    q = db.query(Transaction).order_by(Transaction.created_at.desc())
    if risk_level:
        q = q.filter(Transaction.risk_level == risk_level)
    return q.offset(skip).limit(limit).all()


@router.get("/{transaction_id}", response_model=TransactionDetail)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get a specific transaction by transaction_id."""
    txn = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


def _parse_csv_row(row: dict, row_num: int) -> TransactionInput:
    """Parse and validate a CSV row into a TransactionInput."""
    def _bool(v: str) -> bool:
        return str(v).strip().lower() in ("1", "true", "yes")

    def _opt_float(v) -> Optional[float]:
        s = str(v).strip()
        return float(s) if s and s.lower() not in ("", "none", "null", "nan") else None

    def _opt_int(v) -> Optional[int]:
        s = str(v).strip()
        return int(float(s)) if s and s.lower() not in ("", "none", "null", "nan") else None

    return TransactionInput(
        transaction_id=row.get("transaction_id") or None,
        amount=float(row.get("amount", 0)),
        merchant_category=str(row.get("merchant_category", "other")).strip(),
        merchant_id=row.get("merchant_id") or None,
        hour_of_day=int(float(row.get("hour_of_day", 12))),
        day_of_week=int(float(row.get("day_of_week", 0))),
        is_international=_bool(row.get("is_international", "false")),
        is_new_merchant=_bool(row.get("is_new_merchant", "false")),
        card_age_days=_opt_int(row.get("card_age_days")),
        velocity_24h=int(float(row.get("velocity_24h", 1))) or 1,
        distance_from_home_km=_opt_float(row.get("distance_from_home_km")),
        is_fraud_actual=_bool(row.get("is_fraud_actual", "")) if row.get("is_fraud_actual", "").strip() else None,
    )
