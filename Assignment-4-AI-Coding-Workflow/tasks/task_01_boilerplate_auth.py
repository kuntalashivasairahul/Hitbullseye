"""Task 1: Boilerplate - JWT Authentication Token Handler.

Implements HMAC-SHA256 JWT generation, verification, and token refresh
with strict protection against timing attacks, weak keys, and algorithm tampering.
"""

from __future__ import annotations

import base64
import hmac
import hashlib
import json
import time
from typing import Any, Dict, List


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class TokenExpiredError(AuthError):
    """Raised when a token timestamp has passed expiration."""
    pass


class InvalidSignatureError(AuthError):
    """Raised when token signature does not match secret key or payload was tampered."""
    pass


class MalformedTokenError(AuthError):
    """Raised when token format violates header.payload.signature structure."""
    pass


class JWTAuthHandler:
    """Cryptographic JWT token generator and validator."""

    def __init__(self, secret_key: str):
        if not secret_key or len(secret_key) < 16:
            raise ValueError("Secret key must be at least 16 characters long.")
        self.secret_key = secret_key.encode("utf-8")

    @staticmethod
    def _b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    @staticmethod
    def _b64_decode(data_str: str) -> bytes:
        padding = "=" * ((4 - len(data_str) % 4) % 4)
        return base64.urlsafe_b64decode((data_str + padding).encode("utf-8"))

    def _create_signature(self, signing_input: str) -> str:
        sig = hmac.new(self.secret_key, signing_input.encode("utf-8"), hashlib.sha256).digest()
        return self._b64_encode(sig)

    def generate_token(
        self,
        user_id: str,
        roles: List[str],
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate an HMAC-SHA256 signed JWT token."""
        if not user_id:
            raise ValueError("user_id must be a non-empty string.")

        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(user_id),
            "roles": list(roles),
            "iat": now,
            "exp": now + expires_in_seconds,
        }

        header_b64 = self._b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}"
        signature_b64 = self._create_signature(signing_input)

        return f"{signing_input}.{signature_b64}"

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token, enforcing signature, alg, and expiration."""
        if not token or not isinstance(token, str):
            raise MalformedTokenError("Token must be a non-empty string.")

        parts = token.split(".")
        if len(parts) != 3:
            raise MalformedTokenError(f"Token must have exactly 3 parts separated by dots, got {len(parts)}")

        header_b64, payload_b64, signature_b64 = parts

        try:
            header = json.loads(self._b64_decode(header_b64).decode("utf-8"))
            payload = json.loads(self._b64_decode(payload_b64).decode("utf-8"))
        except Exception as e:
            raise MalformedTokenError(f"Failed to decode token headers or claims: {e}")

        # Protect against alg: none attack
        if header.get("alg") != "HS256":
            raise InvalidSignatureError(f"Unsupported or dangerous algorithm: {header.get('alg')}")

        # Timing-safe signature check
        signing_input = f"{header_b64}.{payload_b64}"
        expected_signature = self._create_signature(signing_input)
        if not hmac.compare_digest(signature_b64, expected_signature):
            raise InvalidSignatureError("Signature mismatch or token tampered.")

        # Expiration check
        exp = payload.get("exp")
        if exp is None or not isinstance(exp, (int, float)):
            raise MalformedTokenError("Missing or invalid 'exp' expiration claim.")

        if time.time() >= exp:
            raise TokenExpiredError("Token has expired.")

        return payload

    def refresh_token(self, token: str, extension_seconds: int = 3600) -> str:
        """Issue a refreshed token preserving claims with a new expiration."""
        claims = self.verify_token(token)
        return self.generate_token(
            user_id=claims["sub"],
            roles=claims.get("roles", []),
            expires_in_seconds=extension_seconds,
        )
