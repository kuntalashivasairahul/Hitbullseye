"""Self-contained test suite for Task 03: Sliding Window Rate Limiter."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_03_algo_sliding_window import SlidingWindowRateLimiter


class TestTask03SlidingWindow(unittest.TestCase):
    """Tests for Task 3: High-Throughput Rate Limiting Sliding Window."""

    def setUp(self):
        self.limiter = SlidingWindowRateLimiter()

    def test_rate_limit_allow_and_block(self):
        """Verify requests allowed up to max_requests and blocked when exceeded."""
        key = "client_ip_1"
        t0 = 1000.0

        # Allow 3 requests in a 10s window
        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 2)

        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 1)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)

        allowed, remaining, _ = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 2)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 0)

        # 4th request at t0 + 3 should be blocked
        allowed, remaining, retry_after = self.limiter.is_allowed(key, max_requests=3, window_seconds=10.0, current_time=t0 + 3)
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertAlmostEqual(retry_after, 7.0, places=2)

    def test_sliding_window_continuous_slide(self):
        """Verify window slides continuously freeing capacity as old requests expire."""
        key = "client_ip_2"
        t0 = 2000.0
        self.limiter.is_allowed(key, 2, 5.0, current_time=t0)
        self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 1.0)

        # Blocked at t0 + 2
        allowed, _, _ = self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 2.0)
        self.assertFalse(allowed)

        # At t0 + 5.1, the first request at t0 has expired!
        allowed, remaining, _ = self.limiter.is_allowed(key, 2, 5.0, current_time=t0 + 5.1)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 0)

    def test_cleanup_expired(self):
        """Verify cleanup_expired removes idle client keys."""
        self.limiter.is_allowed("old_client", 5, 10.0, current_time=100.0)
        self.limiter.is_allowed("new_client", 5, 10.0, current_time=500.0)

        evicted = self.limiter.cleanup_expired(older_than_seconds=200.0, current_time=500.0)
        self.assertEqual(evicted, 1)
        self.assertNotIn("old_client", self.limiter._store)
        self.assertIn("new_client", self.limiter._store)


if __name__ == "__main__":
    unittest.main()
