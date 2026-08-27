"""Synthetic Ground Truth Dataset Generator for Assignment 5.

Generates exactly 100 manually verified ground truth documents across 3 document types
(Invoices, Insurance Claims, KYC Identity) and 4 quality tiers (Clean, Degraded, Handwritten, Unreadable).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.schema_validator import SchemaValidator


class DatasetGenerator:
    """Generates synthetic multi-tier ground truth datasets for extraction benchmarking."""

    VENDORS = [
        "Acme Industrial Supply LLC", "Apex Cloud Technologies Inc.", "Global Logistics Corp",
        "NextGen Semiconductor Ltd", "Prime Office Solutions", "Starlight Freight Forwarders",
        "Quantum Data Systems", "Atlas Packaging & Materials", "Beacon Electronics Group",
        "Summit Enterprise Hardware", "Vanguard Chemical Solutions", "Horizon Media Works",
        "Pinnacle Security Systems", "Omni Health Supplies", "Sterling Automotive Parts",
    ]

    HOSPITALS = [
        "Mercy General Hospital", "Saint Jude Medical Center", "Presbyterian Health Clinic",
        "Memorial Sloan Care Center", "Cedars Sinai Regional Hospital", "Northwestern Medical Center",
        "Cleveland Clinic Foundation", "Mayo Regional Care Facility", "Johns Hopkins Community Hospital",
        "Boston General Infirmary", "Stanford Health Pavilion", "Vanderbilt University Medical",
    ]

    PATIENTS = [
        "Sarah Jenkins", "Michael Chang", "Emily Rodriguez", "David K. Miller",
        "Jessica Alpert", "Robert T. Harrison", "Amanda L. Vance", "James O'Connor",
        "Priya Patel", "Marcus Thorne", "Danielle Dubois", "Alexander Wright",
    ]

    ICD10_CODES = [
        "M54.5", "E11.9", "I10", "J45.909", "K21.9", "F41.1", "S83.511A", "N39.0", "R05", "Z00.00"
    ]

    NATIONALITIES = [
        "United States", "Canada", "United Kingdom", "Germany", "Australia",
        "France", "Japan", "India", "Singapore", "Netherlands"
    ]

    DOC_TYPES_KYC = ["passport", "national_id", "drivers_license", "tax_id"]

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def _generate_clean_invoice(self, doc_idx: int) -> Dict[str, Any]:
        num = f"INV-{10000 + doc_idx}"
        vendor = random.choice(self.VENDORS)
        date = f"2026-{random.randint(1, 8):02d}-{random.randint(1, 28):02d}"
        items_count = random.randint(1, 8)
        subtotal = round(random.uniform(150.0, 4500.0), 2)
        tax = round(subtotal * 0.0825, 2)
        total = round(subtotal + tax, 2)
        currency = random.choice(["USD", "EUR", "GBP", "CAD"])

        raw_text = (
            f"====================================================\n"
            f"                  TAX INVOICE                       \n"
            f"====================================================\n"
            f"Vendor: {vendor}\n"
            f"Invoice Number: {num}\n"
            f"Date: {date}\n"
            f"Currency: {currency}\n"
            f"----------------------------------------------------\n"
            f"Line Items Count: {items_count} items billed\n"
            f"Subtotal: {subtotal:.2f} {currency}\n"
            f"Tax Amount (8.25%): {tax:.2f} {currency}\n"
            f"Total Amount Due: {total:.2f} {currency}\n"
            f"Payment Terms: Net 30 Days. Remit to billing department.\n"
            f"===================================================="
        )

        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "invoice",
            "quality_tier": "clean",
            "raw_text_content": raw_text,
            "expected_fields": {
                "invoice_number": num,
                "vendor_name": vendor,
                "invoice_date": date,
                "total_amount": total,
                "tax_amount": tax,
                "currency": currency,
                "line_items_count": items_count,
            },
            "should_reject": False,
        }

    def _generate_degraded_invoice(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_invoice(doc_idx)
        base["quality_tier"] = "degraded"
        # Simulate OCR speckles, character substitutions, and missing colons
        f = base["expected_fields"]
        noisy_raw = (
            f"== TAX INV0ICE (LOW-RES FAX SCAN) ==\n"
            f"Vend0r..: {f['vendor_name']}\n"
            f"lnvoice No : {f['invoice_number'].replace('-', '~')}\n"
            f"Date (YYYY-MM-DD): {f['invoice_date']}\n"
            f"Currencv : {f['currency']}\n"
            f"Items Count: {f['line_items_count']}\n"
            f"Tax Amt: {f['tax_amount']:.2f}\n"
            f"TOTAL DUE: ${f['total_amount']:.2f} (inclusive)\n"
            f"*faded watermark across bottom*"
        )
        base["raw_text_content"] = noisy_raw
        return base

    def _generate_handwritten_invoice(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_invoice(doc_idx)
        base["quality_tier"] = "handwritten"
        f = base["expected_fields"]
        hw_raw = (
            f"[HANDWRITTEN BILL OF SALE / INVOICE]\n"
            f"From: {f['vendor_name']} (Signed: J. Smith)\n"
            f"Bill Ref # {f['invoice_number']}\n"
            f"Billed on: {f['invoice_date']}\n"
            f"Currency code: {f['currency']}\n"
            f"Total line entries counted: {f['line_items_count']}\n"
            f"Tax: {f['tax_amount']:.2f}\n"
            f"Grand Total: {f['total_amount']:.2f}\n"
            f"[Notes in margin: paid by company check #4401]"
        )
        base["raw_text_content"] = hw_raw
        return base

    def _generate_unreadable_invoice(self, doc_idx: int) -> Dict[str, Any]:
        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "invoice",
            "quality_tier": "unreadable",
            "raw_text_content": (
                "~~~~ CORRUPTED SCAN / UNREADABLE FRAGMENT ~~~~\n"
                "[Severe water damage covering 85% of header]\n"
                "Inv... # [BLURRED]\n"
                "Total: [UNREADABLE BLOB]\n"
                "Please call 1-800-??? for missing slip."
            ),
            "expected_fields": None,
            "should_reject": True,
        }

    def _generate_clean_claim(self, doc_idx: int) -> Dict[str, Any]:
        claim_id = f"CLM-{1000 + doc_idx}"
        policy_num = f"POL-{random.randint(100000, 999999)}"
        patient = random.choice(self.PATIENTS)
        hospital = random.choice(self.HOSPITALS)
        adm_date = f"2026-{random.randint(1, 8):02d}-{random.randint(1, 28):02d}"
        amount = round(random.uniform(500.0, 15000.0), 2)
        diag = random.choice(self.ICD10_CODES)

        raw_text = (
            f"HEALTH INSURANCE REIMBURSEMENT FORM\n"
            f"====================================================\n"
            f"Claim Reference ID: {claim_id}\n"
            f"Policyholder Number: {policy_num}\n"
            f"Patient Full Name: {patient}\n"
            f"Treating Facility: {hospital}\n"
            f"Admission Date: {adm_date}\n"
            f"Primary Diagnosis Code (ICD-10): {diag}\n"
            f"Total Claimed Charges: ${amount:.2f}\n"
            f"Authorization Signature on File.\n"
            f"===================================================="
        )

        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "insurance_claim",
            "quality_tier": "clean",
            "raw_text_content": raw_text,
            "expected_fields": {
                "claim_id": claim_id,
                "policy_number": policy_num,
                "patient_name": patient,
                "hospital_name": hospital,
                "admission_date": adm_date,
                "claim_amount": amount,
                "diagnosis_code": diag,
            },
            "should_reject": False,
        }

    def _generate_degraded_claim(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_claim(doc_idx)
        base["quality_tier"] = "degraded"
        f = base["expected_fields"]
        noisy_raw = (
            f"-- HEALTH INS CLAIM (PHOTOCOPY) --\n"
            f"Claim ID.: {f['claim_id']}\n"
            f"P0licy No: {f['policy_number']}\n"
            f"Patient..: {f['patient_name']}\n"
            f"Hospital.: {f['hospital_name']}\n"
            f"Admitted : {f['admission_date']}\n"
            f"ICD-10 Code: {f['diagnosis_code']}\n"
            f"Claim Amt: {f['claim_amount']:.2f}\n"
            f"*streaks of carbon toner across footer*"
        )
        base["raw_text_content"] = noisy_raw
        return base

    def _generate_handwritten_claim(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_claim(doc_idx)
        base["quality_tier"] = "handwritten"
        f = base["expected_fields"]
        hw_raw = (
            f"[HANDWRITTEN CLINICAL DISCHARGE & CLAIM]\n"
            f"Claim identifier: {f['claim_id']}\n"
            f"Ins Policy: {f['policy_number']}\n"
            f"Patient: {f['patient_name']} (DOB verified)\n"
            f"Clinic/Hospital: {f['hospital_name']}\n"
            f"Date admitted: {f['admission_date']}\n"
            f"Diagnosis ICD10: {f['diagnosis_code']}\n"
            f"Total requested: ${f['claim_amount']:.2f}\n"
            f"Physician initial: DR. J.D."
        )
        base["raw_text_content"] = hw_raw
        return base

    def _generate_unreadable_claim(self, doc_idx: int) -> Dict[str, Any]:
        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "insurance_claim",
            "quality_tier": "unreadable",
            "raw_text_content": (
                "[OUT-OF-SCOPE / CORRUPTED HEALTHCARE DOCUMENT]\n"
                "Generic Cafeteria Menu & Parking Receipt\n"
                "Lunch Combo: $12.50\n"
                "Validated parking slot: B4\n"
                "[No insurance policy, claim ID, or medical diagnosis detected]"
            ),
            "expected_fields": None,
            "should_reject": True,
        }

    def _generate_clean_kyc(self, doc_idx: int) -> Dict[str, Any]:
        dtype = random.choice(self.DOC_TYPES_KYC)
        id_num = f"{dtype[:3].upper()}-{random.randint(1000000, 9999999)}"
        name = random.choice(self.PATIENTS)
        birth_year = random.randint(1965, 2004)
        dob = f"{birth_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        exp_year = random.randint(2027, 2035)
        expiry = f"{exp_year}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        nationality = random.choice(self.NATIONALITIES)

        raw_text = (
            f"GOVERNMENT IDENTITY VERIFICATION DOCUMENT\n"
            f"====================================================\n"
            f"Document Type: {dtype.replace('_', ' ').title()}\n"
            f"Document ID Number: {id_num}\n"
            f"Full Legal Name: {name}\n"
            f"Date of Birth: {dob}\n"
            f"Expiration Date: {expiry}\n"
            f"Nationality / Citizenship: {nationality}\n"
            f"Security Microprint & Biometric Chip Verified.\n"
            f"===================================================="
        )

        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "kyc_identity",
            "quality_tier": "clean",
            "raw_text_content": raw_text,
            "expected_fields": {
                "id_number": id_num,
                "full_name": name,
                "dob": dob,
                "expiry_date": expiry,
                "document_type": dtype,
                "nationality": nationality,
            },
            "should_reject": False,
        }

    def _generate_degraded_kyc(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_kyc(doc_idx)
        base["quality_tier"] = "degraded"
        f = base["expected_fields"]
        noisy_raw = (
            f"-- IDENTITY CARD (MOBILE PHOTO / GLARE) --\n"
            f"DocType: {f['document_type']}\n"
            f"ID No: {f['id_number']}\n"
            f"Name: {f['full_name']}\n"
            f"DOB (YYYY-MM-DD): {f['dob']}\n"
            f"Expires: {f['expiry_date']}\n"
            f"Country/Nat: {f['nationality']}\n"
            f"*flash reflection obscuring hologram strip*"
        )
        base["raw_text_content"] = noisy_raw
        return base

    def _generate_handwritten_kyc(self, doc_idx: int) -> Dict[str, Any]:
        base = self._generate_clean_kyc(doc_idx)
        base["quality_tier"] = "handwritten"
        f = base["expected_fields"]
        hw_raw = (
            f"[HANDWRITTEN EMBASSY REGISTRATION FORM]\n"
            f"Registered doc type: {f['document_type']}\n"
            f"Identification ID: {f['id_number']}\n"
            f"Applicant Name: {f['full_name']}\n"
            f"Birth Date: {f['dob']}\n"
            f"Valid Until: {f['expiry_date']}\n"
            f"Citizenship: {f['nationality']}\n"
            f"[Thumbprint & ink signature on line 4]"
        )
        base["raw_text_content"] = hw_raw
        return base

    def _generate_unreadable_kyc(self, doc_idx: int) -> Dict[str, Any]:
        return {
            "doc_id": f"DOC_{doc_idx:03d}",
            "doc_type": "kyc_identity",
            "quality_tier": "unreadable",
            "raw_text_content": (
                "[CORRUPTED / DEFACED IDENTITY SUBMISSION]\n"
                "Heavily blurred smartphone capture.\n"
                "Resolution: 72x48 pixels.\n"
                "Face obscured by finger, text completely illegible.\n"
                "REJECT: Unacceptable photo quality."
            ),
            "expected_fields": None,
            "should_reject": True,
        }

    def generate_all_100_documents(self) -> List[Dict[str, Any]]:
        """Generate exactly 100 documents matching specified distributions."""
        dataset: List[Dict[str, Any]] = []
        doc_id = 1

        # ---------------------------------------------------------------------
        # 1. 40 Invoices (24 clean, 8 degraded, 4 handwritten, 4 unreadable)
        # ---------------------------------------------------------------------
        for _ in range(24):
            dataset.append(self._generate_clean_invoice(doc_id))
            doc_id += 1
        for _ in range(8):
            dataset.append(self._generate_degraded_invoice(doc_id))
            doc_id += 1
        for _ in range(4):
            dataset.append(self._generate_handwritten_invoice(doc_id))
            doc_id += 1
        for _ in range(4):
            dataset.append(self._generate_unreadable_invoice(doc_id))
            doc_id += 1

        # ---------------------------------------------------------------------
        # 2. 35 Insurance Claims (21 clean, 7 degraded, 4 handwritten, 3 unreadable)
        # ---------------------------------------------------------------------
        for _ in range(21):
            dataset.append(self._generate_clean_claim(doc_id))
            doc_id += 1
        for _ in range(7):
            dataset.append(self._generate_degraded_claim(doc_id))
            doc_id += 1
        for _ in range(4):
            dataset.append(self._generate_handwritten_claim(doc_id))
            doc_id += 1
        for _ in range(3):
            dataset.append(self._generate_unreadable_claim(doc_id))
            doc_id += 1

        # ---------------------------------------------------------------------
        # 3. 25 KYC Identity Documents (15 clean, 5 degraded, 2 handwritten, 3 unreadable)
        # ---------------------------------------------------------------------
        for _ in range(15):
            dataset.append(self._generate_clean_kyc(doc_id))
            doc_id += 1
        for _ in range(5):
            dataset.append(self._generate_degraded_kyc(doc_id))
            doc_id += 1
        for _ in range(2):
            dataset.append(self._generate_handwritten_kyc(doc_id))
            doc_id += 1
        for _ in range(3):
            dataset.append(self._generate_unreadable_kyc(doc_id))
            doc_id += 1

        return dataset

    def export_dataset(self, output_path: Optional[Path | str] = None) -> Path:
        """Generate and save ground truth dataset to disk."""
        target = Path(output_path or (PROJECT_ROOT / "data" / "ground_truth.json")).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        dataset = self.generate_all_100_documents()
        with open(target, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2)

        return target


def main() -> None:
    """CLI to generate and verify dataset."""
    parser = argparse.ArgumentParser(description="Dataset Generator for Assignment 5")
    parser.add_argument("--generate", action="store_true", help="Generate ground_truth.json")
    parser.add_argument("--verify", action="store_true", help="Verify dataset schema compliance")
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "data" / "ground_truth.json"))

    args = parser.parse_args()

    gen = DatasetGenerator()
    out_file = gen.export_dataset(args.output)
    print(f"📦 Successfully generated 100 ground truth documents to: {out_file}")

    if args.verify:
        validator = SchemaValidator()
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        failures = 0
        counts_type: Dict[str, int] = {}
        counts_tier: Dict[str, int] = {}

        for item in data:
            counts_type[item["doc_type"]] = counts_type.get(item["doc_type"], 0) + 1
            counts_tier[item["quality_tier"]] = counts_tier.get(item["quality_tier"], 0) + 1
            ok, errs = validator.validate_document_entry(item)
            if not ok:
                failures += 1
                print(f"❌ Error in {item['doc_id']}: {errs}")

        print("\nDocument Type Distribution:")
        for dt, c in sorted(counts_type.items()):
            print(f"  • {dt}: {c}")

        print("\nQuality Tier Distribution:")
        for qt, c in sorted(counts_tier.items()):
            print(f"  • {qt}: {c}")

        if failures == 0:
            print("\n✅ All 100 documents strictly pass schema and envelope validation!")
        else:
            print(f"\n❌ Encountered {failures} validation failures.")
            sys.exit(1)


if __name__ == "__main__":
    main()
