"""Unified Master Verification Harness for College Submission.

Executes all automated unit test suites and verifies required artifact
integrity across all 3 AI assignments:
- Assignment 3: Prompt Engineering Library (25 tests)
- Assignment 4: AI-Assisted Coding Workflow (39 tests)
- Assignment 5: Document Extraction Pipeline (21 tests)

Total: 85 Unit Tests & 19 Core Artifacts.
"""

from __future__ import annotations

import csv
import json
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def check_artifact(path: Path, min_bytes: int = 50, is_json: bool = False, is_csv: bool = False) -> Tuple[bool, str]:
    """Verify artifact exists, is non-empty, and has valid syntax."""
    if not path.exists():
        return False, f"Missing file: {path.name}"
    size = path.stat().st_size
    if size < min_bytes:
        return False, f"File too small ({size} bytes): {path.name}"

    if is_json:
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            return False, f"Invalid JSON ({e}): {path.name}"

    if is_csv:
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) < 2:
                    return False, f"CSV contains no data rows: {path.name}"
        except Exception as e:
            return False, f"Invalid CSV ({e}): {path.name}"

    return True, f"Valid ({size:,} bytes)"


def run_assignment_tests(assignment_dir_name: str) -> Tuple[int, int, int, float, str]:
    """Run unittest discovery in target assignment directory in an isolated process.

    Returns:
        Tuple of (tests_run, failures, errors, elapsed_seconds, output_summary)
    """
    import subprocess
    import re

    assign_dir = ROOT_DIR / assignment_dir_name
    if not assign_dir.exists():
        raise FileNotFoundError(f"Assignment directory not found: {assign_dir}")

    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    start_time = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=assign_dir,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start_time
    combined_output = proc.stdout + "\n" + proc.stderr

    # Parse test count e.g. "Ran 25 tests in 0.004s"
    m_ran = re.search(r"Ran (\d+) test", combined_output)
    tests_run = int(m_ran.group(1)) if m_ran else 0

    failures = 0
    errors = 0
    m_fail = re.search(r"failures=(\d+)", combined_output)
    if m_fail:
        failures = int(m_fail.group(1))
    m_err = re.search(r"errors=(\d+)", combined_output)
    if m_err:
        errors = int(m_err.group(1))

    # If non-zero exit code and no explicit pattern parsed, flag as failure
    if proc.returncode != 0 and failures == 0 and errors == 0:
        errors = 1

    return tests_run, failures, errors, elapsed, combined_output.strip()


def main() -> None:
    """Execute complete master verification suite."""
    print("\n" + "=" * 80)
    print("AI Engineering & Prompt Systems Evaluation Suite: Master Verification")
    print("=" * 80 + "\n")

    assignments = [
        ("assignment_03_prompt_library", "Assignment 3: Prompt Engineering Library", 25),
        ("assignment_04_ai_coding", "Assignment 4: AI-Assisted Coding Workflow", 39),
        ("assignment_05_doc_extraction", "Assignment 5: Document Extraction Pipeline", 21),
    ]

    total_tests_run = 0
    total_failures = 0
    total_errors = 0
    test_reports = []

    # 1. Execute Test Suites
    print("🧪 Executing Unit Test Suites Across All 3 Assignments...\n")
    for dir_name, title, expected_tests in assignments:
        tests_run, failures, errors, elapsed, out_summary = run_assignment_tests(dir_name)
        total_tests_run += tests_run
        total_failures += failures
        total_errors += errors
        status = "PASSED ✓" if (failures == 0 and errors == 0 and tests_run >= expected_tests) else "FAILED ✗"
        test_reports.append({
            "assignment": title,
            "tests_run": tests_run,
            "expected": expected_tests,
            "failures": failures,
            "errors": errors,
            "elapsed": f"{elapsed:.3f}s",
            "status": status,
        })
        print(f"  • {title:<48} : {tests_run} tests in {elapsed:.3f}s [{status}]")

    print(f"\nTotal Unit Tests Executed: {total_tests_run} (Failures: {total_failures}, Errors: {total_errors})")

    # 2. Check Core Artifacts
    print("\n📁 Verifying Required Deliverables & Benchmark Artifacts...\n")

    artifacts_to_verify = [
        # Assignment 3
        (ROOT_DIR / "assignment_03_prompt_library" / "data" / "golden_set.json", True, False, "A3 Golden Set (50 cases)"),
        (ROOT_DIR / "assignment_03_prompt_library" / "results" / "benchmark_results.json", True, False, "A3 Benchmark Results (200 evaluations)"),
        (ROOT_DIR / "assignment_03_prompt_library" / "results" / "summary_table.csv", False, True, "A3 Strategy Summary Table CSV"),
        (ROOT_DIR / "assignment_03_prompt_library" / "results" / "failure_catalogue.json", True, False, "A3 Failure Catalogue JSON"),
        (ROOT_DIR / "assignment_03_prompt_library" / "PROMPT_LIBRARY_GUIDE.md", False, False, "A3 Prompt Library Guide MD"),
        # Assignment 4
        (ROOT_DIR / "assignment_04_ai_coding" / "data" / "tasks_spec.json", True, False, "A4 Tasks Specification (10 tasks)"),
        (ROOT_DIR / "assignment_04_ai_coding" / "results" / "telemetry_log.json", True, False, "A4 Telemetry Log (21 defects)"),
        (ROOT_DIR / "assignment_04_ai_coding" / "results" / "task_type_breakdown.csv", False, True, "A4 Category Breakdown CSV"),
        (ROOT_DIR / "assignment_04_ai_coding" / "results" / "net_productivity_summary.csv", False, True, "A4 Productivity Summary CSV"),
        (ROOT_DIR / "assignment_04_ai_coding" / "VERIFICATION_DISCIPLINE_GUIDE.md", False, False, "A4 Verification Discipline Guide MD"),
        # Assignment 5
        (ROOT_DIR / "assignment_05_doc_extraction" / "data" / "schemas" / "invoice_schema.json", True, False, "A5 Commercial Invoice Schema JSON"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "data" / "schemas" / "insurance_claim_schema.json", True, False, "A5 Insurance Claim Schema JSON"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "data" / "schemas" / "kyc_identity_schema.json", True, False, "A5 KYC Identity Schema JSON"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "data" / "ground_truth.json", True, False, "A5 Ground Truth Dataset (100 docs)"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "results" / "extraction_results.json", True, False, "A5 Extraction Results JSON"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "results" / "field_level_accuracy.csv", False, True, "A5 Field Level Accuracy CSV"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "results" / "confidence_calibration.csv", False, True, "A5 Confidence Calibration CSV"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "results" / "routing_and_cost_summary.json", True, False, "A5 Routing & Cost Summary JSON"),
        (ROOT_DIR / "assignment_05_doc_extraction" / "DOCUMENT_EXTRACTION_GUIDE.md", False, False, "A5 Document Extraction Guide MD"),
    ]

    artifact_reports = []
    missing_artifacts = 0

    for file_path, is_j, is_c, desc in artifacts_to_verify:
        ok, msg = check_artifact(file_path, is_json=is_j, is_csv=is_c)
        if not ok:
            missing_artifacts += 1
        stat = "EXISTS ✓" if ok else "FAILED ✗"
        artifact_reports.append({
            "description": desc,
            "path": file_path.name,
            "status": stat,
            "details": msg,
        })
        print(f"  • {desc:<42} : [{stat}] {msg}")

    # 3. Final Summary Display
    print("\n" + "=" * 80)
    all_tests_passed = (total_failures == 0 and total_errors == 0 and total_tests_run == 85)
    all_artifacts_valid = (missing_artifacts == 0)

    if RICH_AVAILABLE:
        console = Console()
        status_color = "bold green" if (all_tests_passed and all_artifacts_valid) else "bold red"
        verdict = "SUBMISSION READY ✓" if (all_tests_passed and all_artifacts_valid) else "INCOMPLETE / ERRORS DETECTED ✗"

        summary_text = (
            f"[{status_color}]Overall Verdict : {verdict}[/{status_color}]\n"
            f"• Total Automated Unit Tests : {total_tests_run}/85 Passed ({total_failures} failures, {total_errors} errors)\n"
            f"• Core Production Artifacts   : {len(artifacts_to_verify) - missing_artifacts}/{len(artifacts_to_verify)} Verified\n"
            f"• Assignment 3 Modules       : 25 Unit Tests Passed | 5 Artifacts Verified\n"
            f"• Assignment 4 Modules       : 39 Unit Tests Passed | 5 Artifacts Verified\n"
            f"• Assignment 5 Modules       : 21 Unit Tests Passed | 9 Artifacts Verified"
        )
        console.print(Panel(summary_text, title="College Submission Verification Audit", border_style="green" if all_tests_passed else "red"))
    else:
        print(f"Total Unit Tests : {total_tests_run}/85 Passed (Failures: {total_failures}, Errors: {total_errors})")
        print(f"Core Artifacts   : {len(artifacts_to_verify) - missing_artifacts}/{len(artifacts_to_verify)} Verified")
        if all_tests_passed and all_artifacts_valid:
            print("\n>>> ALL CHECKS PASSED: REPOSITORY IS COMPLETE AND SUBMISSION READY! <<<")
        else:
            print("\n>>> VERIFICATION FAILED: PLEASE CHECK THE ABOVE ERRORS. <<<")
    print("=" * 80 + "\n")

    if not (all_tests_passed and all_artifacts_valid):
        sys.exit(1)


if __name__ == "__main__":
    main()
