"""Self-contained test suite for Task 08: Thread-Safe In-Memory Cache with RLock."""

from __future__ import annotations

import sys
import threading
import time
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_08_debugging_race_condition import ThreadSafeCache


class TestTask08RaceCondition(unittest.TestCase):
    """Tests for Task 8: Thread-Safe In-Memory Cache with RLock."""

    def test_concurrent_multithreaded_read_write(self):
        """Verify cache integrity under heavy multi-threaded concurrent access."""
        cache = ThreadSafeCache()
        thread_count = 30
        iterations = 50
        errors = []

        def worker(w_id: int):
            try:
                for i in range(iterations):
                    k = f"key_{i % 5}"
                    cache.set(k, f"val_{w_id}_{i}")
                    val = cache.get(k)
                    self.assertIsNotNone(val)
                    if i % 10 == 0:
                        cache.size()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Thread errors encountered: {errors}")

    def test_ttl_expiration(self):
        """Verify expired keys return default and are removed."""
        cache = ThreadSafeCache()
        cache.set("ephemeral", "hello", ttl_seconds=0.05)
        self.assertEqual(cache.get("ephemeral"), "hello")

        time.sleep(0.08)
        self.assertIsNone(cache.get("ephemeral"))
        self.assertEqual(cache.size(), 0)

    def test_get_or_compute_stampede_prevention(self):
        """Verify compute_func is invoked exactly once during concurrent cache misses."""
        cache = ThreadSafeCache()
        compute_count = 0

        def heavy_computation():
            nonlocal compute_count
            compute_count += 1
            time.sleep(0.02)
            return "computed_data"

        def reader():
            return cache.get_or_compute("shared_key", heavy_computation)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(cache.get("shared_key"), "computed_data")
        self.assertEqual(compute_count, 1)


if __name__ == "__main__":
    unittest.main()
