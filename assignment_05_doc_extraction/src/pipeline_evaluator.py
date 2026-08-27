"""Pipeline Evaluator for Document Extraction (Assignment 5).

Runs extraction on ground truth documents, measures field-level accuracy,
performs confidence calibration analysis, evaluates Human-in-the-Loop (HITL) routing,
and computes operational processing costs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.cost_model import CostAnalysisResult, CostModel
from src.extractor import DocumentExtractor, ExtractionResult
from src.schema_validator import SchemaValidator


class PipelineEvaluator:
    """End-to-end evaluation harness for document extraction, calibration, and routing."""

    def __init__(
        self,
        ground_truth_file: Optional[Path | str] = None,
        results_dir: Optional[Path | str] = None,
        routing_threshold: float = 0.85,
    ):
        self.gt_path = Path(ground_truth_file or (PROJECT_ROOT / "data" / "ground_truth.json")).resolve()
        self.results_dir = Path(results_dir or (PROJECT_ROOT / "results")).resolve()
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.routing_threshold = routing_threshold

        self.extractor = DocumentExtractor()
        self.validator = SchemaValidator()

    @staticmethod
    def _is_exact_match(val1: Any, val2: Any) -> bool:
        if isinstance(val1, float) and isinstance(val2, float):
            return round(val1, 2) == round(val2, 2)
        return val1 == val2

    @staticmethod
    def _is_normalized_match(val1: Any, val2: Any) -> bool:
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False

        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return round(float(val1), 2) == round(float(val2), 2)

        s1 = str(val1).strip().lower()
        s2 = str(val2).strip().lower()
        return s1 == s2

    def run_evaluations(self) -> Dict[str, Any]:
        """Execute full evaluation across all ground truth documents."""
        if not self.gt_path.exists():
            raise FileNotFoundError(f"Ground truth dataset not found at: {self.gt_path}")

        with open(self.gt_path, "r", encoding="utf-8") as f:
            dataset: List[Dict[str, Any]] = json.load(f)

        evaluation_records: List[Dict[str, Any]] = []
        field_stats: Dict[str, Dict[str, Dict[str, int]]] = {}
        # field_stats structure: doc_type -> field_name -> {"total": int, "exact": int, "norm": int}

        calibration_bins: Dict[str, Dict[str, Any]] = {
            "0.90-1.00": {"count": 0, "conf_sum": 0.0, "total_fields": 0, "exact_corr": 0, "norm_corr": 0},
            "0.80-0.89": {"count": 0, "conf_sum": 0.0, "total_fields": 0, "exact_corr": 0, "norm_corr": 0},
            "0.70-0.79": {"count": 0, "conf_sum": 0.0, "total_fields": 0, "exact_corr": 0, "norm_corr": 0},
            "< 0.70":    {"count": 0, "conf_sum": 0.0, "total_fields": 0, "exact_corr": 0, "norm_corr": 0},
        }

        stp_count = 0
        human_review_count = 0
        rejected_count = 0

        stp_fields_total = 0
        stp_fields_exact = 0
        human_review_fields_total = 0

        for item in dataset:
            doc_id = item["doc_id"]
            doc_type = item["doc_type"]
            tier = item["quality_tier"]
            raw_text = item["raw_text_content"]
            expected = item.get("expected_fields")
            should_reject = item.get("should_reject", False)

            # 1. Execute Extraction
            res: ExtractionResult = self.extractor.extract(doc_id, doc_type, raw_text)
            extracted = res.extracted_fields
            conf = res.confidence_score

            # 2. Schema Validation on Extracted Fields
            is_valid_schema = False
            schema_errors = []
            if res.status == "SUCCESS":
                is_valid_schema, schema_errors = self.validator.validate(doc_type, extracted)

            # 3. Routing Decision (HITL)
            if res.status == "REJECTED":
                route = "REJECTION_QUEUE"
                rejected_count += 1
            elif conf >= self.routing_threshold and is_valid_schema:
                route = "STRAIGHT_THROUGH_PROCESSING"
                stp_count += 1
            else:
                route = "HUMAN_REVIEW_QUEUE"
                human_review_count += 1

            # 4. Field Accuracy Comparison (if ground truth expects fields)
            field_comparisons: Dict[str, Dict[str, Any]] = {}
            doc_exact_matches = 0
            doc_norm_matches = 0
            doc_total_fields = 0

            if expected and isinstance(expected, dict):
                field_stats.setdefault(doc_type, {})
                for field_name, exp_val in expected.items():
                    act_val = extracted.get(field_name)
                    is_exact = self._is_exact_match(act_val, exp_val)
                    is_norm = self._is_normalized_match(act_val, exp_val)

                    field_comparisons[field_name] = {
                        "expected": exp_val,
                        "extracted": act_val,
                        "confidence": res.field_confidences.get(field_name, 0.0),
                        "exact_match": is_exact,
                        "normalized_match": is_norm,
                    }

                    # Accumulate stats
                    f_entry = field_stats[doc_type].setdefault(
                        field_name, {"total": 0, "exact": 0, "norm": 0}
                    )
                    f_entry["total"] += 1
                    if is_exact:
                        f_entry["exact"] += 1
                        doc_exact_matches += 1
                    if is_norm:
                        f_entry["norm"] += 1
                        doc_norm_matches += 1
                    doc_total_fields += 1

                # Routing Post-Review Tracking
                if route == "STRAIGHT_THROUGH_PROCESSING":
                    stp_fields_total += doc_total_fields
                    stp_fields_exact += doc_exact_matches
                elif route == "HUMAN_REVIEW_QUEUE":
                    human_review_fields_total += doc_total_fields

                # Calibration Bin Assignment
                if res.status == "SUCCESS":
                    if conf >= 0.90:
                        b_key = "0.90-1.00"
                    elif conf >= 0.80:
                        b_key = "0.80-0.89"
                    elif conf >= 0.70:
                        b_key = "0.70-0.79"
                    else:
                        b_key = "< 0.70"

                    bin_data = calibration_bins[b_key]
                    bin_data["count"] += 1
                    bin_data["conf_sum"] += conf
                    bin_data["total_fields"] += doc_total_fields
                    bin_data["exact_corr"] += doc_exact_matches
                    bin_data["norm_corr"] += doc_norm_matches

            evaluation_records.append({
                "doc_id": doc_id,
                "doc_type": doc_type,
                "quality_tier": tier,
                "status": res.status,
                "rejection_reason": res.rejection_reason,
                "confidence_score": conf,
                "schema_valid": is_valid_schema,
                "schema_errors": schema_errors,
                "routing_decision": route,
                "extracted_fields": extracted,
                "field_comparisons": field_comparisons,
            })

        # 5. Field Accuracy Summary Rows
        accuracy_rows: List[Dict[str, Any]] = []
        for d_type, fields in field_stats.items():
            for f_name, counts in fields.items():
                tot = counts["total"]
                exact_pct = round((counts["exact"] / tot) * 100.0, 1) if tot else 0.0
                norm_pct = round((counts["norm"] / tot) * 100.0, 1) if tot else 0.0
                accuracy_rows.append({
                    "document_type": d_type,
                    "field_name": f_name,
                    "evaluated_count": tot,
                    "exact_matches": counts["exact"],
                    "exact_match_pct": f"{exact_pct}%",
                    "normalized_matches": counts["norm"],
                    "normalized_match_pct": f"{norm_pct}%",
                })

        # 6. Confidence Calibration Summary Rows
        calibration_rows: List[Dict[str, Any]] = []
        for b_name, b_data in calibration_bins.items():
            cnt = b_data["count"]
            tot_f = b_data["total_fields"]
            avg_c = round(b_data["conf_sum"] / cnt, 3) if cnt else 0.0
            e_acc = round((b_data["exact_corr"] / tot_f) * 100.0, 1) if tot_f else 0.0
            n_acc = round((b_data["norm_corr"] / tot_f) * 100.0, 1) if tot_f else 0.0
            calibration_rows.append({
                "confidence_bin": b_name,
                "document_count": cnt,
                "avg_confidence": avg_c,
                "total_fields": tot_f,
                "exact_accuracy_pct": f"{e_acc}%",
                "normalized_accuracy_pct": f"{n_acc}%",
            })

        # 7. Operational Economics via CostModel
        cost_results: CostAnalysisResult = CostModel.evaluate(
            total_docs=len(dataset),
            stp_count=stp_count,
            human_review_count=human_review_count,
            rejected_count=rejected_count,
        )

        # 8. Post-Review Field Accuracy
        total_admitted_fields = stp_fields_total + human_review_fields_total
        post_review_correct = stp_fields_exact + human_review_fields_total
        post_review_acc_pct = (
            round((post_review_correct / total_admitted_fields) * 100.0, 1)
            if total_admitted_fields else 100.0
        )

        routing_summary = {
            "threshold": self.routing_threshold,
            "total_documents": len(dataset),
            "straight_through_processing": {
                "count": stp_count,
                "rate_pct": cost_results.stp_rate_pct,
            },
            "human_review_queue": {
                "count": human_review_count,
                "rate_pct": cost_results.human_review_rate_pct,
            },
            "rejection_queue": {
                "count": rejected_count,
                "rate_pct": cost_results.rejection_rate_pct,
            },
            "post_review_field_accuracy_pct": post_review_acc_pct,
            "economics": cost_results.to_dict(),
        }

        return {
            "records": evaluation_records,
            "field_accuracy": accuracy_rows,
            "calibration": calibration_rows,
            "routing_and_cost": routing_summary,
        }

    def save_artifacts(self, eval_results: Dict[str, Any]) -> Dict[str, Path]:
        """Export all 4 results artifacts to results/ directory."""
        # 1. extraction_results.json
        p_extractions = self.results_dir / "extraction_results.json"
        with open(p_extractions, "w", encoding="utf-8") as f:
            json.dump(eval_results["records"], f, indent=2)

        # 2. field_level_accuracy.csv
        p_acc = self.results_dir / "field_level_accuracy.csv"
        acc_rows = eval_results["field_accuracy"]
        if acc_rows:
            with open(p_acc, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(acc_rows[0].keys()))
                writer.writeheader()
                writer.writerows(acc_rows)

        # 3. confidence_calibration.csv
        p_calib = self.results_dir / "confidence_calibration.csv"
        calib_rows = eval_results["calibration"]
        if calib_rows:
            with open(p_calib, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(calib_rows[0].keys()))
                writer.writeheader()
                writer.writerows(calib_rows)

        # 4. routing_and_cost_summary.json
        p_summary = self.results_dir / "routing_and_cost_summary.json"
        with open(p_summary, "w", encoding="utf-8") as f:
            json.dump(eval_results["routing_and_cost"], f, indent=2)

        return {
            "extraction_results": p_extractions,
            "field_level_accuracy": p_acc,
            "confidence_calibration": p_calib,
            "routing_and_cost": p_summary,
        }

    def display_results(self, eval_results: Dict[str, Any], file_paths: Dict[str, Path]) -> None:
        """Render terminal summary tables."""
        summary = eval_results["routing_and_cost"]
        econ = summary["economics"]

        if RICH_AVAILABLE:
            console = Console()
            console.print("\n[bold cyan]================================================================================[/bold cyan]")
            console.print("[bold cyan]Assignment 5: Document Extraction Pipeline Evaluation[/bold cyan]")
            console.print("[bold cyan]================================================================================[/bold cyan]\n")

            # 1. Routing & Economics Panel
            panel_text = (
                f"[bold white]Total Documents Processed:[/bold white] {summary['total_documents']}\n"
                f"[bold green]• Straight-Through Processing (STP):[/bold green] {summary['straight_through_processing']['count']} docs "
                f"({summary['straight_through_processing']['rate_pct']}%)\n"
                f"[bold yellow]• Human Review Queue:[/bold yellow] {summary['human_review_queue']['count']} docs "
                f"({summary['human_review_queue']['rate_pct']}%)\n"
                f"[bold red]• Rejection Queue (Corrupted):[/bold red] {summary['rejection_queue']['count']} docs "
                f"({summary['rejection_queue']['rate_pct']}%)\n"
                f"[bold magenta]• Post-Review Field Accuracy:[/bold magenta] {summary['post_review_field_accuracy_pct']}%\n\n"
                f"[bold cyan]Cost & ROI Breakdown:[/bold cyan]\n"
                f"  - Baseline Manual Cost (100% human @ $1.80/doc): ${econ['baseline_manual_cost']:.2f}\n"
                f"  - Total Pipeline Cost (AI + Human Review):       ${econ['total_pipeline_cost']:.2f}\n"
                f"  - Effective Cost Per Document:                   ${econ['cost_per_document']:.3f}\n"
                f"  - [bold green]Net Labor Savings:[/bold green]                             [bold green]${econ['net_savings_dollars']:.2f} ({econ['net_savings_pct']}%) [/bold green]"
            )
            console.print(Panel(panel_text, title="Operational Routing & Cost Summary", border_style="green"))
            console.print()

            # 2. Calibration Table
            cal_table = Table(title="Confidence Calibration Bins", header_style="bold magenta")
            cal_table.add_column("Confidence Bin", style="cyan")
            cal_table.add_column("Documents", justify="center")
            cal_table.add_column("Avg Confidence", justify="right")
            cal_table.add_column("Total Fields", justify="right")
            cal_table.add_column("Exact Accuracy", style="green", justify="right")
            cal_table.add_column("Normalized Accuracy", style="bold green", justify="right")

            for r in eval_results["calibration"]:
                cal_table.add_row(
                    r["confidence_bin"],
                    str(r["document_count"]),
                    f"{r['avg_confidence']:.3f}",
                    str(r["total_fields"]),
                    r["exact_accuracy_pct"],
                    r["normalized_accuracy_pct"],
                )
            console.print(cal_table)
            console.print()

            # 3. Artifact Paths
            art_text = (
                f"• Extraction Logs : [blue]{file_paths['extraction_results']}[/blue]\n"
                f"• Field Accuracy  : [blue]{file_paths['field_level_accuracy']}[/blue]\n"
                f"• Calibration CSV : [blue]{file_paths['confidence_calibration']}[/blue]\n"
                f"• Summary JSON    : [blue]{file_paths['routing_and_cost']}[/blue]"
            )
            console.print(Panel(art_text, title="Generated Artifacts", border_style="blue"))
        else:
            print("=" * 80)
            print(f"Total Documents Evaluated: {summary['total_documents']}")
            print(f"STP (Straight-Through):    {summary['straight_through_processing']['count']} ({summary['straight_through_processing']['rate_pct']}%)")
            print(f"Human Review Queue:        {summary['human_review_queue']['count']} ({summary['human_review_queue']['rate_pct']}%)")
            print(f"Rejection Queue:           {summary['rejection_queue']['count']} ({summary['rejection_queue']['rate_pct']}%)")
            print(f"Post-Review Accuracy:      {summary['post_review_field_accuracy_pct']}%")
            print(f"Total Pipeline Cost:       ${econ['total_pipeline_cost']:.2f} (Baseline: ${econ['baseline_manual_cost']:.2f})")
            print(f"Net Savings:               ${econ['net_savings_dollars']:.2f} ({econ['net_savings_pct']}%)")
            print("=" * 80)


def main() -> None:
    """CLI runner to execute full document extraction pipeline evaluation."""
    parser = argparse.ArgumentParser(description="Document Extraction Pipeline Evaluator")
    parser.add_argument("--run", action="store_true", help="Run evaluation across all 100 documents.")
    parser.add_argument("--threshold", type=float, default=0.85, help="STP routing confidence threshold (default 0.85).")

    args = parser.parse_args()

    evaluator = PipelineEvaluator(routing_threshold=args.threshold)
    results = evaluator.run_evaluations()
    saved_files = evaluator.save_artifacts(results)
    evaluator.display_results(results, saved_files)


if __name__ == "__main__":
    main()
