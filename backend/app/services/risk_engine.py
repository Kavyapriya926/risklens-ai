"""Risk classification engine with configurable thresholds."""
from __future__ import annotations


def classify_risk(score: float, low_threshold: float = 40.0, high_threshold: float = 70.0) -> str:
    """
    Classify a risk score into low / medium / high.

    Args:
        score: Risk score in [0, 100].
        low_threshold: Score below this is 'low' risk.
        high_threshold: Score at or above this is 'high' risk.

    Returns:
        One of 'low', 'medium', 'high'.
    """
    if not (0 <= low_threshold < high_threshold <= 100):
        raise ValueError(
            f"Invalid thresholds: low={low_threshold}, high={high_threshold}. "
            "Must satisfy 0 <= low < high <= 100."
        )
    score = max(0.0, min(100.0, score))
    if score >= high_threshold:
        return "high"
    if score >= low_threshold:
        return "medium"
    return "low"


def priority_from_risk(risk_level: str, amount: float) -> str:
    """Determine investigation priority from risk level and amount."""
    if risk_level == "high":
        return "critical" if amount >= 50000 else "high"
    if risk_level == "medium":
        return "medium"
    return "low"


def simulate_thresholds(
    risk_scores: list[float],
    actual_labels: list[int],
    low_threshold: float = 40.0,
    high_threshold: float = 70.0,
    review_cost: float = 500.0,
    fraud_loss: float = 15000.0,
) -> dict:
    """
    Simulate fraud detection outcomes at given thresholds.

    Treats score >= high_threshold as a 'flagged for review' prediction.
    Returns confusion matrix components and estimated costs.
    """
    if len(risk_scores) != len(actual_labels):
        raise ValueError("risk_scores and actual_labels must have the same length")
    if not (0 <= low_threshold < high_threshold <= 100):
        raise ValueError("Invalid thresholds")

    tp = fp = tn = fn = 0
    for score, label in zip(risk_scores, actual_labels):
        predicted_fraud = score >= high_threshold
        if predicted_fraud and label == 1:
            tp += 1
        elif predicted_fraud and label == 0:
            fp += 1
        elif not predicted_fraud and label == 1:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    review_cases = tp + fp
    estimated_review_cost = review_cases * review_cost
    estimated_fraud_loss = fn * fraud_loss
    total_cost = estimated_review_cost + estimated_fraud_loss

    return {
        "detected_fraud": tp,
        "missed_fraud": fn,
        "false_positives": fp,
        "true_negatives": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "estimated_review_cost": round(estimated_review_cost, 2),
        "estimated_fraud_loss": round(estimated_fraud_loss, 2),
        "total_cost": round(total_cost, 2),
    }
