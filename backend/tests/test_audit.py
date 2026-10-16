"""Tests for audit history service."""
import pytest
from datetime import datetime
from app.models.investigation import Investigation
from app.models.audit import AuditLog
from app.services.audit import record_action, get_audit_history, get_investigation_state


class TestAuditService:

    def test_record_action_creates_log(self, db_session):
        # Create a test investigation
        inv = Investigation(
            id="test-inv-001",
            transaction_id="txn-001",
            status="open",
            priority="high",
            risk_score=80.0,
            risk_level="high",
        )
        db_session.add(inv)
        db_session.commit()

        log = record_action(
            db_session,
            investigation_id="test-inv-001",
            actor_id="analyst_01",
            action="review",
            description="Transaction reviewed and cleared",
            before_state={"status": "open"},
            after_state={"status": "reviewed"},
        )

        assert log.id is not None
        assert log.actor_id == "analyst_01"
        assert log.action == "review"
        assert log.before_state == {"status": "open"}
        assert log.after_state == {"status": "reviewed"}

    def test_audit_history_ordered_by_time(self, db_session):
        inv = Investigation(
            id="test-inv-002",
            transaction_id="txn-002",
            status="open",
            priority="medium",
        )
        db_session.add(inv)
        db_session.commit()

        for i, action in enumerate(["review", "escalate", "close"]):
            record_action(db_session, "test-inv-002", f"analyst_{i}", action, f"Action: {action}")

        history = get_audit_history(db_session, "test-inv-002")
        assert len(history) == 3
        # Must be chronological
        for i in range(len(history) - 1):
            assert history[i].created_at <= history[i + 1].created_at

    def test_audit_logs_are_immutable(self, db_session):
        """Audit logs should not be modifiable through the service (no update methods)."""
        inv = Investigation(
            id="test-inv-003",
            transaction_id="txn-003",
            status="open",
            priority="low",
        )
        db_session.add(inv)
        db_session.commit()

        log = record_action(
            db_session, "test-inv-003", "analyst_01", "note_added", "Original description"
        )
        original_id = log.id

        # Fetch again — should be unchanged
        fetched = db_session.query(AuditLog).filter(AuditLog.id == original_id).first()
        assert fetched.description == "Original description"
        # record_action never modifies existing entries — verify count
        logs = get_audit_history(db_session, "test-inv-003")
        assert len(logs) == 1

    def test_empty_audit_history(self, db_session):
        inv = Investigation(
            id="test-inv-004",
            transaction_id="txn-004",
            status="open",
            priority="low",
        )
        db_session.add(inv)
        db_session.commit()

        history = get_audit_history(db_session, "test-inv-004")
        assert history == []

    def test_get_investigation_state_snapshot(self, db_session):
        inv = Investigation(
            id="test-inv-005",
            transaction_id="txn-005",
            status="open",
            priority="high",
            assigned_to="analyst_02",
        )
        state = get_investigation_state(inv)
        assert state["status"] == "open"
        assert state["priority"] == "high"
        assert state["assigned_to"] == "analyst_02"
        assert "analyst_verdict" in state

    def test_audit_before_after_state(self, db_session):
        inv = Investigation(
            id="test-inv-006",
            transaction_id="txn-006",
            status="open",
            priority="medium",
        )
        db_session.add(inv)
        db_session.commit()

        before = {"status": "open", "analyst_verdict": None}
        after = {"status": "reviewed", "analyst_verdict": "legitimate"}

        log = record_action(
            db_session, "test-inv-006", "analyst_01",
            "review", "Cleared as legitimate",
            before_state=before, after_state=after,
        )
        assert log.before_state["status"] == "open"
        assert log.after_state["analyst_verdict"] == "legitimate"
