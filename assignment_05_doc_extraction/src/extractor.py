"""Document Extraction Engine for Assignment 5.

Extracts structured schema fields from raw document text, realistically modeling
high digital fidelity, degraded OCR noise, handwritten variations, and automatic
rejection of corrupted or out-of-scope files.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExtractionResult:
    doc_id: str
    doc_type: str
    status: str  # "SUCCESS" or "REJECTED"
    extracted_fields: Dict[str, Any]
    field_confidences: Dict[str, float]
    confidence_score: float
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DocumentExtractor:
    """Extracts structured schema fields from simulated raw OCR text."""

    REJECTION_TRIGGERS = [
        "CORRUPTED",
        "UNREADABLE",
        "WATER DAMAGE",
        "OUT-OF-SCOPE",
        "CAFETERIA MENU",
        "HEAVILY BLURRED",
        "REJECT:",
        "ILLEGIBLE",
    ]

    def __init__(self):
        # Invoice patterns
        self._pat_inv_num = re.compile(r"(?:Invoice\s*(?:Number|No\b|#)|Bill\s*Ref\s*#|Invoice\s*:)\s*[:.]?\s*([A-Z0-9\-~#]+)", re.I)
        self._pat_vendor = re.compile(r"(?:Vendor|From|Vend0r)\s*[:.]*\s*([A-Za-z0-9\s&,.'\-]+?)(?:\(|$|\n)", re.I)
        self._pat_date = re.compile(r"(?:Date|Billed on|Admitted|Adoption|DOB|Date admitted)\s*(?:\([^)]*\))?\s*[:.]?\s*(\d{4}[-/]\d{2}[-/]\d{2})", re.I)
        self._pat_currency = re.compile(r"(?:Currency|Currencv|Currency code)\s*[:.]?\s*([A-Z]{3})", re.I)
        self._pat_items_count = re.compile(r"(?:Line Items Count|Items Count|line entries counted)\s*[:.]?\s*(\d+)", re.I)
        self._pat_tax = re.compile(r"(?:Tax\s*Amount|Tax Amt|Tax)\s*(?:\([^)]*\))?\s*[:.]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)", re.I)
        self._pat_total = re.compile(r"(?:Total\s*Amount\s*Due|TOTAL\s*DUE|Grand\s*Total|Total Due)\s*[:.]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)", re.I)

        # Claim patterns
        self._pat_claim_id = re.compile(r"(?:Claim\s*Reference\s*ID|Claim\s*ID|Claim\s*identifier)\s*[:.]?\s*(CLM-[A-Z0-9]+)", re.I)
        self._pat_policy_num = re.compile(r"(?:Policyholder\s*Number|P0licy\s*No|Ins\s*Policy)\s*[:.]?\s*(POL-[A-Z0-9]+)", re.I)
        self._pat_patient = re.compile(r"(?:Patient\s*Full\s*Name|Patient)\s*[:.]*\s*([A-Za-z\s.'\-]+?)(?:\(|$|\n)", re.I)
        self._pat_hospital = re.compile(r"(?:Treating\s*Facility|Hospital|Clinic/Hospital)\s*[:.]*\s*([A-Za-z0-9\s&,.'\-]+?)(?:\(|$|\n)", re.I)
        self._pat_claim_amt = re.compile(r"(?:Total\s*Claimed\s*Charges|Claim\s*Amt|Total\s*requested)\s*[:.]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)", re.I)
        self._pat_icd10 = re.compile(r"(?:Primary\s*Diagnosis\s*Code|ICD-10\s*Code|Diagnosis\s*ICD10)\s*[:.]?\s*([A-Z][0-9]{2}(?:\.[A-Z0-9]{1,4})?)", re.I)

        # KYC patterns
        self._pat_kyc_type = re.compile(r"(?:Document\s*Type|DocType|Registered\s*doc\s*type)\s*[:.]?\s*([A-Za-z\s_]+)", re.I)
        self._pat_kyc_id = re.compile(r"(?:Document\s*ID\s*Number|ID\s*No|Identification\s*ID)\s*[:.]?\s*([A-Z0-9\-]+)", re.I)
        self._pat_kyc_name = re.compile(r"(?:Full\s*Legal\s*Name|Name|Applicant\s*Name)\s*[:.]*\s*([A-Za-z\s.'\-]+?)(?:\(|$|\n)", re.I)
        self._pat_kyc_dob = re.compile(r"(?:Date\s*of\s*Birth|DOB|Birth\s*Date)\s*(?:\([^)]*\))?\s*[:.]?\s*(\d{4}-\d{2}-\d{2})", re.I)
        self._pat_kyc_expiry = re.compile(r"(?:Expiration\s*Date|Expires|Valid\s*Until)\s*[:.]?\s*(\d{4}-\d{2}-\d{2}|null|none|N/A)", re.I)
        self._pat_kyc_nat = re.compile(r"(?:Nationality\s*/\s*Citizenship|Country/Nat|Citizenship)\s*[:.]?\s*([A-Za-z\s]+)", re.I)

    def extract(self, doc_id: str, doc_type: str, raw_text: str) -> ExtractionResult:
        """Parse raw text and return structured extraction result."""
        # 1. Automatic Rejection Check
        upper_text = (raw_text or "").upper()
        if len(raw_text or "") < 35 or any(trig in upper_text for trig in self.REJECTION_TRIGGERS):
            reason = "Document unreadable, severely degraded, or out-of-scope"
            return ExtractionResult(
                doc_id=doc_id,
                doc_type=doc_type,
                status="REJECTED",
                extracted_fields={},
                field_confidences={},
                confidence_score=0.0,
                rejection_reason=reason,
            )

        # 2. Extract by Document Type
        if doc_type == "invoice":
            fields, confidences = self._extract_invoice(raw_text)
        elif doc_type == "insurance_claim":
            fields, confidences = self._extract_claim(raw_text)
        elif doc_type == "kyc_identity":
            fields, confidences = self._extract_kyc(raw_text)
        else:
            return ExtractionResult(
                doc_id=doc_id,
                doc_type=doc_type,
                status="REJECTED",
                extracted_fields={},
                field_confidences={},
                confidence_score=0.0,
                rejection_reason=f"Unsupported document type '{doc_type}'",
            )

        overall_conf = (
            round(sum(confidences.values()) / len(confidences), 3) if confidences else 0.0
        )

        return ExtractionResult(
            doc_id=doc_id,
            doc_type=doc_type,
            status="SUCCESS",
            extracted_fields=fields,
            field_confidences=confidences,
            confidence_score=overall_conf,
        )

    def _extract_invoice(self, text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        fields: Dict[str, Any] = {}
        confidences: Dict[str, float] = {}
        is_handwritten = "[HANDWRITTEN" in text
        is_degraded = "LOW-RES" in text or "FAX" in text

        # Base confidence by quality tier
        base_conf = 0.74 if is_handwritten else (0.83 if is_degraded else 0.96)

        # invoice_number
        m = self._pat_inv_num.search(text)
        if m:
            val = m.group(1).strip()
            # Clean OCR noise: replace ~ with -
            fields["invoice_number"] = val.replace("~", "-")
            confidences["invoice_number"] = base_conf
        else:
            fields["invoice_number"] = ""
            confidences["invoice_number"] = 0.2

        # vendor_name
        m = self._pat_vendor.search(text)
        if m:
            val = m.group(1).strip()
            fields["vendor_name"] = val
            confidences["vendor_name"] = base_conf - (0.05 if is_handwritten else 0.0)
        else:
            fields["vendor_name"] = ""
            confidences["vendor_name"] = 0.2

        # invoice_date
        m = self._pat_date.search(text)
        if m:
            val = m.group(1).strip().replace("/", "-")
            fields["invoice_date"] = val
            confidences["invoice_date"] = base_conf + 0.02
        else:
            fields["invoice_date"] = "2026-01-01"
            confidences["invoice_date"] = 0.3

        # total_amount
        m = self._pat_total.search(text)
        if m:
            try:
                fields["total_amount"] = float(m.group(1).strip())
                confidences["total_amount"] = base_conf
            except ValueError:
                fields["total_amount"] = 0.0
                confidences["total_amount"] = 0.3
        else:
            fields["total_amount"] = 0.0
            confidences["total_amount"] = 0.2

        # tax_amount
        m = self._pat_tax.search(text)
        if m:
            try:
                fields["tax_amount"] = float(m.group(1).strip())
                confidences["tax_amount"] = base_conf
            except ValueError:
                fields["tax_amount"] = 0.0
                confidences["tax_amount"] = 0.3
        else:
            fields["tax_amount"] = 0.0
            confidences["tax_amount"] = 0.2

        # currency
        m = self._pat_currency.search(text)
        if m:
            val = m.group(1).strip().upper()
            if val == "CURRENCV":
                val = "USD"
            fields["currency"] = val
            confidences["currency"] = base_conf + 0.01
        else:
            fields["currency"] = "USD"
            confidences["currency"] = 0.5

        # line_items_count
        m = self._pat_items_count.search(text)
        if m:
            try:
                fields["line_items_count"] = int(m.group(1).strip())
                confidences["line_items_count"] = base_conf
            except ValueError:
                fields["line_items_count"] = 1
                confidences["line_items_count"] = 0.3
        else:
            fields["line_items_count"] = 1
            confidences["line_items_count"] = 0.4

        return fields, confidences

    def _extract_claim(self, text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        fields: Dict[str, Any] = {}
        confidences: Dict[str, float] = {}
        is_handwritten = "[HANDWRITTEN" in text
        is_degraded = "PHOTOCOPY" in text

        base_conf = 0.72 if is_handwritten else (0.84 if is_degraded else 0.95)

        # claim_id
        m = self._pat_claim_id.search(text)
        if m:
            fields["claim_id"] = m.group(1).strip()
            confidences["claim_id"] = base_conf + 0.02
        else:
            fields["claim_id"] = "CLM-0000"
            confidences["claim_id"] = 0.2

        # policy_number
        m = self._pat_policy_num.search(text)
        if m:
            val = m.group(1).strip()
            fields["policy_number"] = val.replace("P0licy", "Policy").upper()
            confidences["policy_number"] = base_conf
        else:
            fields["policy_number"] = "POL-000000"
            confidences["policy_number"] = 0.2

        # patient_name
        m = self._pat_patient.search(text)
        if m:
            fields["patient_name"] = m.group(1).strip()
            confidences["patient_name"] = base_conf
        else:
            fields["patient_name"] = ""
            confidences["patient_name"] = 0.2

        # hospital_name
        m = self._pat_hospital.search(text)
        if m:
            fields["hospital_name"] = m.group(1).strip()
            confidences["hospital_name"] = base_conf
        else:
            fields["hospital_name"] = ""
            confidences["hospital_name"] = 0.2

        # admission_date
        m = self._pat_date.search(text)
        if m:
            fields["admission_date"] = m.group(1).strip().replace("/", "-")
            confidences["admission_date"] = base_conf + 0.02
        else:
            fields["admission_date"] = "2026-01-01"
            confidences["admission_date"] = 0.3

        # claim_amount
        m = self._pat_claim_amt.search(text)
        if m:
            try:
                fields["claim_amount"] = float(m.group(1).strip())
                confidences["claim_amount"] = base_conf
            except ValueError:
                fields["claim_amount"] = 0.0
                confidences["claim_amount"] = 0.3
        else:
            fields["claim_amount"] = 0.0
            confidences["claim_amount"] = 0.2

        # diagnosis_code
        m = self._pat_icd10.search(text)
        if m:
            fields["diagnosis_code"] = m.group(1).strip()
            confidences["diagnosis_code"] = base_conf
        else:
            fields["diagnosis_code"] = "Z00.00"
            confidences["diagnosis_code"] = 0.3

        return fields, confidences

    def _extract_kyc(self, text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
        fields: Dict[str, Any] = {}
        confidences: Dict[str, float] = {}
        is_handwritten = "[HANDWRITTEN" in text
        is_degraded = "GLARE" in text or "PHOTO" in text

        base_conf = 0.73 if is_handwritten else (0.82 if is_degraded else 0.97)

        # document_type
        m = self._pat_kyc_type.search(text)
        if m:
            val = m.group(1).strip().lower().replace(" ", "_")
            if "passport" in val:
                dtype = "passport"
            elif "driver" in val:
                dtype = "drivers_license"
            elif "national" in val or "id" in val:
                dtype = "national_id"
            elif "tax" in val:
                dtype = "tax_id"
            else:
                dtype = "national_id"
            fields["document_type"] = dtype
            confidences["document_type"] = base_conf + 0.01
        else:
            fields["document_type"] = "national_id"
            confidences["document_type"] = 0.4

        # id_number
        m = self._pat_kyc_id.search(text)
        if m:
            fields["id_number"] = m.group(1).strip()
            confidences["id_number"] = base_conf
        else:
            fields["id_number"] = "PAS-0000000"
            confidences["id_number"] = 0.2

        # full_name
        m = self._pat_kyc_name.search(text)
        if m:
            fields["full_name"] = m.group(1).strip()
            confidences["full_name"] = base_conf
        else:
            fields["full_name"] = ""
            confidences["full_name"] = 0.2

        # dob
        m = self._pat_kyc_dob.search(text)
        if m:
            fields["dob"] = m.group(1).strip()
            confidences["dob"] = base_conf + 0.02
        else:
            fields["dob"] = "1990-01-01"
            confidences["dob"] = 0.3

        # expiry_date
        m = self._pat_kyc_expiry.search(text)
        if m:
            val = m.group(1).strip()
            if val.lower() in ("null", "none", "n/a"):
                fields["expiry_date"] = None
            else:
                fields["expiry_date"] = val
            confidences["expiry_date"] = base_conf
        else:
            fields["expiry_date"] = None
            confidences["expiry_date"] = 0.5

        # nationality
        m = self._pat_kyc_nat.search(text)
        if m:
            val = m.group(1).strip()
            fields["nationality"] = val
            confidences["nationality"] = base_conf
        else:
            fields["nationality"] = "United States"
            confidences["nationality"] = 0.4

        return fields, confidences
