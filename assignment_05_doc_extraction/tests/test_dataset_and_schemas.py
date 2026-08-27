"""Unit tests for Assignment 5: Schemas, Validation Engine, and 100-Sample Dataset Integrity."""

import json
import unittest
from pathlib import Path
import sys

# Ensure assignment_05_doc_extraction root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dataset_generator import DatasetGenerator
from src.schema_validator import SchemaValidator


class TestSchemasAndValidation(unittest.TestCase):
    """Test JSON schemas and SchemaValidator logic against valid and invalid payloads."""

    def setUp(self):
        self.validator = SchemaValidator()

    def test_schemas_loaded(self):
        """Verify all 3 document schemas are successfully loaded."""
        self.assertIn("invoice", self.validator.schemas)
        self.assertIn("insurance_claim", self.validator.schemas)
        self.assertIn("kyc_identity", self.validator.schemas)

    def test_valid_invoice(self):
        """Verify compliant invoice passes schema validation."""
        valid_inv = {
            "invoice_number": "INV-2026-001",
            "vendor_name": "Acme Hardware Corp",
            "invoice_date": "2026-05-12",
            "total_amount": 1250.50,
            "tax_amount": 103.16,
            "currency": "USD",
            "line_items_count": 4,
        }
        ok, errors = self.validator.validate("invoice", valid_inv)
        self.assertTrue(ok, f"Validation errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_invalid_invoice_missing_and_types(self):
        """Verify invalid invoice catches missing fields, negative amounts, and bad dates."""
        bad_inv = {
            "invoice_number": "INV-999",
            # Missing vendor_name
            "invoice_date": "2026-02-31",  # Invalid calendar date
            "total_amount": -50.0,         # Below minimum 0.0
            "tax_amount": "ten dollars",   # Wrong type (string instead of number)
            "currency": "US",              # Bad currency code (needs 3 letters)
            "line_items_count": 0,         # Minimum is 1
            "extra_field": "disallowed",   # additionalProperties is false
        }
        ok, errors = self.validator.validate("invoice", bad_inv)
        self.assertFalse(ok)
        error_text = " ".join(errors)
        self.assertIn("vendor_name", error_text)
        self.assertIn("calendar date", error_text)
        self.assertIn("below minimum", error_text)
        self.assertIn("currency", error_text)
        self.assertIn("extra_field", error_text)

    def test_valid_insurance_claim(self):
        """Verify compliant insurance claim passes validation."""
        valid_claim = {
            "claim_id": "CLM-98214",
            "policy_number": "POL-104921",
            "patient_name": "Alexander Wright",
            "hospital_name": "Saint Jude Medical Center",
            "admission_date": "2026-03-14",
            "claim_amount": 4200.00,
            "diagnosis_code": "M54.5",
        }
        ok, errors = self.validator.validate("insurance_claim", valid_claim)
        self.assertTrue(ok, f"Validation errors: {errors}")

    def test_invalid_insurance_claim_bad_icd10(self):
        """Verify invalid ICD-10 codes and bad claim IDs fail."""
        bad_claim = {
            "claim_id": "INVALID_ID",       # Must start with CLM-
            "policy_number": "POL-12345",
            "patient_name": "P",            # Below minLength 2
            "hospital_name": "Clinic X",
            "admission_date": "2026-01-01",
            "claim_amount": 100.0,
            "diagnosis_code": "999.99",     # Must start with letter
        }
        ok, errors = self.validator.validate("insurance_claim", bad_claim)
        self.assertFalse(ok)
        error_text = " ".join(errors)
        self.assertIn("claim_id", error_text)
        self.assertIn("patient_name", error_text)
        self.assertIn("diagnosis_code", error_text)

    def test_valid_kyc_with_and_without_expiry(self):
        """Verify KYC documents validate with both string and null expiry dates."""
        kyc_with_exp = {
            "id_number": "PAS-9821441",
            "full_name": "Jessica Alpert",
            "dob": "1988-07-21",
            "expiry_date": "2032-07-20",
            "document_type": "passport",
            "nationality": "United States",
        }
        ok, errors = self.validator.validate("kyc_identity", kyc_with_exp)
        self.assertTrue(ok, f"Errors: {errors}")

        kyc_null_exp = dict(kyc_with_exp)
        kyc_null_exp["expiry_date"] = None
        ok, errors = self.validator.validate("kyc_identity", kyc_null_exp)
        self.assertTrue(ok, f"Errors: {errors}")

    def test_invalid_kyc_document_type(self):
        """Verify unauthorized KYC document type is rejected by enum check."""
        bad_kyc = {
            "id_number": "ID-12345",
            "full_name": "John Doe",
            "dob": "1990-01-01",
            "expiry_date": "2030-01-01",
            "document_type": "library_card",  # Not in allowed enum
            "nationality": "Canada",
        }
        ok, errors = self.validator.validate("kyc_identity", bad_kyc)
        self.assertFalse(ok)
        self.assertIn("library_card", " ".join(errors))


class TestGroundTruthDataset(unittest.TestCase):
    """Verify ground truth dataset generation, distribution counts, and schema conformance."""

    @classmethod
    def setUpClass(cls):
        generator = DatasetGenerator()
        cls.gt_path = generator.export_dataset()
        with open(cls.gt_path, "r", encoding="utf-8") as f:
            cls.dataset = json.load(f)
        cls.validator = SchemaValidator()

    def test_exact_dataset_size(self):
        """Verify dataset contains exactly 100 documents."""
        self.assertEqual(len(self.dataset), 100)

    def test_unique_document_ids(self):
        """Verify all doc_id identifiers are unique."""
        ids = [doc["doc_id"] for doc in self.dataset]
        self.assertEqual(len(ids), len(set(ids)))

    def test_document_type_distribution(self):
        """Verify distribution: 40 Invoices, 35 Insurance Claims, 25 KYC."""
        counts = {}
        for doc in self.dataset:
            dt = doc["doc_type"]
            counts[dt] = counts.get(dt, 0) + 1

        self.assertEqual(counts.get("invoice"), 40)
        self.assertEqual(counts.get("insurance_claim"), 35)
        self.assertEqual(counts.get("kyc_identity"), 25)

    def test_quality_tier_distribution(self):
        """Verify distribution: 60 clean, 20 degraded, 10 handwritten, 10 unreadable."""
        counts = {}
        for doc in self.dataset:
            qt = doc["quality_tier"]
            counts[qt] = counts.get(qt, 0) + 1

        self.assertEqual(counts.get("clean"), 60)
        self.assertEqual(counts.get("degraded"), 20)
        self.assertEqual(counts.get("handwritten"), 10)
        self.assertEqual(counts.get("unreadable"), 10)

    def test_rejection_criteria_integrity(self):
        """Verify exactly 10 documents are flagged should_reject=True (all unreadable tier)."""
        rejected = [d for d in self.dataset if d["should_reject"]]
        self.assertEqual(len(rejected), 10)

        for d in rejected:
            self.assertEqual(d["quality_tier"], "unreadable")
            self.assertIsNone(d["expected_fields"])

    def test_all_non_rejected_pass_schema_validation(self):
        """Verify all 90 non-rejected documents strictly satisfy their target JSON schema."""
        non_rejected = [d for d in self.dataset if not d["should_reject"]]
        self.assertEqual(len(non_rejected), 90)

        for d in non_rejected:
            ok, errors = self.validator.validate(d["doc_type"], d["expected_fields"])
            self.assertTrue(ok, f"Document {d['doc_id']} failed validation: {errors}")

    def test_raw_text_content_non_empty(self):
        """Verify every document contains simulated OCR raw text."""
        for d in self.dataset:
            text = d.get("raw_text_content")
            self.assertIsNotNone(text)
            self.assertGreater(len(text.strip()), 20)


if __name__ == "__main__":
    unittest.main()
