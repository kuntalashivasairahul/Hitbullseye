"""Task 2: Boilerplate - REST API CRUD Serializer & Validator.

Validates, sanitizes, and serializes user records with immutable ID enforcement,
role constraints, and RFC-compliant email checking.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class ValidationError(Exception):
    """Raised when data payload fails schema or constraint validation."""
    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


class UserRecordSerializer:
    """Validator and serializer for user profile records."""

    ALLOWED_ROLES = {"admin", "editor", "viewer"}
    USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    @classmethod
    def validate(cls, data: Dict[str, Any], is_partial: bool = False) -> Dict[str, Any]:
        """Validate fields against entity constraints."""
        errors: Dict[str, str] = {}
        cleaned: Dict[str, Any] = {}

        # 1. ID check (UUIDv4)
        if "id" in data:
            val = str(data["id"])
            try:
                parsed_uuid = uuid.UUID(val, version=4)
                cleaned["id"] = str(parsed_uuid)
            except ValueError:
                errors["id"] = "Field 'id' must be a valid UUIDv4 string."
        elif not is_partial:
            cleaned["id"] = str(uuid.uuid4())

        # 2. Username check
        if "username" in data:
            uname = str(data["username"]).strip()
            if not cls.USERNAME_REGEX.match(uname):
                errors["username"] = "Username must be 3-30 alphanumeric characters or underscores."
            else:
                cleaned["username"] = uname
        elif not is_partial:
            errors["username"] = "Field 'username' is required."

        # 3. Email check
        if "email" in data:
            email = str(data["email"]).strip()
            if not cls.EMAIL_REGEX.match(email):
                errors["email"] = "Field 'email' must be a valid email address."
            else:
                cleaned["email"] = email.lower()
        elif not is_partial:
            errors["email"] = "Field 'email' is required."

        # 4. Role check
        if "role" in data:
            role = str(data["role"]).strip().lower()
            if role not in cls.ALLOWED_ROLES:
                errors["role"] = f"Role must be one of {sorted(cls.ALLOWED_ROLES)}."
            else:
                cleaned["role"] = role
        elif not is_partial:
            cleaned["role"] = "viewer"

        # 5. is_active check
        if "is_active" in data:
            cleaned["is_active"] = bool(data["is_active"])
        elif not is_partial:
            cleaned["is_active"] = True

        # 6. created_at
        if "created_at" in data:
            cleaned["created_at"] = str(data["created_at"])
        elif not is_partial:
            cleaned["created_at"] = datetime.now(timezone.utc).isoformat()

        if errors:
            raise ValidationError(errors)

        return cleaned

    @classmethod
    def serialize(cls, data: Dict[str, Any]) -> str:
        """Serialize dictionary to JSON string."""
        validated = cls.validate(data)
        return json.dumps(validated, indent=2, sort_keys=True)

    @classmethod
    def deserialize(cls, json_str: str) -> Dict[str, Any]:
        """Deserialize JSON string and validate schema."""
        try:
            parsed = json.loads(json_str)
        except Exception as e:
            raise ValidationError({"_json": f"Invalid JSON payload: {e}"})

        if not isinstance(parsed, dict):
            raise ValidationError({"_json": "JSON payload must be an object."})

        return cls.validate(parsed)

    @classmethod
    def partial_update(cls, existing: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Apply partial update, forbidding modification of immutable fields."""
        immutable_fields = {"id", "created_at"}
        violated = immutable_fields.intersection(updates.keys())
        if violated:
            raise ValidationError({f: f"Field '{f}' is immutable and cannot be updated." for f in violated})

        validated_updates = cls.validate(updates, is_partial=True)
        updated = dict(existing)
        updated.update(validated_updates)
        return updated
