"""Task Manager and CLI verification tool for Assignment 4.

Provides inspection, category filtering, and independent test execution
for the 10 software engineering tasks.
"""

from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

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


class TaskManager:
    """Manages task specifications, catalog inspection, and test verification."""

    def __init__(self, data_path: Optional[Path | str] = None):
        self.data_path = Path(data_path or (PROJECT_ROOT / "data" / "tasks_spec.json")).resolve()
        self._tasks: List[Dict[str, Any]] = self._load_specs()

    def _load_specs(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Task specifications not found at: {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_tasks(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks, optionally filtered by category."""
        if not category:
            return list(self._tasks)
        cat_lower = category.strip().lower()
        return [t for t in self._tasks if t.get("category", "").lower() == cat_lower]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task by its unique identifier."""
        task_id_upper = task_id.strip().upper()
        for t in self._tasks:
            if t.get("task_id", "").upper() == task_id_upper:
                return t
        return None

    def run_tests(self, test_suite_name: Optional[str] = None) -> Dict[str, Any]:
        """Execute independent test suites and report execution statistics."""
        loader = unittest.TestLoader()
        if test_suite_name:
            import tests.test_task_suites as suite_module
            if not hasattr(suite_module, test_suite_name):
                raise ValueError(f"Test suite '{test_suite_name}' not found in tests/test_task_suites.py")
            suite = loader.loadTestsFromTestCase(getattr(suite_module, test_suite_name))
        else:
            suite = loader.discover(str(PROJECT_ROOT / "tests"))

        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)

        return {
            "total_tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "passed": result.wasSuccessful(),
        }


def format_expected_interface(expected: Dict[str, Any]) -> str:
    """Format expected interface dictionary into readable summary string."""
    parts = []
    if "class_name" in expected:
        parts.append(f"class {expected['class_name']}")
    if "methods" in expected:
        methods = expected["methods"]
        if len(methods) <= 2:
            parts.extend(methods)
        else:
            parts.append(f"{methods[0]}; {methods[1]} (+{len(methods) - 2} more)")
    return " | ".join(parts)


def display_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Render task catalog to console."""
    if RICH_AVAILABLE:
        console = Console()
        console.print("\n[bold cyan]================================================================================[/bold cyan]")
        console.print("[bold cyan]Assignment 4: AI-Assisted Coding Workflow - Task Catalog[/bold cyan]")
        console.print("[bold cyan]================================================================================[/bold cyan]\n")

        table = Table(title=f"Registered Tasks ({len(tasks)} Total)", header_style="bold magenta")
        table.add_column("Task ID", style="bold cyan", justify="left")
        table.add_column("Category", style="yellow", justify="left")
        table.add_column("Title", style="white", justify="left")
        table.add_column("Difficulty", style="green", justify="center")
        table.add_column("Expected Interface", style="blue", justify="left")

        for t in tasks:
            iface_str = format_expected_interface(t.get("expected_interface", {}))
            table.add_row(
                t["task_id"],
                t["category"].replace("_", " ").title(),
                t["title"],
                t.get("difficulty", "medium").upper(),
                iface_str,
            )

        console.print(table)
        console.print()
    else:
        print("=" * 95)
        print(f"{'Task ID':<25} | {'Category':<15} | {'Title':<30} | {'Expected Interface'}")
        print("-" * 95)
        for t in tasks:
            iface_str = format_expected_interface(t.get("expected_interface", {}))
            print(f"{t['task_id']:<25} | {t['category']:<15} | {t['title']:<30} | {iface_str}")
        print("=" * 95)


def main() -> None:
    """CLI entrypoint for TaskManager."""
    parser = argparse.ArgumentParser(
        description="Assignment 4: AI-Assisted Coding Workflow - Task Manager CLI"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all tasks with categories, difficulties, and expected interfaces.",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter tasks by category (boilerplate, algorithm, refactoring, test_writing, debugging, integration).",
    )
    parser.add_argument(
        "--inspect",
        type=str,
        metavar="TASK_ID",
        help="Inspect complete specification and verification criteria for a specific task.",
    )
    parser.add_argument(
        "--verify",
        type=str,
        metavar="TASK_ID",
        help="Run verification test suite for a specific task.",
    )
    parser.add_argument(
        "--verify-all",
        action="store_true",
        help="Run independent test suites for all 10 tasks.",
    )

    args = parser.parse_args()
    mgr = TaskManager()

    if args.inspect:
        task = mgr.get_task(args.inspect)
        if not task:
            print(f"❌ Error: Task '{args.inspect}' not found.")
            sys.exit(1)
        print(json.dumps(task, indent=2))
        return

    if args.verify:
        task = mgr.get_task(args.verify)
        if not task:
            print(f"❌ Error: Task '{args.verify}' not found.")
            sys.exit(1)
        suite_name = task.get("test_suite")
        print(f"🧪 Verifying {task['task_id']} via {suite_name}...")
        res = mgr.run_tests(test_suite_name=suite_name)
        status = "PASSED ✓" if res["passed"] else "FAILED ✗"
        print(f"Result: {status} (Tests run: {res['total_tests']}, Failures: {res['failures']}, Errors: {res['errors']})")
        sys.exit(0 if res["passed"] else 1)

    if args.verify_all:
        print("🧪 Running verification test suite for all 10 tasks...")
        res = mgr.run_tests()
        status = "ALL PASSED ✓" if res["passed"] else "FAILURES DETECTED ✗"
        print(f"\n==================================================")
        print(f"Verification Status: {status}")
        print(f"Total Tests Run    : {res['total_tests']}")
        print(f"Failures           : {res['failures']}")
        print(f"Errors             : {res['errors']}")
        print(f"==================================================")
        sys.exit(0 if res["passed"] else 1)

    # Default action or --list
    tasks = mgr.list_tasks(category=args.category)
    display_tasks(tasks)


if __name__ == "__main__":
    main()
