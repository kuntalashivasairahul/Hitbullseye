"""Unit tests for TelemetryRunner, TaskTelemetry metric calculations, and defect categorization."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure assignment_04_ai_coding root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.telemetry_runner import (
    DefectEntry,
    TaskTelemetry,
    TelemetryRunner,
    VALID_DEFECT_CATEGORIES,
)


class TestTaskTelemetryMetrics(unittest.TestCase):
    """Test mathematical formulas for acceptance rate, raw time saved, and net productivity."""

    def test_acceptance_rate_formula(self):
        """Verify acceptance_rate_pct = (lines_kept / lines_generated) * 100."""
        t = TaskTelemetry(
            task_id="TEST_01",
            title="Test Task",
            category="boilerplate",
            unassisted_time_min=60.0,
            generation_time_min=2.0,
            review_time_min=5.0,
            correction_time_min=5.0,
            lines_generated=100,
            lines_kept=85,
            lines_modified=15,
        )
        self.assertEqual(t.acceptance_rate_pct, 85.0)

        # Zero lines generated edge case
        t_zero = TaskTelemetry(
            task_id="TEST_ZERO",
            title="Zero Gen",
            category="boilerplate",
            unassisted_time_min=10.0,
            generation_time_min=0.0,
            review_time_min=0.0,
            correction_time_min=0.0,
            lines_generated=0,
            lines_kept=0,
            lines_modified=0,
        )
        self.assertEqual(t_zero.acceptance_rate_pct, 0.0)

    def test_raw_time_saved_formula(self):
        """Verify raw_time_saved_pct = ((unassisted - gen) / unassisted) * 100."""
        t = TaskTelemetry(
            task_id="TEST_02",
            title="Test Task",
            category="boilerplate",
            unassisted_time_min=100.0,
            generation_time_min=10.0,
            review_time_min=20.0,
            correction_time_min=20.0,
            lines_generated=50,
            lines_kept=40,
            lines_modified=10,
        )
        # ((100 - 10) / 100) * 100 = 90.0%
        self.assertEqual(t.raw_time_saved_pct, 90.0)

    def test_net_productivity_formula(self):
        """Verify net_productivity_pct = ((unassisted - (gen + review + correction)) / unassisted) * 100."""
        # Positive net productivity
        t_pos = TaskTelemetry(
            task_id="TEST_POS",
            title="Productive Task",
            category="boilerplate",
            unassisted_time_min=60.0,
            generation_time_min=2.0,
            review_time_min=8.0,
            correction_time_min=10.0,  # Total assisted: 20m
            lines_generated=100,
            lines_kept=90,
            lines_modified=10,
        )
        # ((60 - 20) / 60) * 100 = 66.7%
        self.assertEqual(t_pos.net_productivity_pct, 66.7)

        # Negative net productivity (e.g. debugging / complex algorithm where fix takes longer)
        t_neg = TaskTelemetry(
            task_id="TEST_NEG",
            title="Negative ROI Task",
            category="algorithm",
            unassisted_time_min=50.0,
            generation_time_min=5.0,
            review_time_min=25.0,
            correction_time_min=30.0,  # Total assisted: 60m
            lines_generated=100,
            lines_kept=40,
            lines_modified=60,
        )
        # ((50 - 60) / 50) * 100 = -20.0%
        self.assertEqual(t_neg.net_productivity_pct, -20.0)

    def test_defect_category_validation(self):
        """Ensure defect categories are strictly validated."""
        for valid_cat in VALID_DEFECT_CATEGORIES:
            d = DefectEntry(category=valid_cat, description="Sample defect")
            self.assertEqual(d.category, valid_cat)

        with self.assertRaises(ValueError):
            DefectEntry(category="invalid_category_xyz", description="Bad defect")


class TestTelemetryRunner(unittest.TestCase):
    """Test TelemetryRunner execution, category aggregations, and file exports."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.runner = TelemetryRunner(results_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empirical_data_integrity(self):
        """Verify empirical dataset covers exactly 10 tasks across all categories."""
        data = self.runner.get_empirical_data()
        self.assertEqual(len(data), 10)

        categories = {t.category for t in data}
        expected_categories = {"boilerplate", "algorithm", "refactoring", "test_writing", "debugging", "integration"}
        self.assertEqual(categories, expected_categories)

        for t in data:
            self.assertGreater(t.unassisted_time_min, 0)
            self.assertGreater(t.generation_time_min, 0)
            self.assertGreaterEqual(t.lines_generated, t.lines_kept)
            self.assertEqual(t.lines_kept + t.lines_modified, t.lines_generated)

    def test_category_breakdown_aggregation(self):
        """Verify category breakdown calculates averages correctly."""
        data = self.runner.get_empirical_data()
        breakdown = self.runner.compute_category_breakdown(data)
        self.assertEqual(len(breakdown), 6)

        boilerplate_row = next(b for b in breakdown if b["category"] == "boilerplate")
        self.assertEqual(boilerplate_row["task_count"], 2)
        self.assertIn("%", boilerplate_row["avg_acceptance_rate_pct"])
        self.assertIn("%", boilerplate_row["avg_net_productivity_pct"])

    def test_save_artifacts(self):
        """Verify generation of telemetry_log.json and summary CSVs."""
        data = self.runner.get_empirical_data()
        breakdown = self.runner.compute_category_breakdown(data)
        files = self.runner.save_artifacts(data, breakdown)

        self.assertTrue(files["telemetry_log"].exists())
        self.assertTrue(files["category_breakdown"].exists())
        self.assertTrue(files["productivity_summary"].exists())

        with open(files["telemetry_log"], "r", encoding="utf-8") as f:
            log_data = json.load(f)
        self.assertEqual(len(log_data), 10)
        self.assertIn("defects_detected", log_data[0])


if __name__ == "__main__":
    unittest.main()
