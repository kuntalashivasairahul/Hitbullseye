"""Task 3: Algorithm - High-Throughput Rate Limiting Sliding Window.

Tracks request timestamps using a sliding window algorithm to ensure smooth rate limits
with precise retry-after latency and automatic stale key eviction.
"""

from __future__ import annotations

import collections
import time
from typing import Dict, Deque, Optional, Tuple


class SlidingWindowRateLimiter:
    """Sliding-window log rate limiter with memory management."""

    def __init__(self):
        # Maps key -> deque of timestamps
        self._store: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: float,
        current_time: Optional[float] = None,
    ) -> Tuple[bool, int, float]:
        """Check if request is allowed under the sliding window constraint.

        Returns:
            Tuple of (allowed: bool, remaining_capacity: int, retry_after_seconds: float)
        """
        now = time.time() if current_time is None else float(current_time)
        window_start = now - window_seconds
        timestamps = self._store[key]

        # Evict timestamps outside current window
        while timestamps and timestamps[0] <= window_start:
            timestamps.popleft()

        current_count = len(timestamps)

        if current_count < max_requests:
            timestamps.append(now)
            remaining = max_requests - (current_count + 1)
            return True, remaining, 0.0
        else:
            # Over limit: calculate time until oldest entry leaves the window
            oldest = timestamps[0]
            retry_after = max(0.0, round((oldest + window_seconds) - now, 4))
            return False, 0, retry_after

    def reset(self, key: str) -> None:
        """Reset rate limit history for a specific key."""
        if key in self._store:
            del self._store[key]

    def cleanup_expired(self, older_than_seconds: float, current_time: Optional[float] = None) -> int:
        """Purge idle keys whose newest timestamps are older than threshold."""
        now = time.time() if current_time is None else float(current_time)
        cutoff = now - older_than_seconds
        keys_to_remove = []

        for key, timestamps in self._store.items():
            if not timestamps or timestamps[-1] <= cutoff:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._store[key]

        return len(keys_to_remove)
