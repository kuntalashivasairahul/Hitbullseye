"""Schema Validation Engine for Document Extraction (Assignment 5).

Provides schema parsing, type checking, range validation, regex pattern matching,
and ISO 8601 date verification for extracted documents.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SchemaValidator:
    """Rigorous schema validation engine for document extraction pipelines."""

    SCHEMA_FILES = {
        "invoice": "invoice_schema.json",
        "insurance_claim": "insurance_claim_schema.json",
        "kyc_identity": "kyc_identity_schema.json",
    }

    def __init__(self, schemas_dir: Optional[Path | str] = None):
        self.schemas_dir = Path(schemas_dir or (PROJECT_ROOT / "data" / "schemas")).resolve()
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load and cache JSON schemas from directory."""
        if not self.schemas_dir.exists():
            raise FileNotFoundError(f"Schemas directory not found: {self.schemas_dir}")

        for doc_type, filename in self.SCHEMA_FILES.items():
            filepath = self.schemas_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Schema file missing: {filepath}")
            with open(filepath, "r", encoding="utf-8") as f:
                schema_dict = json.load(f)
                self.schemas[doc_type] = schema_dict

    def _get_pattern(self, pattern_str: str) -> re.Pattern:
        if pattern_str not in self._compiled_patterns:
            self._compiled_patterns[pattern_str] = re.compile(pattern_str)
        return self._compiled_patterns[pattern_str]

    @staticmethod
    def _validate_iso_date(date_str: str) -> bool:
        """Verify strict ISO 8601 YYYY-MM-DD calendar date with leap year awareness."""
        if not isinstance(date_str, str) or len(date_str) != 10:
            return False
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            # Verify no format truncation / normalization mismatch
            return parsed.strftime("%Y-%m-%d") == date_str
        except ValueError:
            return False

    def validate(self, doc_type: str, data: Optional[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate extracted fields dictionary against target document schema.

        Returns:
            Tuple of (is_valid: bool, errors: List[str])
        """
        doc_type_clean = doc_type.strip().lower()
        if doc_type_clean not in self.schemas:
            return False, [f"Unknown document type '{doc_type}'. Registered: {list(self.schemas.keys())}"]

        if data is None or not isinstance(data, dict):
            return False, ["Data payload must be a non-null dictionary object."]

        schema = self.schemas[doc_type_clean]
        properties: Dict[str, Any] = schema.get("properties", {})
        required: List[str] = schema.get("required", [])
        additional_allowed: bool = schema.get("additionalProperties", True)

        errors: List[str] = []

        # 1. Additional properties check
        if not additional_allowed:
            for key in data.keys():
                if key not in properties:
                    errors.append(f"Unexpected extra field '{key}' not permitted by schema.")

        # 2. Required fields check
        for req in required:
            if req not in data:
                errors.append(f"Missing required field: '{req}'")

        # 3. Property constraint validations
        for field_name, val in data.items():
            if field_name not in properties:
                continue

            field_spec = properties[field_name]
            field_errors = self._validate_field(field_name, field_spec, val)
            errors.extend(field_errors)

        return len(errors) == 0, errors

    def _validate_field(self, field_name: str, spec: Dict[str, Any], val: Any) -> List[str]:
        """Validate an individual field against type, range, pattern, and enum rules."""
        errors: List[str] = []
        expected_type = spec.get("type")

        # Handle nullable type union: e.g. ["string", "null"]
        if isinstance(expected_type, list):
            if val is None:
                if "null" in expected_type:
                    return []
                else:
                    return [f"Field '{field_name}' cannot be null."]
        elif val is None:
            if expected_type == "null":
                return []
            return [f"Field '{field_name}' cannot be null (expected {expected_type})."]

        # Type checking (prevent bool from passing as int)
        if isinstance(val, bool) and expected_type in ("number", "integer"):
            return [f"Field '{field_name}' must be a {expected_type}, got boolean."]

        if expected_type == "string" or (isinstance(expected_type, list) and "string" in expected_type):
            if not isinstance(val, str):
                return [f"Field '{field_name}' must be a string, got {type(val).__name__}."]

            if "minLength" in spec and len(val) < spec["minLength"]:
                errors.append(f"Field '{field_name}' length {len(val)} is below minimum {spec['minLength']}.")
            if "maxLength" in spec and len(val) > spec["maxLength"]:
                errors.append(f"Field '{field_name}' length {len(val)} exceeds maximum {spec['maxLength']}.")

            if "pattern" in spec:
                pattern = self._get_pattern(spec["pattern"])
                if not pattern.match(val):
                    errors.append(f"Field '{field_name}' value '{val}' does not match pattern '{spec['pattern']}'.")

            if "enum" in spec and val not in spec["enum"]:
                errors.append(f"Field '{field_name}' value '{val}' is not in allowed values: {spec['enum']}.")

            # Date check if pattern implies YYYY-MM-DD
            if spec.get("pattern") == "^\\d{4}-\\d{2}-\\d{2}$" or "date" in field_name:
                if not self._validate_iso_date(val):
                    errors.append(f"Field '{field_name}' value '{val}' is not a valid ISO 8601 calendar date.")

        elif expected_type == "number":
            if not isinstance(val, (int, float)):
                return [f"Field '{field_name}' must be a number, got {type(val).__name__}."]
            if "minimum" in spec and val < spec["minimum"]:
                errors.append(f"Field '{field_name}' value {val} is below minimum {spec['minimum']}.")
            if "maximum" in spec and val > spec["maximum"]:
                errors.append(f"Field '{field_name}' value {val} exceeds maximum {spec['maximum']}.")

        elif expected_type == "integer":
            if not isinstance(val, int):
                return [f"Field '{field_name}' must be an integer, got {type(val).__name__}."]
            if "minimum" in spec and val < spec["minimum"]:
                errors.append(f"Field '{field_name}' value {val} is below minimum {spec['minimum']}.")
            if "maximum" in spec and val > spec["maximum"]:
                errors.append(f"Field '{field_name}' value {val} exceeds maximum {spec['maximum']}.")

        return errors

    def validate_document_entry(self, entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate ground truth record envelope and payload."""
        required_envelope = ["doc_id", "doc_type", "quality_tier", "raw_text_content", "expected_fields", "should_reject"]
        errors = []

        for req in required_envelope:
            if req not in entry:
                errors.append(f"Missing envelope property '{req}'.")

        if errors:
            return False, errors

        doc_type = entry["doc_type"]
        tier = entry["quality_tier"]
        valid_tiers = {"clean", "degraded", "handwritten", "unreadable"}
        if tier not in valid_tiers:
            errors.append(f"Invalid quality tier '{tier}'. Expected one of {valid_tiers}.")

        should_reject = entry["should_reject"]

        if should_reject:
            # Corrupted / unreadable document
            return len(errors) == 0, errors
        else:
            # Non-rejected documents must satisfy strict schema
            fields = entry.get("expected_fields")
            is_valid, field_errs = self.validate(doc_type, fields)
            if not is_valid:
                errors.extend([f"[{entry['doc_id']}] {e}" for e in field_errs])

        return len(errors) == 0, errors


def main() -> None:
    """CLI to inspect and validate schemas."""
    parser = argparse.ArgumentParser(description="Schema Validator CLI for Assignment 5")
    parser.add_argument("--validate-all", action="store_true", help="Validate all schemas and ground truth dataset.")
    parser.add_argument("--doc-type", type=str, help="Document type to validate sample against.")
    parser.add_argument("--file", type=str, help="JSON file containing extracted document fields to validate.")

    args = parser.parse_args()
    validator = SchemaValidator()

    if args.validate_all:
        gt_file = PROJECT_ROOT / "data" / "ground_truth.json"
        print(f"🔍 Loaded schemas: {list(validator.schemas.keys())}")
        if gt_file.exists():
            print(f"📄 Validating ground truth dataset at: {gt_file}")
            with open(gt_file, "r", encoding="utf-8") as f:
                dataset = json.load(f)
            total = len(dataset)
            failures = 0
            for item in dataset:
                ok, errs = validator.validate_document_entry(item)
                if not ok:
                    failures += 1
                    print(f"❌ Failure in {item.get('doc_id')}: {errs}")
            if failures == 0:
                print(f"✅ All {total} ground truth documents strictly valid!")
            else:
                print(f"❌ {failures}/{total} documents failed validation.")
                sys.exit(1)
        else:
            print("ℹ️  ground_truth.json not yet generated. Run dataset_generator.py first.")
        return

    if args.doc_type and args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        ok, errs = validator.validate(args.doc_type, sample_data)
        if ok:
            print(f"✅ Data satisfies schema for '{args.doc_type}'.")
        else:
            print(f"❌ Validation failed ({len(errs)} errors):")
            for e in errs:
                print(f"   • {e}")
            sys.exit(1)
    else:
        print("Registered schemas:")
        for name, s in validator.schemas.items():
            print(f"  • {name}: {s.get('title')} ({len(s.get('required', []))} required fields)")


if __name__ == "__main__":
    main()
