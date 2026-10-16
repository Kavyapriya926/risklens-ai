"""Dashboard and monitoring schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_transactions: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    pending_investigations: int
    fraud_rate_pct: float
    avg_risk_score: float
    transactions_today: int
    high_risk_today: int


class RiskDistributionBucket(BaseModel):
    range: str
    count: int
    percentage: float


class DailyTrend(BaseModel):
    date: str
    total: int
    high_risk: int
    reviewed: int


class DashboardCharts(BaseModel):
    risk_distribution: list[RiskDistributionBucket]
    daily_trends: list[DailyTrend]
    category_breakdown: list[dict]


class SimulatorInput(BaseModel):
    low_threshold: float = 40.0
    high_threshold: float = 70.0
    review_cost_per_case: float = 500.0  # INR
    fraud_loss_per_case: float = 15000.0  # INR


class SimulatorResult(BaseModel):
    threshold_config: SimulatorInput
    total_transactions: int
    detected_fraud: int
    missed_fraud: int
    false_positives: int
    true_negatives: int
    precision: float
    recall: float
    f1_score: float
    estimated_review_cost: float
    estimated_fraud_loss: float
    total_cost: float
    comparison_baseline: Optional[dict] = None


class ModelEvaluationReport(BaseModel):
    model_name: str
    model_version: str
    trained_at: str
    dataset_size: int
    train_size: int
    test_size: int
    fraud_rate_pct: float
    metrics: dict
    confusion_matrix: list[list[int]]
    threshold_used: float
    pr_curve_points: list[dict]
    feature_importances: list[dict]
    disclaimer: str


class DriftReport(BaseModel):
    model_version: str
    report_generated_at: str
    reference_period: str
    current_period: str
    feature_drift: list[dict]
    overall_drift_detected: bool
    drift_severity: str  # low/medium/high
    recommendation: str
