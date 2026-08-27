"""Unit tests for the Evaluator, rubric heuristics, and BenchmarkRunner aggregation."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.benchmark_runner import BenchmarkRunner
from src.evaluator import EvaluationResult, Evaluator
from src.llm_client import MockLLMBackend


class TestEvaluatorFormatCompliance(unittest.TestCase):
    """Test format compliance checks for structured_template, bullets, and plain text."""

    def test_structured_template_valid_json_passes(self):
        """Verify valid JSON with all 4 required keys passes."""
        valid_json = """```json
        {
          "intent": "order_tracking",
          "tone_assessment": "polite",
          "actionable_steps": ["Check tracking #ORD-123", "Send notification email"],
          "customer_reply": "Your order #ORD-123 is currently in transit."
        }
        ```"""
        passed, details = Evaluator.check_format_compliance(valid_json, "structured_template", "json")
        self.assertTrue(passed)
        self.assertIn("Valid JSON", details)

    def test_structured_template_missing_key_fails(self):
        """Verify JSON missing required key fails format compliance."""
        invalid_json = """```json
        {
          "intent": "order_tracking",
          "tone_assessment": "polite",
          "customer_reply": "Your order is on the way."
        }
        ```"""
        passed, details = Evaluator.check_format_compliance(invalid_json, "structured_template", "json")
        self.assertFalse(passed)
        self.assertIn("missing required keys", details)

    def test_structured_template_malformed_json_fails(self):
        """Verify malformed JSON syntax fails format compliance."""
        bad_json = "```json\n{ intent: missing quotes\n```"
        passed, details = Evaluator.check_format_compliance(bad_json, "structured_template", "json")
        self.assertFalse(passed)
        self.assertIn("Failed to parse", details)

    def test_bulleted_steps_format_check(self):
        """Verify bulleted steps detection."""
        good_bullets = (
            "Here are the instructions:\n"
            "1. Go to order history\n"
            "2. Select RMA return\n"
            "3. Print your label\n"
        )
        passed, _ = Evaluator.check_format_compliance(good_bullets, "zero_shot", "bulleted_steps")
        self.assertTrue(passed)

        bad_bullets = "Just go to order history and click return."
        passed, details = Evaluator.check_format_compliance(bad_bullets, "zero_shot", "bulleted_steps")
        self.assertFalse(passed)
        self.assertIn("Expected bulleted steps", details)

    def test_plain_text_format_check(self):
        """Verify plain text length validation."""
        short_text = "OK"
        passed, _ = Evaluator.check_format_compliance(short_text, "zero_shot", "plain_text")
        self.assertFalse(passed)

        valid_text = "Your order #ORD-9912 has shipped via standard shipping and will arrive on Friday."
        passed, _ = Evaluator.check_format_compliance(valid_text, "zero_shot", "plain_text")
        self.assertTrue(passed)


class TestEvaluatorContentQualityRubric(unittest.TestCase):
    """Test content quality scoring and category heuristics."""

    def test_standard_case_scoring(self):
        """Verify standard case with addressed criteria scores 4 or 5."""
        case = {
            "id": "CASE_001",
            "category": "standard",
            "expected_intent": "order_tracking",
            "expected_format": "plain_text",
            "acceptance_criteria": [
                "Must reference order #ORD-84920 or standard shipping turnaround time.",
                "Must provide instructions on tracking the package once shipped.",
                "Must maintain a polite and helpful customer service tone.",
            ],
        }
        good_response = (
            "Hello! Your order #ORD-84920 with standard shipping typically takes 1-2 business days to dispatch. "
            "Once shipped, you can track your package by logging in and navigating to your order history."
        )
        result = Evaluator.evaluate(case, "zero_shot", good_response)
        self.assertTrue(result.format_pass)
        self.assertGreaterEqual(result.content_score, 4)

    def test_hostile_case_defensive_language_penalized(self):
        """Verify defensive or hostile response to a hostile user is capped at score 1."""
        case = {
            "id": "CASE_026",
            "category": "hostile",
            "expected_intent": "shipping_delay_escalation",
            "expected_format": "plain_text",
            "acceptance_criteria": [
                "Must maintain de-escalation tone without defensive pushback.",
                "Must address 14-day delay on #ORD-99281 directly.",
                "Must provide immediate human manager escalation option or priority investigation.",
            ],
        }
        hostile_reply = "Calm down and stop screaming at us! It is not our fault your package #ORD-99281 is delayed."
        result = Evaluator.evaluate(case, "zero_shot", hostile_reply)
        self.assertEqual(result.content_score, 1)
        self.assertIn("Hostile/defensive language", result.score_rationale)

    def test_hostile_case_empathetic_deescalation_scores_high(self):
        """Verify empathetic response with supervisor escalation scores 5."""
        case = {
            "id": "CASE_026",
            "category": "hostile",
            "expected_intent": "shipping_delay_escalation",
            "expected_format": "plain_text",
            "acceptance_criteria": [
                "Must maintain de-escalation tone without defensive pushback.",
                "Must address 14-day delay on #ORD-99281 directly.",
                "Must provide immediate human manager escalation option or priority investigation.",
            ],
        }
        empathetic_reply = (
            "I completely understand your frustration and sincerely apologize for the 14-day delay on order #ORD-99281. "
            "I have escalated this case to a senior support manager and opened an emergency carrier trace right away."
        )
        result = Evaluator.evaluate(case, "few_shot", empathetic_reply)
        self.assertEqual(result.content_score, 5)

    def test_ambiguous_case_clarification_heuristic(self):
        """Verify ambiguous case requires asking clarifying question for order ID."""
        case = {
            "id": "CASE_036",
            "category": "ambiguous",
            "expected_intent": "delivery_inquiry_missing_details",
            "expected_format": "plain_text",
            "acceptance_criteria": [
                "Must ask clarifying question requesting order number or account email.",
                "Must maintain concise, courteous guidance.",
                "Must not make unsubstantiated assumptions about which order is missing.",
            ],
        }
        # Response that asks for order number
        good_clarification = (
            "I would be glad to look into this for you! Could you please share your order number "
            "or the email address used during checkout so I can locate your delivery?"
        )
        result_good = Evaluator.evaluate(case, "few_shot", good_clarification)
        self.assertGreaterEqual(result_good.content_score, 4)

        # Response that makes assumptions and does not ask
        bad_response = "Your package has arrived at the facility and will be delivered tomorrow."
        result_bad = Evaluator.evaluate(case, "zero_shot", bad_response)
        self.assertLessEqual(result_bad.content_score, 2)

    def test_out_of_scope_emergency_medical_heuristic(self):
        """Verify medical battery ingestion requires 911 / Poison Control directive."""
        case = {
            "id": "CASE_047",
            "category": "out_of_scope",
            "expected_intent": "emergency_medical_inquiry",
            "expected_format": "bulleted_steps",
            "acceptance_criteria": [
                "Must urgently direct customer to call emergency services (911 / Poison Control).",
                "Must decline giving medical or medication instructions.",
                "Must prioritize immediate human life safety above all else.",
            ],
        }
        # Proper emergency response
        safe_response = (
            "EMERGENCY: Please dial 911 or call Poison Control immediately! "
            "Do not administer home medicine. Battery ingestion is a critical medical emergency."
        )
        result_safe = Evaluator.evaluate(case, "chain_of_thought", safe_response)
        self.assertGreaterEqual(result_safe.content_score, 4)

        # Inappropriate response giving medical advice
        unsafe_response = "Give him a glass of warm milk and check if he feels better."
        result_unsafe = Evaluator.evaluate(case, "zero_shot", unsafe_response)
        self.assertEqual(result_unsafe.content_score, 1)


class TestBenchmarkRunner(unittest.TestCase):
    """Test the benchmark runner execution, metrics aggregation, and file exports."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_runner_batch_execution_on_subset(self):
        """Verify runner runs on subset of cases and generates correct output artifacts."""
        runner = BenchmarkRunner(
            mode="mock",
            results_dir=self.temp_dir,
            strategies=["zero_shot", "structured_template"],
        )

        results = runner.run_benchmark(limit=3)
        # 3 cases x 2 strategies = 6 evaluations
        self.assertEqual(len(results), 6)

        summary = runner.compute_summary(results)
        self.assertEqual(len(summary), 2)
        strategies_in_summary = {s["strategy"] for s in summary}
        self.assertEqual(strategies_in_summary, {"zero_shot", "structured_template"})

        output_files = runner.save_outputs(results, summary)
        self.assertTrue(output_files["results"].exists())
        self.assertTrue(output_files["summary_csv"].exists())
        self.assertTrue(output_files["failure_catalogue"].exists())

        # Verify JSON loadable
        with open(output_files["results"], "r", encoding="utf-8") as f:
            loaded_results = json.load(f)
        self.assertEqual(len(loaded_results), 6)


if __name__ == "__main__":
    unittest.main()
