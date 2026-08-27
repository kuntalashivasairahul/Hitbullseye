"""Task 8: Debugging - Thread-Safe In-Memory Cache with RLock.

Eliminates race conditions, dirty reads, and cache stampedes in a multi-threaded
in-memory cache using re-entrant locks (threading.RLock) and double-checked locking.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple


class ThreadSafeCache:
    """Thread-safe in-memory cache with atomic read-modify-write semantics."""

    def __init__(self):
        # Maps key -> (value, expiry_timestamp)
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()

    def _is_expired(self, expiry: Optional[float], now: float) -> bool:
        return expiry is not None and now >= expiry

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value if present and unexpired; lazily evicts expired keys."""
        with self._lock:
            if key not in self._store:
                return default

            val, expiry = self._store[key]
            now = time.time()
            if self._is_expired(expiry, now):
                del self._store[key]
                return default

            return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store key-value pair with optional TTL expiration."""
        with self._lock:
            expiry = (time.time() + ttl_seconds) if ttl_seconds is not None else None
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Atomically remove key from cache. Returns True if key existed."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl_seconds: Optional[float] = None,
    ) -> Any:
        """Atomically get cached value or invoke compute_func exactly once (stampede prevention)."""
        with self._lock:
            # 1. First check
            val = self.get(key, default=None)
            if val is not None:
                return val

            # 2. Compute once while lock is held
            computed_val = compute_func()
            self.set(key, computed_val, ttl_seconds=ttl_seconds)
            return computed_val

    def clear(self) -> None:
        """Atomically wipe all cached items."""
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        """Return count of unexpired keys."""
        with self._lock:
            now = time.time()
            # Clean up expired on inspection
            expired_keys = [k for k, (_, exp) in self._store.items() if self._is_expired(exp, now)]
            for k in expired_keys:
                del self._store[k]
            return len(self._store)
