"""Integration tests for the FastAPI endpoints."""
import pytest
import io
import csv


VALID_TXN = {
    "amount": 5000.0,
    "merchant_category": "retail",
    "hour_of_day": 10,
    "day_of_week": 2,
    "is_international": False,
    "is_new_merchant": False,
    "card_age_days": 365,
    "velocity_24h": 2,
    "distance_from_home_km": 5.0,
}

HIGH_RISK_TXN = {
    "amount": 95000.0,
    "merchant_category": "jewelry",
    "hour_of_day": 2,
    "day_of_week": 6,
    "is_international": True,
    "is_new_merchant": True,
    "card_age_days": 5,
    "velocity_24h": 15,
    "distance_from_home_km": 900.0,
}


@pytest.mark.usefixtures("trained_models")
class TestHealthEndpoint:
    def test_health_check(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.usefixtures("trained_models")
class TestTransactionAnalysis:
    def test_analyze_valid_transaction(self, client):
        r = client.post("/api/transactions/analyze", json=VALID_TXN)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 100
        assert data["risk_level"] in ("low", "medium", "high")
        assert "explanation" in data
        assert "evidence_summary" in data["explanation"]
        assert "factors" in data["explanation"]

    def test_analyze_high_risk_transaction(self, client):
        r = client.post("/api/transactions/analyze", json=HIGH_RISK_TXN)
        assert r.status_code == 200
        data = r.json()
        # High-risk patterns should score above medium threshold
        assert data["risk_score"] > 30

    def test_missing_required_field(self, client):
        incomplete = {k: v for k, v in VALID_TXN.items() if k != "amount"}
        r = client.post("/api/transactions/analyze", json=incomplete)
        assert r.status_code == 422

    def test_negative_amount_rejected(self, client):
        bad = dict(VALID_TXN, amount=-100)
        r = client.post("/api/transactions/analyze", json=bad)
        assert r.status_code == 422

    def test_invalid_hour_rejected(self, client):
        bad = dict(VALID_TXN, hour_of_day=99)
        r = client.post("/api/transactions/analyze", json=bad)
        assert r.status_code == 422

    def test_explanation_has_factors(self, client):
        r = client.post("/api/transactions/analyze", json=VALID_TXN)
        assert r.status_code == 200
        factors = r.json()["explanation"]["factors"]
        assert len(factors) > 0
        for f in factors:
            assert "feature" in f
            assert "contribution" in f
            assert "direction" in f

    # ── Duplicate transaction_id regression tests ────────────────────────────

    def test_unique_id_generated_when_omitted(self, client):
        """Two requests with no transaction_id must produce two distinct IDs."""
        r1 = client.post("/api/transactions/analyze", json=VALID_TXN)
        r2 = client.post("/api/transactions/analyze", json=VALID_TXN)
        assert r1.status_code == 200, r1.text
        assert r2.status_code == 200, r2.text
        assert r1.json()["transaction_id"] != r2.json()["transaction_id"]

    def test_explicit_id_first_submission_succeeds(self, client):
        """A caller-supplied transaction_id is accepted on the first submission."""
        payload = dict(VALID_TXN, transaction_id="dup-regression-001")
        r = client.post("/api/transactions/analyze", json=payload)
        assert r.status_code == 200, r.text
        assert r.json()["transaction_id"] == "dup-regression-001"

    def test_duplicate_id_returns_409(self, client):
        """Re-submitting the same transaction_id must return 409, not 500."""
        payload = dict(VALID_TXN, transaction_id="dup-regression-002")
        r1 = client.post("/api/transactions/analyze", json=payload)
        assert r1.status_code == 200, r1.text

        r2 = client.post("/api/transactions/analyze", json=payload)
        assert r2.status_code == 409, (
            f"Expected 409 Conflict for duplicate ID, got {r2.status_code}: {r2.text}"
        )
        assert "already exists" in r2.json()["detail"].lower()

    def test_409_detail_mentions_the_id(self, client):
        """The 409 response body must name the conflicting transaction_id."""
        payload = dict(VALID_TXN, transaction_id="dup-regression-detail-check")
        client.post("/api/transactions/analyze", json=payload)
        r = client.post("/api/transactions/analyze", json=payload)
        assert r.status_code == 409
        assert "dup-regression-detail-check" in r.json()["detail"]

    def test_session_healthy_after_duplicate(self, client):
        """A new unique transaction must succeed immediately after a 409 conflict."""
        shared_id = "dup-regression-session-test"
        client.post("/api/transactions/analyze", json=dict(VALID_TXN, transaction_id=shared_id))
        # Trigger the conflict
        r_dup = client.post("/api/transactions/analyze", json=dict(VALID_TXN, transaction_id=shared_id))
        assert r_dup.status_code == 409

        # Session must be clean — a fresh transaction should work without error
        fresh_id = f"dup-regression-after-{__import__('uuid').uuid4().hex[:8]}"
        r_fresh = client.post("/api/transactions/analyze", json=dict(VALID_TXN, transaction_id=fresh_id))
        assert r_fresh.status_code == 200, (
            f"Session was left in a failed state after 409: {r_fresh.status_code} {r_fresh.text}"
        )
        assert r_fresh.json()["transaction_id"] == fresh_id


@pytest.mark.usefixtures("trained_models")
class TestCSVUpload:
    def _make_csv(self, rows: list[dict]) -> bytes:
        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return buf.getvalue().encode("utf-8")

    def test_valid_csv_upload(self, client):
        rows = [dict(VALID_TXN, transaction_id=f"txn-csv-{i:03d}", is_fraud_actual="false") for i in range(5)]
        content = self._make_csv(rows)
        r = client.post(
            "/api/transactions/upload-csv",
            files={"file": ("test.csv", content, "text/csv")},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["processed"] == 5
        assert data["failed"] == 0
        assert "batch_id" in data

    def test_non_csv_rejected(self, client):
        r = client.post(
            "/api/transactions/upload-csv",
            files={"file": ("malicious.exe", b"binary data", "application/octet-stream")},
        )
        assert r.status_code == 400

    def test_malformed_csv_handled_gracefully(self, client):
        content = b"not,valid,csv\n\x00\x01\x02"
        r = client.post(
            "/api/transactions/upload-csv",
            files={"file": ("bad.csv", content, "text/csv")},
        )
        # Should not crash the server — either 200 with errors or 400
        assert r.status_code in (200, 400)


@pytest.mark.usefixtures("trained_models")
class TestDashboard:
    def test_dashboard_stats(self, client):
        r = client.get("/api/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_transactions" in data
        assert "high_risk_count" in data
        assert "avg_risk_score" in data

    def test_dashboard_charts(self, client):
        r = client.get("/api/dashboard/charts")
        assert r.status_code == 200
        data = r.json()
        assert "risk_distribution" in data
        assert "daily_trends" in data


@pytest.mark.usefixtures("trained_models")
class TestInvestigations:
    def _create_investigation(self, client) -> str:
        """Create a high-risk transaction to generate an investigation."""
        r = client.post("/api/transactions/analyze", json={
            **HIGH_RISK_TXN,
            "transaction_id": f"inv-test-{__import__('uuid').uuid4().hex[:8]}",
        })
        assert r.status_code == 200
        # Fetch the investigation
        invs = client.get("/api/investigations?status=open&limit=1").json()
        if not invs:
            pytest.skip("No open investigations created")
        return invs[0]["id"]

    def test_list_investigations(self, client):
        r = client.get("/api/investigations")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_investigation_state_transitions(self, client):
        inv_id = self._create_investigation(client)
        r = client.post(f"/api/investigations/{inv_id}/review", json={
            "analyst_id": "analyst_01",
            "action": "review",
            "verdict": "legitimate",
            "comment": "Verified with customer",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "reviewed"

    def test_invalid_transition_rejected(self, client):
        inv_id = self._create_investigation(client)
        # First close it
        client.post(f"/api/investigations/{inv_id}/review", json={
            "analyst_id": "a1", "action": "close",
        })
        # Trying to escalate a closed investigation should fail
        r = client.post(f"/api/investigations/{inv_id}/review", json={
            "analyst_id": "a1", "action": "escalate",
        })
        assert r.status_code == 400

    def test_add_note(self, client):
        inv_id = self._create_investigation(client)
        r = client.post(f"/api/investigations/{inv_id}/notes", json={
            "analyst_id": "analyst_02",
            "content": "Customer confirmed transaction is legitimate.",
            "note_type": "clearance",
        })
        assert r.status_code == 200
        assert r.json()["note_type"] == "clearance"

    def test_audit_history_populated(self, client):
        inv_id = self._create_investigation(client)
        client.post(f"/api/investigations/{inv_id}/review", json={
            "analyst_id": "a1", "action": "review", "verdict": "fraud",
        })
        r = client.get(f"/api/investigations/{inv_id}/audit")
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_investigation_not_found(self, client):
        r = client.get("/api/investigations/non-existent-id-xyz")
        assert r.status_code == 404


@pytest.mark.usefixtures("trained_models")
class TestModelEndpoints:
    def test_model_evaluation(self, client):
        r = client.get("/api/model/evaluation")
        assert r.status_code == 200
        data = r.json()
        assert "metrics" in data
        assert "precision" in data["metrics"]
        assert "recall" in data["metrics"]
        assert "confusion_matrix" in data
        assert "disclaimer" in data

    def test_model_monitoring(self, client):
        r = client.get("/api/model/monitoring")
        assert r.status_code == 200
        data = r.json()
        assert "model_version" in data
        assert "drift_report" in data
