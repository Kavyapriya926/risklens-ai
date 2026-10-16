"""
End-to-end smoke test against the live API server.
Run with: python scripts/smoke_test.py
Requires server running on localhost:8000.
"""
import sys, json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"
PASS = FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        print(f"  ✓  {name}")
        PASS += 1
    else:
        print(f"  ✗  {name}: {detail}")
        FAIL += 1


def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}", timeout=10)
    return json.loads(r.read()), r.status


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


print("\n=== RiskLens AI Smoke Test ===\n")

# 1. Health
d, s = get("/health")
check("GET /health → 200", s == 200)
check("health.status == ok", d.get("status") == "ok")

# 2. Analyze low-risk transaction
LOW_TXN = {
    "amount": 500, "merchant_category": "grocery",
    "hour_of_day": 10, "day_of_week": 1,
    "is_international": False, "is_new_merchant": False,
    "velocity_24h": 1,
}
d, s = post("/api/transactions/analyze", LOW_TXN)
check("POST /api/transactions/analyze (low) → 200", s == 200)
check("risk_score in [0,100]", 0 <= d.get("risk_score", -1) <= 100)
check("risk_level present", d.get("risk_level") in ("low", "medium", "high"))
check("explanation.factors non-empty", len(d.get("explanation", {}).get("factors", [])) > 0)
check("evidence_summary non-empty", bool(d.get("explanation", {}).get("evidence_summary")))
low_score = d.get("risk_score", 0)

# 3. Analyze high-risk transaction
HIGH_TXN = {
    "amount": 95000, "merchant_category": "jewelry",
    "hour_of_day": 2, "day_of_week": 6,
    "is_international": True, "is_new_merchant": True,
    "card_age_days": 5, "velocity_24h": 15,
    "distance_from_home_km": 900,
    "transaction_id": "smoke-high-001",
}
d, s = post("/api/transactions/analyze", HIGH_TXN)
check("POST /api/transactions/analyze (high) → 200", s == 200)
high_score = d.get("risk_score", 0)
check("high-risk score > low-risk score", high_score > low_score,
      f"high={high_score} low={low_score}")
check("high-risk level is 'high'", d.get("risk_level") == "high")

# 4. Invalid input rejected
BAD = {"amount": -100, "merchant_category": "retail", "hour_of_day": 10, "day_of_week": 2, "velocity_24h": 1}
d, s = post("/api/transactions/analyze", BAD)
check("Negative amount → 422", s == 422)

# 5. Dashboard stats
d, s = get("/api/dashboard/stats")
check("GET /api/dashboard/stats → 200", s == 200)
check("total_transactions >= 2", d.get("total_transactions", 0) >= 2)

# 6. Dashboard charts
d, s = get("/api/dashboard/charts")
check("GET /api/dashboard/charts → 200", s == 200)
check("risk_distribution has 5 buckets", len(d.get("risk_distribution", [])) == 5)

# 7. List transactions
d, s = get("/api/transactions?limit=10")
check("GET /api/transactions → 200", s == 200)
check("transactions list non-empty", len(d) > 0)

# 8. List investigations
d, s = get("/api/investigations?limit=10")
check("GET /api/investigations → 200", s == 200)
check("investigations is a list", isinstance(d, list))

# 9. Investigation actions (on the high-risk one created above)
invs, _ = get("/api/investigations?status=open&limit=1")
if invs:
    inv_id = invs[0]["id"]

    # Add note
    d, s = post(f"/api/investigations/{inv_id}/notes", {
        "analyst_id": "smoke_analyst",
        "content": "Smoke test note — verified transaction pattern",
        "note_type": "general",
    })
    check("POST /investigations/{id}/notes → 200", s == 200)

    # Review
    d, s = post(f"/api/investigations/{inv_id}/review", {
        "analyst_id": "smoke_analyst",
        "action": "review",
        "verdict": "fraud",
        "comment": "Smoke test review",
    })
    check("POST /investigations/{id}/review → 200", s == 200)
    check("status updated to 'reviewed'", d.get("status") == "reviewed")

    # Audit history
    d, s = get(f"/api/investigations/{inv_id}/audit")
    check("GET /investigations/{id}/audit → 200", s == 200)
    check("audit log has entries", len(d) >= 1)

    # Invalid transition (reviewed → escalate is allowed; reviewed → review again is not)
    d, s = post(f"/api/investigations/{inv_id}/review", {
        "analyst_id": "smoke_analyst", "action": "review",
    })
    check("Invalid re-review → 400", s == 400)
else:
    print("  ⚠  Skipped investigation tests (no open investigations)")

# 10. Model evaluation
d, s = get("/api/model/evaluation")
check("GET /api/model/evaluation → 200", s == 200)
check("metrics.f1_score present", "f1_score" in d.get("metrics", {}))
check("confusion_matrix is 2×2", len(d.get("confusion_matrix", [])) == 2)
check("disclaimer present", bool(d.get("disclaimer")))

# 11. Model monitoring
d, s = get("/api/model/monitoring")
check("GET /api/model/monitoring → 200", s == 200)
check("model_version present", bool(d.get("model_version")))
check("drift_report present", "drift_report" in d)

# 12. Simulator thresholds
d, s = get("/api/simulator/thresholds")
check("GET /api/simulator/thresholds → 200", s == 200)

# Summary
print(f"\n{'='*40}")
print(f"  TOTAL: {PASS+FAIL}  PASSED: {PASS}  FAILED: {FAIL}")
print(f"{'='*40}\n")
sys.exit(0 if FAIL == 0 else 1)
