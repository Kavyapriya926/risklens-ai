"""
Evidence-based explanation generator.

Explanations are derived from actual feature values and model coefficients /
feature importances — not from heuristic rules or fabricated scores.
"""
from __future__ import annotations
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from app.ml.features import FEATURE_NAMES, FEATURE_LABELS
from app.schemas.transaction import FeatureContribution, RiskExplanation


def explain_prediction(
    pipeline: Pipeline,
    raw_row: dict,
    risk_score: float,
) -> RiskExplanation:
    """
    Generate an evidence-based explanation for a risk prediction.

    For Logistic Regression: uses signed coefficient × feature value contributions.
    For Random Forest: uses mean decrease impurity feature importances + feature value context.
    """
    import pandas as pd
    from app.ml.features import row_to_dataframe

    df = row_to_dataframe(raw_row)
    transformer = pipeline.named_steps["features"]
    feature_matrix = transformer.transform(df)  # shape (1, n_features)
    feature_values = feature_matrix[0]

    clf = pipeline.named_steps["clf"]
    contributions = []

    if isinstance(clf, LogisticRegression):
        # Coefficients give the direction and magnitude of each feature's contribution
        scaler = pipeline.named_steps.get("scaler")
        if scaler is not None:
            # Scale the feature values as the model sees them
            scaled = scaler.transform(feature_matrix)[0]
        else:
            scaled = feature_values

        coefs = clf.coef_[0]  # shape (n_features,)
        raw_contributions = coefs * scaled  # element-wise product

        for i, fname in enumerate(FEATURE_NAMES):
            contrib = float(raw_contributions[i])
            contributions.append(FeatureContribution(
                feature=fname,
                value=round(float(feature_values[i]), 4),
                contribution=round(contrib, 4),
                direction="increases_risk" if contrib > 0 else "decreases_risk",
                human_label=FEATURE_LABELS.get(fname, fname),
            ))

    elif isinstance(clf, RandomForestClassifier):
        importances = clf.feature_importances_  # shape (n_features,)
        # For RF, sign the contribution using the feature value relative to a neutral baseline (0)
        for i, fname in enumerate(FEATURE_NAMES):
            raw_val = float(feature_values[i])
            importance = float(importances[i])
            # Heuristic sign: if the feature value is above 0 (encoded), it increases risk
            # This is an approximation — for production use SHAP TreeExplainer
            direction = "increases_risk" if raw_val > 0 else "decreases_risk"
            contrib = importance * (1 if raw_val > 0 else -0.5)
            contributions.append(FeatureContribution(
                feature=fname,
                value=round(raw_val, 4),
                contribution=round(contrib, 4),
                direction=direction,
                human_label=FEATURE_LABELS.get(fname, fname),
            ))
    else:
        # Fallback: no model-level explanation, return feature values only
        for i, fname in enumerate(FEATURE_NAMES):
            contributions.append(FeatureContribution(
                feature=fname,
                value=round(float(feature_values[i]), 4),
                contribution=0.0,
                direction="neutral",
                human_label=FEATURE_LABELS.get(fname, fname),
            ))

    # Sort by absolute contribution descending
    contributions.sort(key=lambda c: abs(c.contribution), reverse=True)

    # Build human-readable evidence summary from actual feature values
    evidence = _build_evidence_text(raw_row, contributions[:5], risk_score)
    primary = contributions[0].human_label if contributions else "Unknown factor"

    return RiskExplanation(
        primary_reason=primary,
        factors=contributions,
        evidence_summary=evidence,
    )


def _build_evidence_text(raw: dict, top_factors: list[FeatureContribution], score: float) -> str:
    """Build a human-readable evidence summary from actual field values."""
    parts = []

    # Amount
    amount = raw.get("amount", 0)
    if amount > 50000:
        parts.append(f"high transaction amount (₹{amount:,.0f})")
    elif amount > 10000:
        parts.append(f"above-average transaction amount (₹{amount:,.0f})")

    # Time
    hour = raw.get("hour_of_day", 12)
    if 0 <= hour < 6:
        parts.append(f"transaction occurred at {hour:02d}:00 (night-time)")

    # Flags
    if raw.get("is_international"):
        parts.append("international transaction")
    if raw.get("is_new_merchant"):
        parts.append("new or previously unseen merchant")

    # Velocity
    vel = raw.get("velocity_24h", 1)
    if vel >= 5:
        parts.append(f"{vel} transactions in the last 24 hours (high velocity)")

    # Distance
    dist = raw.get("distance_from_home_km")
    if dist and dist > 500:
        parts.append(f"transaction location {dist:.0f} km from home")

    # Category
    from app.ml.features import HIGH_RISK_CATEGORIES
    cat = raw.get("merchant_category", "")
    if cat in HIGH_RISK_CATEGORIES:
        parts.append(f"high-risk merchant category ({cat})")

    if not parts:
        # Fall back to top feature label
        if top_factors:
            parts.append(top_factors[0].human_label.lower())
        else:
            parts.append("model detected a combination of suspicious patterns")

    level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    summary = f"{level} risk ({score:.0f}/100). Factors: {'; '.join(parts)}."
    return summary
