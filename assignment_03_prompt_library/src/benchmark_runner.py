"""Benchmark Runner for Assignment 3: Prompt Engineering Library.

Orchestrates 200 evaluations (50 golden set cases x 4 prompt strategies):
- zero_shot
- few_shot
- chain_of_thought
- structured_template

Generates:
- results/benchmark_results.json
- results/summary_table.csv
- results/failure_catalogue.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluator import EvaluationResult, Evaluator
from src.llm_client import LLMResponse, MockLLMBackend, get_llm_client
from src.prompt_registry import PromptRegistry

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class BenchmarkRunner:
    """Orchestrates multi-strategy prompt evaluation batch runs."""

    def __init__(
        self,
        mode: str = "mock",
        data_path: Optional[Path | str] = None,
        results_dir: Optional[Path | str] = None,
        strategies: Optional[List[str]] = None,
    ):
        self.mode = mode
        self.project_root = PROJECT_ROOT
        self.data_path = Path(data_path or (self.project_root / "data" / "golden_set.json")).resolve()
        self.results_dir = Path(results_dir or (self.project_root / "results")).resolve()
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.strategies = strategies or [
            "zero_shot",
            "few_shot",
            "chain_of_thought",
            "structured_template",
        ]
        self.client = get_llm_client(mode=self.mode)

    def load_dataset(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load the golden dataset from JSON file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Golden dataset not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if limit and limit > 0:
            return data[:limit]
        return data

    def run_single(
        self,
        case: Dict[str, Any],
        strategy_name: str,
    ) -> Dict[str, Any]:
        """Execute a single test case evaluation under a prompt strategy."""
        query = case.get("input_text", "")
        meta = PromptRegistry.get_metadata(strategy_name)
        system_prompt = meta.get("system_prompt", "")
        formatted_prompt = PromptRegistry.format_prompt(strategy_name, query)

        # Execute inference
        start_time = time.perf_counter()
        if hasattr(self.client, "generate"):
            response: LLMResponse = self.client.generate(
                prompt=formatted_prompt,
                system_prompt=system_prompt,
                strategy_name=strategy_name,
                case=case,
            )
        else:
            response = MockLLMBackend.generate(
                prompt=formatted_prompt,
                system_prompt=system_prompt,
                strategy_name=strategy_name,
                case=case,
            )
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Evaluate response
        eval_result: EvaluationResult = Evaluator.evaluate(
            case=case,
            strategy_name=strategy_name,
            response_text=response.text,
        )

        return {
            "case_id": case.get("id"),
            "category": case.get("category"),
            "strategy": strategy_name,
            "input_text": query,
            "expected_intent": case.get("expected_intent"),
            "expected_format": case.get("expected_format"),
            "response_text": response.text,
            "latency_ms": response.latency_ms or round(duration_ms, 2),
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "model_name": response.model_name,
            "error": response.error,
            "format_pass": eval_result.format_pass,
            "format_details": eval_result.format_details,
            "content_score": eval_result.content_score,
            "score_rationale": eval_result.score_rationale,
            "criteria_results": eval_result.criteria_results,
            "heuristics_summary": eval_result.heuristics_summary,
            "extracted_reply": eval_result.extracted_reply,
        }

    def run_benchmark(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Run all test cases across all registered strategies."""
        dataset = self.load_dataset(limit=limit)
        all_results: List[Dict[str, Any]] = []

        total_runs = len(dataset) * len(self.strategies)
        current = 0

        for strat in self.strategies:
            for case in dataset:
                current += 1
                res = self.run_single(case, strat)
                all_results.append(res)

        return all_results

    def compute_summary(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate performance metrics grouped by strategy."""
        grouped: Dict[str, List[Dict[str, Any]]] = {s: [] for s in self.strategies}
        for r in results:
            grouped.setdefault(r["strategy"], []).append(r)

        summary = []
        for strat, items in grouped.items():
            total = len(items)
            if total == 0:
                continue

            format_passes = sum(1 for i in items if i["format_pass"])
            format_pass_rate = round((format_passes / total) * 100.0, 1)

            scores = [i["content_score"] for i in items]
            avg_score = round(sum(scores) / total, 2)

            score_dist = {f"score_{s}": scores.count(s) for s in range(1, 6)}
            avg_latency = round(sum(i["latency_ms"] for i in items) / total, 1)
            avg_tokens = round(sum(i["total_tokens"] for i in items) / total, 1)

            row = {
                "strategy": strat,
                "total_runs": total,
                "format_pass_rate": f"{format_pass_rate}%",
                "avg_content_score": avg_score,
                **score_dist,
                "avg_latency_ms": avg_latency,
                "avg_tokens": avg_tokens,
            }
            summary.append(row)

        return summary

    def save_outputs(
        self,
        results: List[Dict[str, Any]],
        summary: List[Dict[str, Any]],
    ) -> Dict[str, Path]:
        """Save results to JSON, CSV, and failure catalogue files."""
        # 1. Full detailed results
        results_file = self.results_dir / "benchmark_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 2. Summary CSV
        csv_file = self.results_dir / "summary_table.csv"
        if summary:
            fieldnames = list(summary[0].keys())
            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(summary)

        # 3. Failure catalogue (score < 4 or format_pass == False)
        failures = [
            r for r in results
            if r["content_score"] < 4 or not r["format_pass"]
        ]
        failures_file = self.results_dir / "failure_catalogue.json"
        with open(failures_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_failures": len(failures),
                    "failure_rate": f"{round((len(failures) / len(results)) * 100.0, 1) if results else 0}%",
                    "failures": failures,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        return {
            "results": results_file,
            "summary_csv": csv_file,
            "failure_catalogue": failures_file,
        }

    def print_display_summary(
        self,
        summary: List[Dict[str, Any]],
        results: List[Dict[str, Any]],
        output_files: Dict[str, Path],
    ) -> None:
        """Render summary table to console."""
        failures = [r for r in results if r["content_score"] < 4 or not r["format_pass"]]

        if RICH_AVAILABLE:
            console = Console()
            console.print("\n[bold cyan]======================================================================[/bold cyan]")
            console.print("[bold cyan]Prompt Engineering Evaluation Benchmark - Results[/bold cyan]")
            console.print("[bold cyan]======================================================================[/bold cyan]\n")

            table = Table(title="Performance Summary by Strategy", header_style="bold magenta")
            table.add_column("Strategy", style="cyan", justify="left")
            table.add_column("Runs", style="white", justify="right")
            table.add_column("Format Pass", style="green", justify="right")
            table.add_column("Avg Score", style="bold yellow", justify="right")
            table.add_column("Score 5", style="green", justify="right")
            table.add_column("Score 4", style="blue", justify="right")
            table.add_column("Score 3", style="yellow", justify="right")
            table.add_column("Score 2", style="magenta", justify="right")
            table.add_column("Score 1", style="red", justify="right")
            table.add_column("Avg Latency", style="white", justify="right")

            for s in summary:
                table.add_row(
                    s["strategy"],
                    str(s["total_runs"]),
                    s["format_pass_rate"],
                    f"{s['avg_content_score']:.2f}",
                    str(s["score_5"]),
                    str(s["score_4"]),
                    str(s["score_3"]),
                    str(s["score_2"]),
                    str(s["score_1"]),
                    f"{s['avg_latency_ms']} ms",
                )
            console.print(table)
            console.print()

            # Category Breakdown Table
            cat_table = Table(title="Category Breakdown (Average Content Score)", header_style="bold magenta")
            cat_table.add_column("Category", style="cyan", justify="left")
            for strat in self.strategies:
                cat_table.add_column(strat, style="yellow", justify="center")

            categories = ["standard", "hostile", "ambiguous", "out_of_scope"]
            for cat in categories:
                row_vals = [cat.replace("_", " ").title()]
                for strat in self.strategies:
                    cat_items = [r for r in results if r["strategy"] == strat and r["category"] == cat]
                    if cat_items:
                        avg_cat_score = sum(r["content_score"] for r in cat_items) / len(cat_items)
                        row_vals.append(f"{avg_cat_score:.2f}")
                    else:
                        row_vals.append("N/A")
                cat_table.add_row(*row_vals)
            console.print(cat_table)
            console.print()

            panel_text = (
                f"[bold]Total Evaluations:[/bold] {len(results)} (Mode: [yellow]{self.mode}[/yellow])\n"
                f"[bold]Failures / Sub-optimal (Score < 4 or Format Fail):[/bold] [red]{len(failures)}[/red] "
                f"({round(len(failures)/len(results)*100, 1)}%)\n\n"
                f"[bold green]Artifacts Generated:[/bold green]\n"
                f"• Detailed Logs   : [blue]{output_files['results']}[/blue]\n"
                f"• Summary Table   : [blue]{output_files['summary_csv']}[/blue]\n"
                f"• Failure Log     : [blue]{output_files['failure_catalogue']}[/blue]"
            )
            console.print(Panel(panel_text, title="[bold green]Benchmark Completed Successfully[/bold green]", border_style="green"))
        else:
            print("=" * 78)
            print(f"{'Strategy':<20} | {'Runs':<4} | {'Format':<7} | {'Avg Score':<9} | {'Score 5':<7} | {'Score 4':<7} | {'Latency'}")
            print("-" * 78)
            for s in summary:
                print(
                    f"{s['strategy']:<20} | {s['total_runs']:<4} | {s['format_pass_rate']:<7} | "
                    f"{s['avg_content_score']:<9.2f} | {s['score_5']:<7} | {s['score_4']:<7} | {s['avg_latency_ms']} ms"
                )
            print("=" * 78)
            print(f"Total Evaluations : {len(results)} | Failures (Score < 4 or Format Fail): {len(failures)}")
            print(f"Detailed Logs     : {output_files['results']}")
            print(f"Summary CSV       : {output_files['summary_csv']}")
            print(f"Failure Catalogue : {output_files['failure_catalogue']}")
            print("=" * 78)


def main() -> None:
    """CLI entrypoint for batch evaluation benchmark runner."""
    parser = argparse.ArgumentParser(
        description="Assignment 3: Prompt Engineering Evaluation Batch Runner"
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "live"],
        default="mock",
        help="Inference mode: 'mock' (deterministic, zero-cost) or 'live' (API keys). Default: mock.",
    )
    parser.add_argument(
        "--strategies",
        type=str,
        default="all",
        help="Comma-separated prompt strategies to evaluate (e.g., 'zero_shot,few_shot') or 'all'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of test cases for quick evaluation smoke testing.",
    )

    args = parser.parse_args()

    selected_strategies = None
    if args.strategies != "all":
        selected_strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    runner = BenchmarkRunner(mode=args.mode, strategies=selected_strategies)
    print(f"\n🚀 Launching Prompt Benchmark (Mode: {args.mode})...")
    results = runner.run_benchmark(limit=args.limit)
    summary = runner.compute_summary(results)
    output_files = runner.save_outputs(results, summary)
    runner.print_display_summary(summary, results, output_files)


if __name__ == "__main__":
    main()
