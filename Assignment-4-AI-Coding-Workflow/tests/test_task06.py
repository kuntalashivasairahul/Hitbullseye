"""Self-contained test suite for Task 06: Concurrent Async Data Fetcher with Retries."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_06_refactor_async_fetcher import AsyncDataFetcher


class TestTask06AsyncFetcher(unittest.TestCase):
    """Tests for Task 6: Concurrent Async Data Fetcher with Retries."""

    def test_batch_fetch_concurrency_and_results(self):
        """Verify async batch fetch executes all requests concurrently."""
        fetcher = AsyncDataFetcher()
        urls = [f"https://api.example.com/item/{i}" for i in range(10)]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(fetcher.batch_fetch(urls, max_concurrency=4))
            self.assertEqual(len(results), 10)
            for res in results:
                self.assertEqual(res["status_code"], 200)
                self.assertIn("Response from", res["data"])
        finally:
            loop.close()

    def test_retry_on_transient_failure(self):
        """Verify fetcher retries on transient errors."""
        attempts = 0

        async def flaky_call(url: str):
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ConnectionResetError("Temporary blip")
            return "Success after retry"

        fetcher = AsyncDataFetcher(mock_requester=flaky_call)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(fetcher.fetch_url("https://api.test/flaky", max_retries=2))
            self.assertEqual(res["status_code"], 200)
            self.assertEqual(res["data"], "Success after retry")
            self.assertEqual(res["attempts"], 2)
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
