"""Self-contained test suite for Task 10: Webhook HMAC Verifier & Replay Guard."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_10_integration_webhook_parser import WebhookDispatcher


class TestTask10WebhookParser(unittest.TestCase):
    """Tests for Task 10: Webhook HMAC Verifier & Replay Guard."""

    def setUp(self):
        self.secret = "whsec_super_secret_signing_key_456"
        self.dispatcher = WebhookDispatcher(self.secret, max_drift_seconds=300.0)

    def test_valid_webhook_dispatch(self):
        """Verify valid signature within drift window executes handler."""
        payload = b'{"event": "payment.succeeded", "amount": 1500}'
        ts_str = str(time.time())
        sig = self.dispatcher.compute_signature(payload, ts_str)

        handler_called = False

        def on_payment(data: dict):
            nonlocal handler_called
            handler_called = True
            return "processed_successfully"

        self.dispatcher.register_handler("payment.succeeded", on_payment)
        res = self.dispatcher.dispatch(payload, signature_header=sig, timestamp_header=ts_str)

        self.assertEqual(res["status"], WebhookDispatcher.STATUS_SUCCESS)
        self.assertTrue(handler_called)
        self.assertEqual(res["result"], "processed_successfully")

    def test_expired_timestamp_replay_rejection(self):
        """Verify webhook timestamp older than 300s is rejected as expired replay."""
        payload = b'{"event": "order.cancelled"}'
        old_ts = str(time.time() - 400.0)
        sig = self.dispatcher.compute_signature(payload, old_ts)

        res = self.dispatcher.dispatch(payload, signature_header=sig, timestamp_header=old_ts)
        self.assertEqual(res["status"], WebhookDispatcher.STATUS_EXPIRED_TIMESTAMP)
        self.assertIn("drift", res["error"])

    def test_tampered_payload_rejected(self):
        """Verify altered payload fails signature check."""
        payload = b'{"event": "account.compromised"}'
        ts_str = str(time.time())
        sig = self.dispatcher.compute_signature(payload, ts_str)

        tampered_payload = b'{"event": "account.compromised", "admin": true}'
        res = self.dispatcher.dispatch(tampered_payload, signature_header=sig, timestamp_header=ts_str)
        self.assertEqual(res["status"], WebhookDispatcher.STATUS_INVALID_SIGNATURE)


if __name__ == "__main__":
    unittest.main()
