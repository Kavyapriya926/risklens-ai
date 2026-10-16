"""Tests for the risk classification engine."""
import pytest
from app.services.risk_engine import classify_risk, priority_from_risk, simulate_thresholds


class TestClassifyRisk:
    def test_low_risk(self):
        assert classify_risk(0) == "low"
        assert classify_risk(39.9) == "low"

    def test_medium_risk(self):
        assert classify_risk(40.0) == "medium"
        assert classify_risk(69.9) == "medium"

    def test_high_risk(self):
        assert classify_risk(70.0) == "high"
        assert classify_risk(100.0) == "high"

    def test_boundary_clamping(self):
        assert classify_risk(-5) == "low"
        assert classify_risk(105) == "high"

    def test_custom_thresholds(self):
        assert classify_risk(50, low_threshold=30, high_threshold=80) == "medium"
        assert classify_risk(85, low_threshold=30, high_threshold=80) == "high"
        assert classify_risk(20, low_threshold=30, high_threshold=80) == "low"

    def test_invalid_thresholds(self):
        with pytest.raises(ValueError):
            classify_risk(50, low_threshold=80, high_threshold=40)

    def test_equal_thresholds_invalid(self):
        with pytest.raises(ValueError):
            classify_risk(50, low_threshold=50, high_threshold=50)


class TestPriorityFromRisk:
    def test_high_risk_large_amount(self):
        assert priority_from_risk("high", 75000) == "critical"

    def test_high_risk_small_amount(self):
        assert priority_from_risk("high", 5000) == "high"

    def test_medium_risk(self):
        assert priority_from_risk("medium", 5000) == "medium"

    def test_low_risk(self):
        assert priority_from_risk("low", 500) == "low"


class TestSimulateThresholds:
    def _make_data(self):
        # 100 transactions: 10 fraud
        scores = [90] * 8 + [50] * 2 + [20] * 90  # 8 high fraud, 2 medium fraud, 90 legit
        labels = [1] * 10 + [0] * 90
        return scores, labels

    def test_basic_simulation(self):
        scores, labels = self._make_data()
        result = simulate_thresholds(scores, labels, low_threshold=40, high_threshold=70)
        assert result["detected_fraud"] + result["missed_fraud"] == 10
        assert result["false_positives"] + result["true_negatives"] == 90
        assert 0 <= result["precision"] <= 1
        assert 0 <= result["recall"] <= 1

    def test_zero_threshold_catches_all(self):
        scores = [80] * 10 + [20] * 90
        labels = [1] * 10 + [0] * 90
        result = simulate_thresholds(scores, labels, low_threshold=0, high_threshold=1)
        # Every transaction flagged → all fraud caught but many FP
        assert result["detected_fraud"] == 10

    def test_high_threshold_misses_fraud(self):
        scores = [60] * 10 + [20] * 90
        labels = [1] * 10 + [0] * 90
        result = simulate_thresholds(scores, labels, low_threshold=40, high_threshold=90)
        # High threshold → all fraud missed
        assert result["missed_fraud"] == 10
        assert result["detected_fraud"] == 0

    def test_cost_calculation(self):
        scores, labels = self._make_data()
        result = simulate_thresholds(
            scores, labels, review_cost=500.0, fraud_loss=10000.0,
            low_threshold=40, high_threshold=70,
        )
        expected_review = result["false_positives"] + result["detected_fraud"]
        assert result["estimated_review_cost"] == round(expected_review * 500.0, 2)
        assert result["estimated_fraud_loss"] == round(result["missed_fraud"] * 10000.0, 2)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            simulate_thresholds([80, 60], [1], low_threshold=40, high_threshold=70)

    def test_invalid_thresholds_raises(self):
        with pytest.raises(ValueError):
            simulate_thresholds([50], [1], low_threshold=70, high_threshold=40)
