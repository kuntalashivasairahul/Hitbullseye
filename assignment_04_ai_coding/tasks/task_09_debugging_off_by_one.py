"""Task 9: Debugging - Robust Subarray Prefix & Sliding Window Max.

Eliminates off-by-one errors in prefix sum ranges, sliding window maximums,
and binary search duplicate boundary spans.
"""

from __future__ import annotations

import collections
from typing import List, Tuple


class SubarrayRangeProcessor:
    """Rigorous array manipulation algorithms immune to boundary off-by-one errors."""

    @classmethod
    def prefix_sum_query(cls, arr: List[int], queries: List[Tuple[int, int]]) -> List[int]:
        """Compute inclusive range sums query [L, R] for 0 <= L <= R < len(arr)."""
        if not arr or not queries:
            return []

        n = len(arr)
        # 1-indexed prefix sum array: P[i] = sum(arr[0..i-1])
        prefix = [0] * (n + 1)
        for i in range(n):
            prefix[i + 1] = prefix[i] + arr[i]

        results = []
        for left, right in queries:
            if left < 0 or right >= n or left > right:
                raise IndexError(f"Query range [{left}, {right}] out of bounds for array length {n}.")
            # Sum from index left to right inclusive is prefix[right + 1] - prefix[left]
            results.append(prefix[right + 1] - prefix[left])

        return results

    @classmethod
    def sliding_window_maximum(cls, nums: List[int], k: int) -> List[int]:
        """Return maximum elements in sliding window of size k using monotonic deque in O(N) time."""
        if not nums or k <= 0:
            return []

        n = len(nums)
        if k >= n:
            return [max(nums)]

        if k == 1:
            return list(nums)

        # Deque stores indices of elements in descending value order
        deq: collections.deque[int] = collections.deque()
        results: List[int] = []

        for i in range(n):
            # 1. Remove indices outside current window [i - k + 1, i]
            while deq and deq[0] < i - k + 1:
                deq.popleft()

            # 2. Maintain monotonic decreasing order
            while deq and nums[deq[-1]] <= nums[i]:
                deq.pop()

            deq.append(i)

            # 3. Add to results once first window is formed
            if i >= k - 1:
                results.append(nums[deq[0]])

        return results

    @classmethod
    def binary_search_bounds(cls, sorted_arr: List[int], target: int) -> Tuple[int, int]:
        """Find the (first_index, last_index) inclusive span of target in O(log n) time."""
        if not sorted_arr:
            return -1, -1

        def find_bound(is_first: bool) -> int:
            left, right = 0, len(sorted_arr) - 1
            boundary = -1

            while left <= right:
                mid = left + (right - left) // 2
                if sorted_arr[mid] == target:
                    boundary = mid
                    if is_first:
                        right = mid - 1  # Keep searching left
                    else:
                        left = mid + 1   # Keep searching right
                elif sorted_arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1

            return boundary

        first_idx = find_bound(is_first=True)
        if first_idx == -1:
            return -1, -1

        last_idx = find_bound(is_first=False)
        return first_idx, last_idx
