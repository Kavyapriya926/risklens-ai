"""Investigation workbench endpoints."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.investigation import Investigation, AnalystNote
from app.schemas.investigation import (
    InvestigationOut, InvestigationReview, AnalystNoteCreate, AnalystNoteOut, AuditLogOut,
)
from app.services.audit import record_action, get_audit_history, get_investigation_state

router = APIRouter(prefix="/api/investigations", tags=["investigations"])
logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "open": {"review", "escalate", "close"},
    "reviewed": {"escalate", "reopen", "close"},
    "escalated": {"review", "close"},
    "closed": {"reopen"},
}


@router.get("", response_model=list[InvestigationOut])
def list_investigations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    """List investigations with optional filters."""
    q = (
        db.query(Investigation)
        .options(selectinload(Investigation.notes), selectinload(Investigation.audit_logs))
        .order_by(Investigation.created_at.desc())
    )
    if status:
        q = q.filter(Investigation.status == status)
    if priority:
        q = q.filter(Investigation.priority == priority)
    if search:
        q = q.filter(Investigation.transaction_id.ilike(f"%{search}%"))
    results = q.offset(skip).limit(limit).all()
    # Materialize related collections while session is still open
    return [_inv_to_out(inv) for inv in results]


@router.get("/{investigation_id}", response_model=InvestigationOut)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = _get_or_404(db, investigation_id)
    return _inv_to_out(inv)


@router.post("/{investigation_id}/review", response_model=InvestigationOut)
def review_investigation(
    investigation_id: str,
    payload: InvestigationReview,
    db: Session = Depends(get_db),
):
    """Submit an analyst review action (review / escalate / close / reopen)."""
    inv = _get_or_404(db, investigation_id)

    # Validate state transition
    allowed = VALID_TRANSITIONS.get(inv.status, set())
    if payload.action not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Action '{payload.action}' not allowed from status '{inv.status}'. Allowed: {sorted(allowed)}",
        )

    before = get_investigation_state(inv)

    # Apply transition
    status_map = {
        "review": "reviewed",
        "escalate": "escalated",
        "close": "closed",
        "reopen": "open",
    }
    inv.status = status_map[payload.action]
    inv.analyst_id = payload.analyst_id
    inv.updated_at = datetime.now(timezone.utc)

    if payload.verdict:
        inv.analyst_verdict = payload.verdict
    if payload.action == "review":
        inv.reviewed_at = datetime.now(timezone.utc)

    db.flush()
    after = get_investigation_state(inv)

    # Record audit
    desc = f"Status changed to '{inv.status}' by analyst '{payload.analyst_id}'"
    if payload.verdict:
        desc += f". Verdict: {payload.verdict}"
    if payload.comment:
        desc += f". Comment: {payload.comment[:200]}"

    record_action(db, investigation_id, payload.analyst_id, payload.action, desc, before, after)

    db.commit()
    # Re-fetch with selectinload to get updated collections
    updated = _get_or_404(db, investigation_id)
    return _inv_to_out(updated)


@router.post("/{investigation_id}/notes", response_model=AnalystNoteOut)
def add_note(
    investigation_id: str,
    payload: AnalystNoteCreate,
    db: Session = Depends(get_db),
):
    """Add an analyst note to an investigation."""
    inv = _get_or_404(db, investigation_id)

    note = AnalystNote(
        investigation_id=investigation_id,
        analyst_id=payload.analyst_id,
        content=payload.content,
        note_type=payload.note_type,
    )
    db.add(note)
    db.flush()

    record_action(
        db, investigation_id, payload.analyst_id, "note_added",
        f"Note added ({payload.note_type}): {payload.content[:100]}...",
        None, {"note_id": note.id, "type": payload.note_type},
    )
    db.commit()
    db.refresh(note)
    return note


@router.get("/{investigation_id}/audit", response_model=list[AuditLogOut])
def get_audit(investigation_id: str, db: Session = Depends(get_db)):
    """Return the full audit history for an investigation."""
    _get_or_404(db, investigation_id)
    return get_audit_history(db, investigation_id)


def _get_or_404(db: Session, investigation_id: str) -> Investigation:
    inv = (
        db.query(Investigation)
        .options(selectinload(Investigation.notes), selectinload(Investigation.audit_logs))
        .filter(Investigation.id == investigation_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


def _inv_to_out(inv: Investigation) -> InvestigationOut:
    """Serialize Investigation ORM object to Pydantic schema while session is open."""
    # Explicitly access collections to trigger loading
    notes_data = []
    try:
        for n in (inv.notes or []):
            notes_data.append(n)
    except TypeError:
        notes_data = []

    audit_data = []
    try:
        for a in (inv.audit_logs or []):
            audit_data.append(a)
    except TypeError:
        audit_data = []

    return InvestigationOut(
        id=inv.id,
        transaction_id=inv.transaction_id,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        status=inv.status,
        priority=inv.priority,
        assigned_to=inv.assigned_to,
        risk_score=inv.risk_score,
        risk_level=inv.risk_level,
        analyst_verdict=inv.analyst_verdict,
        analyst_id=inv.analyst_id,
        reviewed_at=inv.reviewed_at,
        notes=notes_data,
        audit_logs=audit_data,
    )
