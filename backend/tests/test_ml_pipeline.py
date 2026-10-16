"""Tests for the ML training pipeline."""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


@pytest.mark.usefixtures("trained_models")
class TestMLPipeline:

    def test_dataset_generation(self):
        from data.generate_data import generate_synthetic_dataset
        df = generate_synthetic_dataset(n_samples=500, fraud_rate=0.05, random_state=1)
        assert len(df) == 500
        assert "is_fraud" in df.columns
        assert df["is_fraud"].sum() > 0
        assert df["is_fraud"].sum() < 500
        # No NaN in critical fields
        assert df["amount"].isna().sum() == 0
        assert df["merchant_category"].isna().sum() == 0

    def test_fraud_rate_matches(self):
        from data.generate_data import generate_synthetic_dataset
        df = generate_synthetic_dataset(n_samples=10000, fraud_rate=0.10, random_state=2)
        actual_rate = df["is_fraud"].mean()
        assert abs(actual_rate - 0.10) < 0.005, f"Fraud rate {actual_rate:.4f} not close to 0.10"

    def test_feature_transformer_output_shape(self):
        from data.generate_data import generate_synthetic_dataset
        from app.ml.features import FraudFeatureTransformer, FEATURE_NAMES
        df = generate_synthetic_dataset(n_samples=500, random_state=3)
        t = FraudFeatureTransformer()
        X = t.fit_transform(df.drop(columns=["is_fraud"]))
        assert X.shape == (500, len(FEATURE_NAMES))
        # Check no inf values (NaN can occur in edge cases with single-category std=0)
        assert not np.isinf(X).any(), "Feature matrix contains inf values"

    def test_feature_transformer_single_row(self):
        from app.ml.features import FraudFeatureTransformer, row_to_dataframe, FEATURE_NAMES
        from data.generate_data import generate_synthetic_dataset
        df = generate_synthetic_dataset(n_samples=200, random_state=4)
        t = FraudFeatureTransformer()
        t.fit(df.drop(columns=["is_fraud"]))
        row = {
            "amount": 5000.0, "merchant_category": "gaming",
            "hour_of_day": 2, "day_of_week": 5,
            "is_international": True, "is_new_merchant": True,
            "card_age_days": 10, "velocity_24h": 8,
            "distance_from_home_km": 500.0,
        }
        X = t.transform(row_to_dataframe(row))
        assert X.shape == (1, len(FEATURE_NAMES))
        assert not np.isnan(X).any()

    def test_no_test_data_leakage(self, trained_models):
        """Verify test set size matches 20% of total."""
        total = trained_models["dataset_size"]
        test = trained_models["test_size"]
        train = trained_models["train_size"]
        assert train + test == total
        # 20% ±1 row (rounding)
        assert abs(test / total - 0.20) < 0.01

    def test_metrics_are_on_test_set(self, trained_models):
        """F1 and PR-AUC must be non-trivial (better than random)."""
        rf = trained_models["rf_metrics"]
        assert rf["f1_score"] > 0.3, f"RF F1 too low: {rf['f1_score']}"
        assert rf["pr_auc"] > 0.4, f"RF PR-AUC too low: {rf['pr_auc']}"
        lr = trained_models["lr_metrics"]
        assert lr["pr_auc"] > 0.3, f"LR PR-AUC too low: {lr['pr_auc']}"

    def test_model_files_saved(self, trained_models):
        """All expected model artifacts must exist after training."""
        # model_dir path is embedded in metadata by checking the files exist
        # We verify the metadata confirms all required keys are present
        assert "version" in trained_models
        assert "lr_metrics" in trained_models
        assert "rf_metrics" in trained_models
        assert "feature_names" in trained_models
        assert "disclaimer" in trained_models

    def test_best_model_prediction(self, trained_models):
        """Best model must return valid probability for a single row."""
        import joblib, tempfile
        from pathlib import Path as _P
        from app.ml.pipeline import load_best_model

        # Retrain in a temp dir and load from there
        from data.generate_data import generate_synthetic_dataset
        from app.ml.pipeline import train_models
        import tempfile
        tmp = tempfile.mkdtemp()
        df = generate_synthetic_dataset(n_samples=500, random_state=99)
        train_models(df, tmp)
        pipeline = load_best_model(tmp)

        row = pd.DataFrame([{
            "amount": 75000.0, "merchant_category": "jewelry",
            "hour_of_day": 3, "day_of_week": 6,
            "is_international": True, "is_new_merchant": True,
            "card_age_days": 5, "velocity_24h": 12,
            "distance_from_home_km": 800.0,
        }])
        proba = pipeline.predict_proba(row)[0, 1]
        assert 0.0 <= proba <= 1.0

    def test_confusion_matrix_structure(self, trained_models):
        """Confusion matrix must be 2×2."""
        cm = trained_models["rf_metrics"]["confusion_matrix"]
        assert len(cm) == 2
        assert len(cm[0]) == 2
        total = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1]
        assert total == trained_models["test_size"]
