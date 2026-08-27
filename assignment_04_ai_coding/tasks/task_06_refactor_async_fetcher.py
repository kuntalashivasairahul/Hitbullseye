"""Task 6: Refactoring - Concurrent Async Data Fetcher with Retries.

Employs asyncio concurrency, bounded semaphore pools, timeout guarantees,
and exponential backoff retry mechanisms.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional


class AsyncDataFetcher:
    """Non-blocking concurrent HTTP data fetcher with bounded concurrency."""

    def __init__(self, mock_requester: Optional[Callable[[str], Any]] = None):
        self.mock_requester = mock_requester

    async def fetch_url(
        self,
        url: str,
        timeout: float = 5.0,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Fetch a single URL asynchronously with timeout and retries."""
        start_time = time.perf_counter()
        attempts = 0
        last_error = None

        while attempts <= max_retries:
            attempts += 1
            try:
                # Use custom mock requester if provided, or simulated non-blocking fetch
                if self.mock_requester:
                    result = await asyncio.wait_for(self.mock_requester(url), timeout=timeout)
                else:
                    await asyncio.sleep(0.01)  # Simulate network hop
                    result = f"Response from {url}"

                latency = (time.perf_counter() - start_time) * 1000.0
                return {
                    "url": url,
                    "status_code": 200,
                    "data": result,
                    "attempts": attempts,
                    "latency_ms": round(latency, 2),
                    "error": None,
                }
            except asyncio.TimeoutError:
                last_error = f"Request timed out after {timeout}s"
            except Exception as e:
                last_error = str(e)

            # Exponential backoff
            if attempts <= max_retries:
                await asyncio.sleep(0.02 * (2 ** (attempts - 1)))

        latency = (time.perf_counter() - start_time) * 1000.0
        return {
            "url": url,
            "status_code": 500,
            "data": None,
            "attempts": attempts,
            "latency_ms": round(latency, 2),
            "error": last_error,
        }

    async def batch_fetch(
        self,
        urls: List[str],
        max_concurrency: int = 5,
        timeout: float = 5.0,
        max_retries: int = 2,
    ) -> List[Dict[str, Any]]:
        """Fetch a batch of URLs concurrently, bounded by max_concurrency semaphore."""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _bounded_fetch(u: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.fetch_url(u, timeout=timeout, max_retries=max_retries)

        tasks = [_bounded_fetch(url) for url in urls]
        return await asyncio.gather(*tasks)
