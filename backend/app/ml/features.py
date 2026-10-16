"""Feature engineering for the fraud detection pipeline."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

# Canonical feature order — must never change once a model is saved
FEATURE_NAMES = [
    "amount_log",           # log1p(amount) — tames extreme values
    "amount_zscore",        # z-score within merchant category
    "hour_sin",             # cyclic encoding of hour
    "hour_cos",
    "day_sin",              # cyclic encoding of day of week
    "day_cos",
    "is_international",
    "is_new_merchant",
    "velocity_24h_log",     # log1p(velocity)
    "card_age_days_log",    # log1p(card_age_days); 0 when unknown
    "distance_log",         # log1p(distance); 0 when unknown
    "is_night",             # 0h–6h flag
    "is_weekend",
    "is_high_risk_category",
]

HIGH_RISK_CATEGORIES = {"gaming", "financial_services", "online_marketplace", "jewelry"}

FEATURE_LABELS = {
    "amount_log": "Transaction amount",
    "amount_zscore": "Amount relative to category average",
    "hour_sin": "Time of day (hour)",
    "hour_cos": "Time of day (hour)",
    "day_sin": "Day of week",
    "day_cos": "Day of week",
    "is_international": "International transaction",
    "is_new_merchant": "New merchant",
    "velocity_24h_log": "Transaction frequency (last 24h)",
    "card_age_days_log": "Card age",
    "distance_log": "Distance from home",
    "is_night": "Night-time transaction (0–6 AM)",
    "is_weekend": "Weekend transaction",
    "is_high_risk_category": "High-risk merchant category",
}


class FraudFeatureTransformer(BaseEstimator, TransformerMixin):
    """Converts raw transaction dicts/DataFrames into the feature matrix."""

    def __init__(self):
        self._category_stats: dict = {}

    def fit(self, X: pd.DataFrame, y=None) -> "FraudFeatureTransformer":
        # Compute per-category amount statistics for z-score
        self._category_stats = (
            X.groupby("merchant_category")["amount"]
            .agg(["mean", "std"])
            .to_dict("index")
        )
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        df = X.copy()

        # Amount features
        df["amount_log"] = np.log1p(df["amount"])
        df["amount_zscore"] = df.apply(
            lambda r: self._zscore(r["amount"], r["merchant_category"]), axis=1
        )

        # Cyclic time encoding
        df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)
        df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
        df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

        # Binary flags
        df["is_international"] = df["is_international"].astype(float)
        df["is_new_merchant"] = df["is_new_merchant"].astype(float)

        # Velocity and age (with 0 as safe default for missing)
        df["velocity_24h_log"] = np.log1p(df["velocity_24h"].fillna(1))
        df["card_age_days_log"] = np.log1p(df["card_age_days"].fillna(0))
        df["distance_log"] = np.log1p(df["distance_from_home_km"].fillna(0))

        # Derived flags
        df["is_night"] = ((df["hour_of_day"] >= 0) & (df["hour_of_day"] < 6)).astype(float)
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(float)
        df["is_high_risk_category"] = df["merchant_category"].isin(HIGH_RISK_CATEGORIES).astype(float)

        return df[FEATURE_NAMES].values.astype(np.float32)

    def _zscore(self, amount: float, category: str) -> float:
        stats = self._category_stats.get(category, {})
        mean = stats.get("mean", amount)
        std = stats.get("std", 1.0) or 1.0
        if std == 0 or np.isnan(std):
            std = 1.0
        z = (amount - mean) / std
        # Clamp to avoid extreme values propagating as inf/nan in float32
        return float(np.clip(z, -10.0, 10.0))

    def get_feature_names_out(self):
        return FEATURE_NAMES


def row_to_dataframe(data: dict) -> pd.DataFrame:
    """Convert a single transaction dict to a single-row DataFrame."""
    return pd.DataFrame([data])
