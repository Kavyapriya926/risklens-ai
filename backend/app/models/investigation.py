"""Investigation and analyst note models."""
import uuid
from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

_utcnow = lambda: datetime.now(timezone.utc)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Investigation state
    status: Mapped[str] = mapped_column(String(32), default="open")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    assigned_to: Mapped[str] = mapped_column(String(64), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=True)

    # Analyst decision
    analyst_verdict: Mapped[str] = mapped_column(String(32), nullable=True)
    analyst_id: Mapped[str] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships — explicitly typed as List to get proper ORM collection behaviour
    notes: Mapped[List["AnalystNote"]] = relationship(
        "AnalystNote", back_populates="investigation",
        cascade="all, delete-orphan", lazy="select"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="investigation",
        cascade="all, delete-orphan", lazy="select"
    )


class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    analyst_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(32), default="general")

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="notes")
