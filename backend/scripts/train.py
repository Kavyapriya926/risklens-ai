"""
Standalone training script.

Usage:
    python scripts/train.py
    python scripts/train.py --samples 50000 --fraud-rate 0.05
"""
from __future__ import annotations
import sys
import argparse
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train RiskLens AI fraud detection models")
    parser.add_argument("--samples", type=int, default=20000, help="Number of training samples")
    parser.add_argument("--fraud-rate", type=float, default=0.05, help="Fraud rate (0–1)")
    parser.add_argument("--model-dir", type=str, default="./models", help="Directory to save models")
    parser.add_argument("--data-path", type=str, default=None, help="Path to custom CSV dataset")
    args = parser.parse_args()

    from app.ml.pipeline import train_models, load_dataset

    csv_path = args.data_path or (Path("./data/fraud_dataset.csv") if Path("./data/fraud_dataset.csv").exists() else None)
    
    if csv_path and Path(str(csv_path)).exists():
        logger.info("Loading dataset from %s", csv_path)
        df = load_dataset(csv_path)
    else:
        logger.info("No dataset found — generating synthetic data (%d samples, %.1f%% fraud)", args.samples, args.fraud_rate * 100)
        # Save generated data for reference
        from data.generate_data import generate_synthetic_dataset
        df = generate_synthetic_dataset(n_samples=args.samples, fraud_rate=args.fraud_rate)
        out = Path("./data/fraud_dataset.csv")
        out.parent.mkdir(exist_ok=True)
        df.to_csv(out, index=False)
        logger.info("Saved synthetic dataset to %s", out)

    logger.info("Starting model training...")
    metadata = train_models(df, args.model_dir)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Model version : {metadata['version']}")
    print(f"Best model    : {metadata['best_model']}")
    print(f"Dataset size  : {metadata['dataset_size']} ({metadata['fraud_rate_pct']}% fraud)")
    print(f"Train / Test  : {metadata['train_size']} / {metadata['test_size']}")
    print()
    print("Logistic Regression (test set):")
    lr = metadata["lr_metrics"]
    print(f"  Precision={lr['precision']:.4f}  Recall={lr['recall']:.4f}  F1={lr['f1_score']:.4f}  PR-AUC={lr['pr_auc']:.4f}  FPR={lr['false_positive_rate']:.4f}")
    print()
    print("Random Forest (test set):")
    rf = metadata["rf_metrics"]
    print(f"  Precision={rf['precision']:.4f}  Recall={rf['recall']:.4f}  F1={rf['f1_score']:.4f}  PR-AUC={rf['pr_auc']:.4f}  FPR={rf['false_positive_rate']:.4f}")
    print()
    print(metadata["disclaimer"])
    print("=" * 60)


if __name__ == "__main__":
    main()
