"""Pydantic schemas for transactions."""
from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TransactionInput(BaseModel):
    """Input schema for a single transaction to analyze.

    ``transaction_id`` is optional.  If omitted (or left as null/empty) the
    server generates a UUID automatically.  Supplying an ID that already exists
    in the database returns HTTP 409 Conflict — use the returned transaction_id
    from the first call to look up that record instead.
    """
    transaction_id: Optional[str] = Field(
        default=None,
        description=(
            "Caller-supplied stable identifier for this payment transaction. "
            "Must be alphanumeric plus dashes/underscores, 1–64 chars. "
            "Omit (or pass null) to have the server generate a UUID. "
            "Re-submitting an existing ID returns 409 Conflict."
        ),
        json_schema_extra={"example": None},  # suppress the Swagger "string" placeholder
    )
    amount: float = Field(..., gt=0, le=10_000_000, description="Transaction amount in INR")
    merchant_category: str = Field(..., min_length=1, max_length=64)
    merchant_id: Optional[str] = Field(None, max_length=64)
    hour_of_day: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    is_international: bool = False
    is_new_merchant: bool = False
    card_age_days: Optional[int] = Field(None, ge=0, le=36500)
    velocity_24h: int = Field(1, ge=1, le=1000, description="Transactions in last 24 hours")
    distance_from_home_km: Optional[float] = Field(None, ge=0, le=50000)
    is_fraud_actual: Optional[bool] = None  # Ground truth for evaluation

    @field_validator("merchant_category")
    @classmethod
    def sanitize_merchant_category(cls, v: str) -> str:
        allowed = {
            "retail", "food_beverage", "travel", "electronics", "utilities",
            "entertainment", "healthcare", "education", "financial_services",
            "online_marketplace", "fuel", "grocery", "jewelry", "gaming", "other"
        }
        v = v.lower().strip()
        return v if v in allowed else "other"

    @model_validator(mode="before")
    @classmethod
    def ensure_transaction_id(cls, data):
        if isinstance(data, dict):
            tid = data.get("transaction_id")
            if tid is None or (isinstance(tid, str) and tid.strip() == ""):
                data["transaction_id"] = str(uuid.uuid4())
            else:
                tid = str(tid).strip()
                if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', tid):
                    raise ValueError("transaction_id must be alphanumeric with dashes/underscores only")
                data["transaction_id"] = tid
        return data


class FeatureContribution(BaseModel):
    feature: str
    value: float
    contribution: float
    direction: str  # "increases_risk" / "decreases_risk" / "neutral"
    human_label: str


class RiskExplanation(BaseModel):
    primary_reason: str
    factors: list[FeatureContribution]
    evidence_summary: str


class TransactionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    risk_score: float
    risk_level: str  # low / medium / high
    prediction_confidence: float
    model_version: str
    explanation: RiskExplanation
    processing_time_ms: float


class TransactionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    created_at: datetime
    amount: float
    merchant_category: str
    merchant_id: Optional[str]
    hour_of_day: int
    day_of_week: int
    is_international: bool
    is_new_merchant: bool
    card_age_days: Optional[int]
    velocity_24h: int
    distance_from_home_km: Optional[float]
    risk_score: Optional[float]
    risk_level: Optional[str]
    model_version: Optional[str]
    prediction_confidence: Optional[float]
    explanation_text: Optional[str]
    feature_contributions: Optional[dict]
    status: str
    is_fraud_actual: Optional[bool]


class BatchUploadResult(BaseModel):
    batch_id: str
    total_rows: int
    processed: int
    failed: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    errors: list[str]
