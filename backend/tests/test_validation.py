"""Tests for input validation in Pydantic schemas."""
import pytest
from pydantic import ValidationError
from app.schemas.transaction import TransactionInput
from app.schemas.investigation import AnalystNoteCreate, InvestigationReview


class TestTransactionInput:
    def _valid(self, **kwargs):
        defaults = dict(
            amount=1000.0,
            merchant_category="retail",
            hour_of_day=10,
            day_of_week=2,
        )
        defaults.update(kwargs)
        return TransactionInput(**defaults)

    def test_valid_transaction(self):
        t = self._valid()
        assert t.amount == 1000.0
        assert t.merchant_category == "retail"

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            self._valid(amount=-100)

    def test_zero_amount_rejected(self):
        with pytest.raises(ValidationError):
            self._valid(amount=0)

    def test_excessive_amount_rejected(self):
        with pytest.raises(ValidationError):
            self._valid(amount=20_000_000)

    def test_invalid_hour_rejected(self):
        with pytest.raises(ValidationError):
            self._valid(hour_of_day=25)
        with pytest.raises(ValidationError):
            self._valid(hour_of_day=-1)

    def test_invalid_day_rejected(self):
        with pytest.raises(ValidationError):
            self._valid(day_of_week=7)

    def test_unknown_category_becomes_other(self):
        t = self._valid(merchant_category="SUSPICIOUS_INJECTION; DROP TABLE")
        assert t.merchant_category == "other"

    def test_category_case_insensitive(self):
        t = self._valid(merchant_category="RETAIL")
        assert t.merchant_category == "retail"

    def test_transaction_id_sanitized(self):
        with pytest.raises(ValidationError):
            self._valid(transaction_id="'; DROP TABLE transactions; --")

    def test_velocity_at_boundaries(self):
        t1 = self._valid(velocity_24h=1)
        t2 = self._valid(velocity_24h=1000)
        assert t1.velocity_24h == 1
        assert t2.velocity_24h == 1000
        with pytest.raises(ValidationError):
            self._valid(velocity_24h=0)

    def test_optional_fields_none(self):
        t = self._valid()
        assert t.card_age_days is None
        assert t.distance_from_home_km is None

    def test_transaction_id_auto_assigned(self):
        t = self._valid()
        assert t.transaction_id is not None
        assert len(t.transaction_id) > 0

    def test_is_fraud_actual_optional(self):
        t = self._valid(is_fraud_actual=True)
        assert t.is_fraud_actual is True
        t2 = self._valid()
        assert t2.is_fraud_actual is None


class TestAnalystNoteCreate:
    def test_valid_note(self):
        n = AnalystNoteCreate(analyst_id="analyst_01", content="Reviewed and cleared.", note_type="clearance")
        assert n.content == "Reviewed and cleared."

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            AnalystNoteCreate(analyst_id="a1", content="")

    def test_invalid_note_type(self):
        with pytest.raises(ValidationError):
            AnalystNoteCreate(analyst_id="a1", content="test", note_type="invalid_type")

    def test_content_too_long(self):
        with pytest.raises(ValidationError):
            AnalystNoteCreate(analyst_id="a1", content="x" * 2001)


class TestInvestigationReview:
    def test_valid_review(self):
        r = InvestigationReview(analyst_id="a1", action="review", verdict="legitimate")
        assert r.action == "review"

    def test_invalid_action(self):
        with pytest.raises(ValidationError):
            InvestigationReview(analyst_id="a1", action="delete")

    def test_invalid_verdict(self):
        with pytest.raises(ValidationError):
            InvestigationReview(analyst_id="a1", action="review", verdict="maybe")
