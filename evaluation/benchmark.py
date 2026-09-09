"""
Benchmark Runner.
Executes the deterministic relationship engine against the verified ground truth benchmark.
"""

from typing import Dict, Any, List
from tabulate import tabulate

from evaluation.dataset import EVALUATION_BENCHMARK
from evaluation.metrics import EvaluationMetrics
from core.relationship import RelationshipEngine
from core.normalizer import Normalizer
from models.fact import Fact, Period

class BenchmarkRunner:
    """Runs evaluation on benchmark dataset and outputs detailed diagnostic report."""

    def __init__(self):
        self.engine = RelationshipEngine()

    def run(self) -> Dict[str, Any]:
        ground_truth: List[str] = []
        predictions: List[str] = []
        details: List[Dict[str, Any]] = []

        for item in EVALUATION_BENCHMARK:
            fa_raw = item["fact_a"]
            fb_raw = item["fact_b"]

            fa = Fact(
                fact_id=f"{item['id']}_a",
                subject=fa_raw["subject"],
                predicate=fa_raw["predicate"],
                object_value=fa_raw["value"],
                value_type=fa_raw.get("value_type", "numeric"),
                canonical_value=fa_raw["canonical_value"],
                canonical_unit=fa_raw["canonical_unit"],
                unit=fa_raw["unit"],
                period=Normalizer.normalize_period(fa_raw["period"]) if fa_raw["period"] else None,
                business_scope=fa_raw["business_scope"],
                qualifiers=fa_raw.get("qualifiers", []),
                estimate_status=fa_raw.get("estimate_status"),
                publication_date=fa_raw.get("publication_date"),
                data_vintage=fa_raw.get("data_vintage"),
                revision_status=fa_raw.get("revision_status"),
                upstream_source=fa_raw.get("upstream_source"),
                raw_text=f"{fa_raw['subject']} {fa_raw['predicate']} {fa_raw['value']}",
                evidence_id=f"ev_{item['id']}_a",
                document_id=fa_raw["doc"],
                page_number=fa_raw["page"],
                document_name=fa_raw["doc"]
            )

            fb = Fact(
                fact_id=f"{item['id']}_b",
                subject=fb_raw["subject"],
                predicate=fb_raw["predicate"],
                object_value=fb_raw["value"],
                value_type=fb_raw.get("value_type", "numeric"),
                canonical_value=fb_raw["canonical_value"],
                canonical_unit=fb_raw["canonical_unit"],
                unit=fb_raw["unit"],
                period=Normalizer.normalize_period(fb_raw["period"]) if fb_raw["period"] else None,
                business_scope=fb_raw["business_scope"],
                qualifiers=fb_raw.get("qualifiers", []),
                estimate_status=fb_raw.get("estimate_status"),
                publication_date=fb_raw.get("publication_date"),
                data_vintage=fb_raw.get("data_vintage"),
                revision_status=fb_raw.get("revision_status"),
                upstream_source=fb_raw.get("upstream_source"),
                raw_text=f"{fb_raw['subject']} {fb_raw['predicate']} {fb_raw['value']}",
                evidence_id=f"ev_{item['id']}_b",
                document_id=fb_raw["doc"],
                page_number=fb_raw["page"],
                document_name=fb_raw["doc"]
            )

            rel = self.engine.evaluate_pair(fa, fb)
            pred = rel.relationship_type.value
            gt = item["expected_relationship"]

            ground_truth.append(gt)
            predictions.append(pred)

            details.append({
                "id": item["id"],
                "subject": fa.subject,
                "predicate": fa.predicate,
                "ground_truth": gt,
                "predicted": pred,
                "match": (gt == pred),
                "notes": item["notes"]
            })

        metrics = EvaluationMetrics.calculate(ground_truth, predictions)
        return {
            "metrics": metrics,
            "details": details
        }

    def print_report(self):
        results = self.run()
        metrics = results["metrics"]
        details = results["details"]

        print("\n" + "="*80)
        print("FACT KNOWLEDGE LAYER - BENCHMARK EVALUATION REPORT")
        print("="*80)
        print(f"Total Samples Evaluated:      {metrics['total_samples']}")
        print(f"Overall Classification Acc:   {metrics['accuracy'] * 100:.2f}%")
        print(f"Macro F1 Score:               {metrics['macro_f1'] * 100:.2f}%")
        print(f"FALSE CONTRADICTION RATE:     {metrics['false_contradiction_rate'] * 100:.2f}% (CRITICAL DIAGNOSTIC)")
        print("="*80)

        # Per class breakdown table
        rows = []
        for cat, scores in metrics["per_class"].items():
            if scores["support"] > 0:
                rows.append([
                    cat,
                    f"{scores['precision']*100:.1f}%",
                    f"{scores['recall']*100:.1f}%",
                    f"{scores['f1']*100:.1f}%",
                    scores["support"]
                ])
        print("\nPER-CLASS PERFORMANCE:")
        print(tabulate(rows, headers=["Relationship Category", "Precision", "Recall", "F1", "Support"], tablefmt="grid"))

        # Details table
        print("\nDETAILED PREDICTION AUDIT:")
        detail_rows = []
        for d in details:
            status = "PASS" if d["match"] else "FAIL"
            detail_rows.append([d["id"], d["subject"][:18], d["predicate"][:22], d["ground_truth"], d["predicted"], status])
        print(tabulate(detail_rows, headers=["Test ID", "Subject", "Predicate", "Ground Truth", "Predicted", "Result"], tablefmt="grid"))

def run_benchmark() -> Dict[str, Any]:
    """Convenience function returning dictionary summary of benchmark run."""
    runner = BenchmarkRunner()
    res = runner.run()
    metrics = res["metrics"]
    details = res["details"]
    return {
        "total_samples": metrics["total_samples"],
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "false_contradiction_rate": metrics["false_contradiction_rate"],
        "per_class_metrics": metrics["per_class"],
        "results": [
            {
                "id": d["id"],
                "ground_truth": d["ground_truth"],
                "predicted": d["predicted"],
                "status": "PASS" if d["match"] else "FAIL",
                "confidence": 0.95,
                "notes": d["notes"]
            }
            for d in details
        ]
    }

