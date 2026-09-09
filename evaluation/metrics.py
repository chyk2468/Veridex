"""
Evaluation metrics calculation.
Calculates Precision, Recall, F1, Accuracy, and the critical False Contradiction Rate.
"""

from typing import List, Dict, Any

class EvaluationMetrics:
    """Calculates comprehensive evaluation metrics across relationship predictions."""

    @staticmethod
    def calculate(ground_truth: List[str], predictions: List[str]) -> Dict[str, Any]:
        categories = ["CORROBORATED", "CONTRADICTED", "CONTEXTUAL_DIFFERENCE", "UNCERTAIN", "RELATED_BUT_DIFFERENT"]
        
        per_class = {}
        total = len(ground_truth)
        correct = 0

        # False contradiction tracking
        false_contradictions = 0
        total_non_contradictions_truth = 0

        for cat in categories:
            tp = sum(1 for gt, pr in zip(ground_truth, predictions) if gt == cat and pr == cat)
            fp = sum(1 for gt, pr in zip(ground_truth, predictions) if gt != cat and pr == cat)
            fn = sum(1 for gt, pr in zip(ground_truth, predictions) if gt == cat and pr != cat)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            per_class[cat] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": sum(1 for gt in ground_truth if gt == cat)
            }

        for gt, pr in zip(ground_truth, predictions):
            if gt == pr:
                correct += 1
            if gt != "CONTRADICTED":
                total_non_contradictions_truth += 1
                if pr == "CONTRADICTED":
                    false_contradictions += 1

        accuracy = correct / total if total > 0 else 0.0
        false_contradiction_rate = (
            false_contradictions / total_non_contradictions_truth if total_non_contradictions_truth > 0 else 0.0
        )

        macro_p = sum(per_class[c]["precision"] for c in categories) / len(categories)
        macro_r = sum(per_class[c]["recall"] for c in categories) / len(categories)
        macro_f1 = sum(per_class[c]["f1"] for c in categories) / len(categories)

        return {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(macro_p, 4),
            "macro_recall": round(macro_r, 4),
            "macro_f1": round(macro_f1, 4),
            "false_contradiction_rate": round(false_contradiction_rate, 4),
            "total_samples": total,
            "per_class": per_class
        }
