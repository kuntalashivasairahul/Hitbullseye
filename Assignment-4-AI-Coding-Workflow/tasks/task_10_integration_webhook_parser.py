"""Task 10: Integration - Webhook HMAC Verifier & Replay Guard.

Implements secure cryptographic webhook ingestion with HMAC-SHA256 signatures,
replay attack timestamp tolerance windows, and dynamic event dispatching.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Callable, Dict, Optional


class WebhookDispatcher:
    """Cryptographic webhook parser, verifier, and event dispatcher."""

    STATUS_SUCCESS = "SUCCESS"
    STATUS_INVALID_SIGNATURE = "INVALID_SIGNATURE"
    STATUS_EXPIRED_TIMESTAMP = "EXPIRED_TIMESTAMP"
    STATUS_HANDLER_ERROR = "HANDLER_ERROR"
    STATUS_UNREGISTERED_EVENT = "UNREGISTERED_EVENT"

    def __init__(self, secret_key: str, max_drift_seconds: float = 300.0):
        if not secret_key:
            raise ValueError("secret_key must be a non-empty string.")
        self.secret_key = secret_key.encode("utf-8")
        self.max_drift_seconds = float(max_drift_seconds)
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        """Register an event callback for a specific event_type."""
        self._handlers[event_type] = handler

    def compute_signature(self, payload: bytes, timestamp_str: str) -> str:
        """Compute expected HMAC-SHA256 signature hex digest."""
        message = f"{timestamp_str}.".encode("utf-8") + payload
        return hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

    def verify_signature(
        self,
        payload: bytes,
        signature_header: str,
        timestamp_header: str,
        current_time: Optional[float] = None,
    ) -> bool:
        """Verify HMAC-SHA256 signature and timestamp freshness."""
        now = time.time() if current_time is None else float(current_time)

        # 1. Timestamp Freshness / Replay Check
        try:
            ts = float(timestamp_header)
        except (ValueError, TypeError):
            return False

        if abs(now - ts) > self.max_drift_seconds:
            return False

        # 2. Signature verification
        expected = self.compute_signature(payload, timestamp_header)
        return hmac.compare_digest(signature_header.strip(), expected)

    def dispatch(
        self,
        payload: bytes,
        signature_header: str,
        timestamp_header: str,
        current_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Verify headers, parse JSON payload, and dispatch event to registered handler."""
        now = time.time() if current_time is None else float(current_time)

        # Check timestamp drift
        try:
            ts = float(timestamp_header)
            if abs(now - ts) > self.max_drift_seconds:
                return {
                    "status": self.STATUS_EXPIRED_TIMESTAMP,
                    "error": f"Timestamp drift ({abs(now - ts):.1f}s) exceeded limit of {self.max_drift_seconds}s",
                    "result": None,
                }
        except (ValueError, TypeError) as e:
            return {
                "status": self.STATUS_EXPIRED_TIMESTAMP,
                "error": f"Invalid timestamp header: {e}",
                "result": None,
            }

        # Check signature
        expected = self.compute_signature(payload, timestamp_header)
        if not hmac.compare_digest(signature_header.strip(), expected):
            return {
                "status": self.STATUS_INVALID_SIGNATURE,
                "error": "Signature mismatch or tampered payload.",
                "result": None,
            }

        # Parse JSON
        try:
            data = json.loads(payload.decode("utf-8"))
        except Exception as e:
            return {
                "status": self.STATUS_HANDLER_ERROR,
                "error": f"Failed to parse payload as JSON: {e}",
                "result": None,
            }

        event_type = data.get("event") or data.get("type") or "default"

        if event_type not in self._handlers:
            return {
                "status": self.STATUS_UNREGISTERED_EVENT,
                "event_type": event_type,
                "data": data,
                "result": None,
            }

        # Dispatch
        try:
            handler = self._handlers[event_type]
            res = handler(data)
            return {
                "status": self.STATUS_SUCCESS,
                "event_type": event_type,
                "data": data,
                "result": res,
            }
        except Exception as e:
            return {
                "status": self.STATUS_HANDLER_ERROR,
                "event_type": event_type,
                "error": str(e),
                "result": None,
            }
