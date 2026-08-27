"""Unit tests for the dataset generator and golden set data integrity."""

import json
import re
import unittest
from pathlib import Path
import sys

# Ensure src is importable
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dataset_generator import (
    EXPECTED_DISTRIBUTION,
    TOTAL_EXPECTED_CASES,
    VALID_CATEGORIES,
    TestCase,
    generate_dataset,
    save_dataset,
    validate_dataset,
)


class TestDatasetGenerator(unittest.TestCase):
    """Test suite for golden set generation and schema validation."""

    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.data_file = cls.project_root / "data" / "golden_set.json"
        cls.dataset = generate_dataset()

    def test_total_count(self):
        """Ensure dataset contains exactly 50 test cases."""
        self.assertEqual(len(self.dataset), TOTAL_EXPECTED_CASES)

    def test_category_distribution(self):
        """Ensure distribution matches exact requirements."""
        counts = {}
        for item in self.dataset:
            c = item["category"]
            counts[c] = counts.get(c, 0) + 1

        self.assertEqual(counts.get("standard", 0), 25)
        self.assertEqual(counts.get("hostile", 0), 10)
        self.assertEqual(counts.get("ambiguous", 0), 8)
        self.assertEqual(counts.get("out_of_scope", 0), 7)
        self.assertEqual(counts, EXPECTED_DISTRIBUTION)

    def test_id_formatting_and_uniqueness(self):
        """Ensure IDs are sequential and formatted as CASE_001 to CASE_050."""
        seen_ids = set()
        for idx, item in enumerate(self.dataset, start=1):
            expected_id = f"CASE_{idx:03d}"
            self.assertEqual(item["id"], expected_id)
            self.assertNotIn(item["id"], seen_ids)
            seen_ids.add(item["id"])
            self.assertTrue(re.match(r"^CASE_\d{3}$", item["id"]))

    def test_required_schema_fields(self):
        """Verify each test case contains all required schema fields."""
        required_fields = {
            "id",
            "category",
            "input_text",
            "expected_intent",
            "expected_resolution",
            "expected_format",
            "acceptance_criteria",
        }
        for item in self.dataset:
            self.assertEqual(set(item.keys()), required_fields, f"Field mismatch in {item.get('id')}")
            self.assertIn(item["category"], VALID_CATEGORIES)
            self.assertIn(item["expected_format"], {"plain_text", "bulleted_steps", "json"})
            self.assertIsInstance(item["input_text"], str)
            self.assertGreater(len(item["input_text"].strip()), 0)
            self.assertIsInstance(item["expected_intent"], str)
            self.assertGreater(len(item["expected_intent"].strip()), 0)
            self.assertIsInstance(item["expected_resolution"], str)
            self.assertGreater(len(item["expected_resolution"].strip()), 0)

    def test_acceptance_criteria_bounds(self):
        """Verify acceptance_criteria has 2-3 specific rules."""
        for item in self.dataset:
            criteria = item["acceptance_criteria"]
            self.assertIsInstance(criteria, list)
            self.assertGreaterEqual(len(criteria), 2, f"Fewer than 2 criteria in {item['id']}")
            self.assertLessEqual(len(criteria), 3, f"More than 3 criteria in {item['id']}")
            for rule in criteria:
                self.assertIsInstance(rule, str)
                self.assertGreater(len(rule.strip()), 0)

    def test_golden_set_file_persistence_and_reloading(self):
        """Verify saved golden_set.json matches generated dataset exactly."""
        saved_path = save_dataset(self.dataset, self.data_file)
        self.assertTrue(saved_path.exists())

        with open(saved_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(len(loaded_data), TOTAL_EXPECTED_CASES)
        self.assertEqual(loaded_data, self.dataset)

    def test_validation_fails_on_corrupt_data(self):
        """Verify validation function raises ValueError on malformed inputs."""
        corrupted = list(self.dataset)

        # Truncate dataset
        with self.assertRaises(ValueError):
            validate_dataset(corrupted[:-1])

        # Bad category
        bad_category_dataset = [dict(item) for item in self.dataset]
        bad_category_dataset[0]["category"] = "invalid_category"
        with self.assertRaises(ValueError):
            validate_dataset(bad_category_dataset)

        # Bad criteria count
        bad_criteria_dataset = [dict(item) for item in self.dataset]
        bad_criteria_dataset[0]["acceptance_criteria"] = ["only one rule"]
        with self.assertRaises(ValueError):
            validate_dataset(bad_criteria_dataset)


if __name__ == "__main__":
    unittest.main()
