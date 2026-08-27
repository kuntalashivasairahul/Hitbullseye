"""Unit tests for DocumentExtractor, CostModel, and PipelineEvaluator."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure assignment_05_doc_extraction root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cost_model import CostModel
from src.extractor import DocumentExtractor
from src.pipeline_evaluator import PipelineEvaluator


class TestDocumentExtractor(unittest.TestCase):
    """Test extraction logic across document types and rejection triggers."""

    def setUp(self):
        self.extractor = DocumentExtractor()

    def test_extract_clean_invoice(self):
        """Verify extraction from clean invoice text."""
        raw = (
            "TAX INVOICE\n"
            "Vendor: Acme Cloud Systems\n"
            "Invoice Number: INV-9901\n"
            "Date: 2026-04-10\n"
            "Currency: USD\n"
            "Line Items Count: 3\n"
            "Tax Amount: $82.50\n"
            "Total Amount Due: $1082.50\n"
        )
        res = self.extractor.extract("TEST_INV", "invoice", raw)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.extracted_fields["invoice_number"], "INV-9901")
        self.assertEqual(res.extracted_fields["vendor_name"], "Acme Cloud Systems")
        self.assertEqual(res.extracted_fields["total_amount"], 1082.50)
        self.assertGreater(res.confidence_score, 0.85)

    def test_extract_clean_insurance_claim(self):
        """Verify extraction from clean healthcare claim form."""
        raw = (
            "HEALTH INSURANCE REIMBURSEMENT FORM\n"
            "Claim Reference ID: CLM-4401\n"
            "Policyholder Number: POL-992144\n"
            "Patient Full Name: Emily Rodriguez\n"
            "Treating Facility: Mayo Regional Care Facility\n"
            "Admission Date: 2026-02-18\n"
            "Primary Diagnosis Code: J45.909\n"
            "Total Claimed Charges: $2450.00\n"
        )
        res = self.extractor.extract("TEST_CLM", "insurance_claim", raw)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.extracted_fields["claim_id"], "CLM-4401")
        self.assertEqual(res.extracted_fields["diagnosis_code"], "J45.909")
        self.assertGreater(res.confidence_score, 0.85)

    def test_extract_clean_kyc(self):
        """Verify extraction from clean identity document."""
        raw = (
            "GOVERNMENT IDENTITY VERIFICATION DOCUMENT\n"
            "Document Type: Passport\n"
            "Document ID Number: PAS-881920\n"
            "Full Legal Name: Alexander Wright\n"
            "Date of Birth: 1985-11-20\n"
            "Expiration Date: 2035-11-19\n"
            "Nationality / Citizenship: United States\n"
        )
        res = self.extractor.extract("TEST_KYC", "kyc_identity", raw)
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.extracted_fields["document_type"], "passport")
        self.assertEqual(res.extracted_fields["id_number"], "PAS-881920")
        self.assertGreater(res.confidence_score, 0.85)

    def test_rejection_trigger_on_corrupt_documents(self):
        """Verify unreadable or corrupted documents are rejected."""
        corrupt_raw = (
            "~~~~ CORRUPTED SCAN / UNREADABLE FRAGMENT ~~~~\n"
            "[Severe water damage covering 85% of header]\n"
            "Inv... # [BLURRED]\n"
        )
        res = self.extractor.extract("TEST_BAD", "invoice", corrupt_raw)
        self.assertEqual(res.status, "REJECTED")
        self.assertEqual(res.confidence_score, 0.0)
        self.assertIsNotNone(res.rejection_reason)


class TestCostModel(unittest.TestCase):
    """Test operational cost and savings calculations."""

    def test_cost_evaluation(self):
        """Verify baseline cost, review cost, and net savings formulas."""
        total_docs = 100
        stp_count = 60
        review_count = 30
        reject_count = 10

        res = CostModel.evaluate(total_docs, stp_count, review_count, reject_count)

        # Baseline: 100 * $1.80 = $180.00
        self.assertEqual(res.baseline_manual_cost, 180.00)
        # AI cost: 100 * $0.015 = $1.50
        self.assertEqual(res.ai_extraction_cost, 1.50)
        # Review cost: 30 * $0.60 = $18.00
        self.assertEqual(res.human_review_cost, 18.00)
        # Total pipeline: 1.50 + 18.00 = $19.50
        self.assertEqual(res.total_pipeline_cost, 19.50)
        # Net savings dollars: 180.00 - 19.50 = $160.50
        self.assertEqual(res.net_savings_dollars, 160.50)
        # Net savings %: (160.50 / 180.00) * 100 = 89.2%
        self.assertEqual(res.net_savings_pct, 89.2)
        # Rates
        self.assertEqual(res.stp_rate_pct, 60.0)
        self.assertEqual(res.human_review_rate_pct, 30.0)
        self.assertEqual(res.rejection_rate_pct, 10.0)


class TestPipelineEvaluator(unittest.TestCase):
    """Test pipeline evaluation, match comparisons, and calibration logic."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_match_helpers(self):
        """Verify exact and normalized match comparisons."""
        # Exact match
        self.assertTrue(PipelineEvaluator._is_exact_match(100.50, 100.50))
        self.assertFalse(PipelineEvaluator._is_exact_match("USA", "usa"))

        # Normalized match
        self.assertTrue(PipelineEvaluator._is_normalized_match("  USA  ", "usa"))
        self.assertTrue(PipelineEvaluator._is_normalized_match(15.000, 15.0))
        self.assertTrue(PipelineEvaluator._is_normalized_match(None, None))
        self.assertFalse(PipelineEvaluator._is_normalized_match("A", None))

    def test_run_evaluations_and_artifacts(self):
        """Verify full evaluation run against ground truth and artifact generation."""
        evaluator = PipelineEvaluator(results_dir=self.temp_dir, routing_threshold=0.85)
        results = evaluator.run_evaluations()

        self.assertEqual(len(results["records"]), 100)
        self.assertIn("straight_through_processing", results["routing_and_cost"])
        self.assertGreaterEqual(results["routing_and_cost"]["straight_through_processing"]["rate_pct"], 50.0)

        saved = evaluator.save_artifacts(results)
        self.assertTrue(saved["extraction_results"].exists())
        self.assertTrue(saved["field_level_accuracy"].exists())
        self.assertTrue(saved["confidence_calibration"].exists())
        self.assertTrue(saved["routing_and_cost"].exists())


if __name__ == "__main__":
    unittest.main()
