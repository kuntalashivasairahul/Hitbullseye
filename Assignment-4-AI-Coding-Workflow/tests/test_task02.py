"""Self-contained test suite for Task 02: REST API CRUD Serializer & Validator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_02_boilerplate_crud import UserRecordSerializer, ValidationError


class TestTask02Crud(unittest.TestCase):
    """Tests for Task 2: REST API CRUD Serializer & Validator."""

    def test_valid_user_serialization(self):
        """Verify valid user payload serializes to clean JSON."""
        data = {
            "username": "alex_smith",
            "email": "alex.smith@company.org",
            "role": "admin",
            "is_active": True,
        }
        json_str = UserRecordSerializer.serialize(data)
        deserialized = UserRecordSerializer.deserialize(json_str)
        self.assertEqual(deserialized["username"], "alex_smith")
        self.assertEqual(deserialized["email"], "alex.smith@company.org")
        self.assertEqual(deserialized["role"], "admin")
        self.assertIn("id", deserialized)
        self.assertIn("created_at", deserialized)

    def test_invalid_fields_raise_validation_error(self):
        """Verify invalid username, email, and roles raise field-specific errors."""
        bad_data = {
            "username": "a!",  # Too short, invalid symbol
            "email": "not-an-email",
            "role": "super_god_mode",  # Disallowed role
        }
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.validate(bad_data)
        errors = ctx.exception.errors
        self.assertIn("username", errors)
        self.assertIn("email", errors)
        self.assertIn("role", errors)

    def test_partial_update_immutable_fields(self):
        """Verify attempting to modify 'id' or 'created_at' raises ValidationError."""
        existing = {
            "id": "11111111-1111-4111-8111-111111111111",
            "username": "original_user",
            "email": "original@domain.com",
            "role": "viewer",
            "created_at": "2026-01-01T00:00:00Z",
        }
        # Legitimate partial update
        updated = UserRecordSerializer.partial_update(existing, {"role": "editor"})
        self.assertEqual(updated["role"], "editor")
        self.assertEqual(updated["id"], existing["id"])

        # Attempt to tamper immutable ID
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.partial_update(existing, {"id": "22222222-2222-4222-8222-222222222222"})
        self.assertIn("id", ctx.exception.errors)

        # Attempt to tamper created_at
        with self.assertRaises(ValidationError) as ctx:
            UserRecordSerializer.partial_update(existing, {"created_at": "2020-01-01T00:00:00Z"})
        self.assertIn("created_at", ctx.exception.errors)


if __name__ == "__main__":
    unittest.main()
