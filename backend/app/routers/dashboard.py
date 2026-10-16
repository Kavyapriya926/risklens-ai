"""Dashboard statistics and charts endpoints."""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.investigation import Investigation
from app.schemas.dashboard import DashboardStats, DashboardCharts

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Return key performance indicators for the dashboard."""
    total = db.query(func.count(Transaction.id)).scalar() or 0
    high = db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "high").scalar() or 0
    medium = db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "medium").scalar() or 0
    low = db.query(func.count(Transaction.id)).filter(Transaction.risk_level == "low").scalar() or 0
    pending_inv = db.query(func.count(Investigation.id)).filter(Investigation.status == "open").scalar() or 0
    avg_score = db.query(func.avg(Transaction.risk_score)).scalar() or 0.0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    txns_today = db.query(func.count(Transaction.id)).filter(Transaction.created_at >= today_start).scalar() or 0
    high_today = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.created_at >= today_start, Transaction.risk_level == "high")
        .scalar() or 0
    )

    # Fraud rate = confirmed fraud / total with ground truth
    confirmed = db.query(func.count(Transaction.id)).filter(Transaction.is_fraud_actual == True).scalar() or 0  # noqa: E712
    with_truth = db.query(func.count(Transaction.id)).filter(Transaction.is_fraud_actual != None).scalar() or 1  # noqa: E711
    fraud_rate = (confirmed / with_truth) * 100 if with_truth > 0 else 0.0

    return DashboardStats(
        total_transactions=total,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        pending_investigations=pending_inv,
        fraud_rate_pct=round(fraud_rate, 2),
        avg_risk_score=round(float(avg_score), 2),
        transactions_today=txns_today,
        high_risk_today=high_today,
    )


@router.get("/charts", response_model=DashboardCharts)
def get_dashboard_charts(db: Session = Depends(get_db)):
    """Return chart data for risk distribution, trends, and category breakdown."""
    # Risk distribution buckets
    all_scores = [r[0] for r in db.query(Transaction.risk_score).filter(Transaction.risk_score != None).all()]  # noqa: E711
    total = len(all_scores) or 1

    buckets = [
        ("0–20", 0, 20), ("20–40", 20, 40), ("40–60", 40, 60),
        ("60–80", 60, 80), ("80–100", 80, 101),
    ]
    risk_dist = []
    for label, lo, hi in buckets:
        count = sum(1 for s in all_scores if lo <= s < hi)
        risk_dist.append({"range": label, "count": count, "percentage": round(count / total * 100, 1)})

    # Daily trends — last 14 days
    daily_trends = []
    for delta in range(13, -1, -1):
        day = datetime.now(timezone.utc).date() - timedelta(days=delta)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        total_day = db.query(func.count(Transaction.id)).filter(
            Transaction.created_at >= day_start, Transaction.created_at < day_end
        ).scalar() or 0
        high_day = db.query(func.count(Transaction.id)).filter(
            Transaction.created_at >= day_start, Transaction.created_at < day_end,
            Transaction.risk_level == "high",
        ).scalar() or 0
        reviewed_day = db.query(func.count(Investigation.id)).filter(
            Investigation.updated_at >= day_start, Investigation.updated_at < day_end,
            Investigation.status.in_(["reviewed", "closed"]),
        ).scalar() or 0
        daily_trends.append({
            "date": day.strftime("%b %d"),
            "total": total_day,
            "high_risk": high_day,
            "reviewed": reviewed_day,
        })

    # Category breakdown
    cat_rows = (
        db.query(Transaction.merchant_category, func.count(Transaction.id), Transaction.risk_level)
        .group_by(Transaction.merchant_category, Transaction.risk_level)
        .all()
    )
    cat_map = defaultdict(lambda: {"category": "", "total": 0, "high_risk": 0})
    for cat, count, level in cat_rows:
        cat_map[cat]["category"] = cat
        cat_map[cat]["total"] += count
        if level == "high":
            cat_map[cat]["high_risk"] += count
    category_breakdown = sorted(cat_map.values(), key=lambda x: x["total"], reverse=True)[:10]

    return DashboardCharts(
        risk_distribution=risk_dist,
        daily_trends=daily_trends,
        category_breakdown=category_breakdown,
    )
