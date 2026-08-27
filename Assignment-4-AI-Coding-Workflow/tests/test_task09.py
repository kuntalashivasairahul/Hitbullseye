"""Self-contained test suite for Task 09: Subarray & Window Processor."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_09_debugging_off_by_one import SubarrayRangeProcessor


class TestTask09OffByOne(unittest.TestCase):
    """Tests for Task 9: Robust Subarray Prefix & Sliding Window Max."""

    def test_prefix_sum_inclusive_ranges(self):
        """Verify prefix sum range queries [L, R] inclusive without index errors."""
        arr = [2, 4, 6, 8, 10]
        queries = [
            (0, 4),  # Full sum: 30
            (0, 0),  # Single element at 0: 2
            (4, 4),  # Single element at end: 10
            (1, 3),  # 4 + 6 + 8 = 18
        ]
        results = SubarrayRangeProcessor.prefix_sum_query(arr, queries)
        self.assertEqual(results, [30, 2, 10, 18])

    def test_sliding_window_maximum(self):
        """Verify sliding window maximum handles boundary window sizes."""
        nums = [1, 3, -1, -3, 5, 3, 6, 7]
        res = SubarrayRangeProcessor.sliding_window_maximum(nums, k=3)
        self.assertEqual(res, [3, 3, 5, 5, 6, 7])

        # k = 1 (every element is its own max)
        self.assertEqual(SubarrayRangeProcessor.sliding_window_maximum(nums, k=1), nums)

        # k >= len (single maximum)
        self.assertEqual(SubarrayRangeProcessor.sliding_window_maximum(nums, k=len(nums)), [7])

    def test_binary_search_bounds(self):
        """Verify binary search finds exact duplicate span indices or (-1, -1)."""
        sorted_arr = [1, 2, 4, 4, 4, 4, 7, 9]
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 4), (2, 5))
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 1), (0, 0))
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 9), (7, 7))
        self.assertEqual(SubarrayRangeProcessor.binary_search_bounds(sorted_arr, 5), (-1, -1))


if __name__ == "__main__":
    unittest.main()
