"""Audit log service — records analyst actions immutably."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.investigation import Investigation


def record_action(
    db: Session,
    investigation_id: str,
    actor_id: str,
    action: str,
    description: str,
    before_state: dict | None = None,
    after_state: dict | None = None,
) -> AuditLog:
    """
    Create an immutable audit log entry.

    This function never updates or deletes existing entries.
    All analyst actions are permanently recorded.
    """
    log = AuditLog(
        investigation_id=investigation_id,
        actor_id=actor_id,
        action=action,
        description=description,
        before_state=before_state,
        after_state=after_state,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_history(db: Session, investigation_id: str) -> list[AuditLog]:
    """Return full audit history for an investigation, ordered by time."""
    return (
        db.query(AuditLog)
        .filter(AuditLog.investigation_id == investigation_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )


def get_investigation_state(inv: Investigation) -> dict:
    """Snapshot the current state of an investigation for audit logging."""
    return {
        "status": inv.status,
        "priority": inv.priority,
        "assigned_to": inv.assigned_to,
        "analyst_verdict": inv.analyst_verdict,
        "analyst_id": inv.analyst_id,
    }
