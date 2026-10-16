"""Transaction database model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

_utcnow = lambda: datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Raw input fields
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant_category: Mapped[str] = mapped_column(String(64), nullable=False)
    merchant_id: Mapped[str] = mapped_column(String(64), nullable=True)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False)
    is_new_merchant: Mapped[bool] = mapped_column(Boolean, default=False)
    card_age_days: Mapped[int] = mapped_column(Integer, nullable=True)
    velocity_24h: Mapped[int] = mapped_column(Integer, default=1)
    distance_from_home_km: Mapped[float] = mapped_column(Float, nullable=True)

    # ML outputs
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=True)
    model_version: Mapped[str] = mapped_column(String(32), nullable=True)
    prediction_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    feature_contributions: Mapped[dict] = mapped_column(JSON, nullable=True)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=True)

    # Ground truth
    is_fraud_actual: Mapped[bool] = mapped_column(Boolean, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="pending_review")
    batch_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
