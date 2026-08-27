"""Self-contained test suite for Task 01: JWT Authentication Token Handler."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_01_boilerplate_auth import (
    InvalidSignatureError,
    JWTAuthHandler,
    MalformedTokenError,
    TokenExpiredError,
)


class TestTask01Auth(unittest.TestCase):
    """Tests for Task 1: JWT Authentication Token Handler."""

    def setUp(self):
        self.secret = "super_secure_production_secret_key_12345"
        self.handler = JWTAuthHandler(self.secret)

    def test_weak_secret_rejection(self):
        """Ensure secret keys under 16 characters are rejected."""
        with self.assertRaises(ValueError):
            JWTAuthHandler("short_secret")

    def test_valid_token_lifecycle(self):
        """Verify token generation, decoding, and claims verification."""
        token = self.handler.generate_token("user_42", ["admin", "editor"], expires_in_seconds=3600)
        claims = self.handler.verify_token(token)
        self.assertEqual(claims["sub"], "user_42")
        self.assertEqual(claims["roles"], ["admin", "editor"])
        self.assertIn("iat", claims)
        self.assertIn("exp", claims)

    def test_tampered_payload_or_signature_rejected(self):
        """Verify tampering payload triggers InvalidSignatureError."""
        token = self.handler.generate_token("user_42", ["viewer"])
        parts = token.split(".")
        tampered_token = f"{parts[0]}.eyJzdWIiOiAiaGFja2VyIn0.{parts[2]}"
        with self.assertRaises(InvalidSignatureError):
            self.handler.verify_token(tampered_token)

    def test_expired_token_rejected(self):
        """Verify expired token raises TokenExpiredError."""
        token = self.handler.generate_token("user_expired", ["viewer"], expires_in_seconds=-10)
        with self.assertRaises(TokenExpiredError):
            self.handler.verify_token(token)

    def test_malformed_token_rejected(self):
        """Verify malformed tokens without 3 parts raise MalformedTokenError."""
        with self.assertRaises(MalformedTokenError):
            self.handler.verify_token("invalid.token")
        with self.assertRaises(MalformedTokenError):
            self.handler.verify_token("")

    def test_token_refresh(self):
        """Verify refreshed token preserves claims with extended expiration."""
        token = self.handler.generate_token("user_refresh", ["admin"], expires_in_seconds=100)
        refreshed = self.handler.refresh_token(token, extension_seconds=7200)
        claims = self.handler.verify_token(refreshed)
        self.assertEqual(claims["sub"], "user_refresh")
        self.assertEqual(claims["roles"], ["admin"])
        self.assertGreater(claims["exp"], time.time() + 7000)


if __name__ == "__main__":
    unittest.main()
