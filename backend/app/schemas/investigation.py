"""Pydantic schemas for investigations and audit logs."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalystNoteCreate(BaseModel):
    analyst_id: str = Field(..., min_length=1, max_length=64)
    content: str = Field(..., min_length=1, max_length=2000)
    note_type: str = Field("general", pattern="^(general|flag|clearance)$")


class AnalystNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    created_at: datetime
    analyst_id: str
    content: str
    note_type: str


class InvestigationReview(BaseModel):
    analyst_id: str = Field(..., min_length=1, max_length=64)
    action: str = Field(..., pattern="^(review|escalate|close|reopen)$")
    verdict: Optional[str] = Field(None, pattern="^(fraud|legitimate|inconclusive)$")
    comment: Optional[str] = Field(None, max_length=1000)


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    created_at: datetime
    actor_id: str
    action: str
    description: str
    before_state: Optional[dict]
    after_state: Optional[dict]


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    priority: str
    assigned_to: Optional[str]
    risk_score: Optional[float]
    risk_level: Optional[str]
    analyst_verdict: Optional[str]
    analyst_id: Optional[str]
    reviewed_at: Optional[datetime]
    notes: list[AnalystNoteOut] = []
    audit_logs: list[AuditLogOut] = []
