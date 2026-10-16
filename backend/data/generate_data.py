"""
Synthetic fraud dataset generator.

Generates a labeled dataset mimicking payment transaction patterns
documented in public fraud benchmarks (IEEE-CIS, PaySim).

This is SYNTHETIC DEMO DATA — clearly labeled as such.
It must not be used for real fraud detection decisions.
"""
from __future__ import annotations
import uuid
import numpy as np
import pandas as pd
from pathlib import Path


CATEGORIES = [
    "retail", "food_beverage", "travel", "electronics", "utilities",
    "entertainment", "healthcare", "education", "financial_services",
    "online_marketplace", "fuel", "grocery", "jewelry", "gaming", "other",
]

# Approximate average amounts per category (INR)
CATEGORY_AMOUNTS = {
    "retail": (2000, 5000),
    "food_beverage": (300, 800),
    "travel": (8000, 25000),
    "electronics": (5000, 30000),
    "utilities": (500, 3000),
    "entertainment": (400, 1500),
    "healthcare": (1000, 8000),
    "education": (2000, 20000),
    "financial_services": (5000, 50000),
    "online_marketplace": (500, 10000),
    "fuel": (400, 2000),
    "grocery": (300, 1500),
    "jewelry": (10000, 100000),
    "gaming": (200, 5000),
    "other": (500, 5000),
}


def generate_synthetic_dataset(
    n_samples: int = 20000,
    fraud_rate: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic transaction dataset with realistic fraud patterns.

    Fraud is modeled as a combination of:
    - High amounts (anomalous for category)
    - Night-time transactions (0–5 AM)
    - International transactions
    - New merchants
    - High transaction velocity
    - High-risk categories
    - Cards with low age
    - Large distance from home

    Data source: SYNTHETIC — generated programmatically for demonstration.
    """
    rng = np.random.default_rng(random_state)
    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    rows = []

    # Legitimate transactions
    for _ in range(n_legit):
        cat = rng.choice(CATEGORIES, p=_category_probs())
        lo, hi = CATEGORY_AMOUNTS[cat]
        amount = float(rng.lognormal(np.log((lo + hi) / 2), 0.4))
        amount = max(10.0, min(amount, hi * 2))
        hour = int(rng.choice(range(24), p=_hour_probs_legit()))
        rows.append({
            "transaction_id": str(uuid.uuid4())[:12],
            "amount": round(amount, 2),
            "merchant_category": cat,
            "hour_of_day": hour,
            "day_of_week": int(rng.integers(0, 7)),
            "is_international": bool(rng.random() < 0.08),
            "is_new_merchant": bool(rng.random() < 0.10),
            "card_age_days": int(rng.integers(30, 3650)),
            "velocity_24h": int(rng.integers(1, 4)),
            "distance_from_home_km": float(round(rng.exponential(20), 1)),
            "is_fraud": 0,
        })

    # Fraudulent transactions — inject suspicious patterns
    fraud_cats = ["jewelry", "gaming", "financial_services", "online_marketplace", "electronics", "travel"]
    for _ in range(n_fraud):
        cat = rng.choice(fraud_cats)
        lo, hi = CATEGORY_AMOUNTS[cat]
        # Fraud tends toward higher amounts
        amount = float(rng.lognormal(np.log(hi * 0.7), 0.6))
        amount = max(50.0, min(amount, hi * 5))
        # Fraud tends toward night hours
        hour = int(rng.choice([0, 1, 2, 3, 4, 23], p=[0.2, 0.2, 0.2, 0.15, 0.15, 0.1]))
        rows.append({
            "transaction_id": str(uuid.uuid4())[:12],
            "amount": round(amount, 2),
            "merchant_category": cat,
            "hour_of_day": hour,
            "day_of_week": int(rng.integers(0, 7)),
            "is_international": bool(rng.random() < 0.55),   # higher rate
            "is_new_merchant": bool(rng.random() < 0.65),    # higher rate
            "card_age_days": int(rng.integers(1, 90)),        # newer cards
            "velocity_24h": int(rng.integers(5, 20)),         # high velocity
            "distance_from_home_km": float(round(rng.exponential(400), 1)),  # far from home
            "is_fraud": 1,
        })

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    print(f"[generate_data] Generated {len(df)} transactions: {n_legit} legitimate, {n_fraud} fraud ({fraud_rate*100:.1f}%)")
    print("[generate_data] DATA SOURCE: SYNTHETIC DEMO — not for real financial decisions")
    return df


def _category_probs() -> np.ndarray:
    probs = np.array([8, 10, 5, 4, 6, 5, 4, 3, 3, 8, 6, 12, 1, 3, 4], dtype=float)
    return probs / probs.sum()


def _hour_probs_legit() -> np.ndarray:
    """Higher probability during business hours for legitimate transactions."""
    probs = np.array([
        0.5, 0.3, 0.2, 0.2, 0.3, 0.5,   # 0–5: night (rare)
        1.0, 2.0, 3.5, 4.0, 4.5, 5.0,   # 6–11: morning ramp
        5.5, 5.5, 5.0, 4.5, 4.0, 3.5,   # 12–17: afternoon peak
        3.0, 2.5, 2.0, 1.5, 1.0, 0.7,   # 18–23: evening
    ], dtype=float)
    return probs / probs.sum()


if __name__ == "__main__":
    out_path = Path(__file__).parent / "fraud_dataset.csv"
    df = generate_synthetic_dataset(n_samples=20000, fraud_rate=0.05)
    df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    print(df.head())
    print(df["is_fraud"].value_counts())
