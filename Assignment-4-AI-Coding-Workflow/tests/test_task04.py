"""Self-contained test suite for Task 04: Directed Graph Cycle Detector & Topo Sort."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure assignment root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tasks.task_04_algo_graph_cycles import DirectedGraphCycleDetector


class TestTask04GraphCycles(unittest.TestCase):
    """Tests for Task 4: Directed Graph Cycle Detector & Topo Sort."""

    def test_detects_self_loops(self):
        """Verify self-loops A -> A are detected as cycles."""
        detector = DirectedGraphCycleDetector()
        detector.add_edge("A", "A")
        self.assertTrue(detector.has_cycle())
        self.assertIsNone(detector.topological_sort())

    def test_detects_simple_cycle(self):
        """Verify cycle A -> B -> C -> A is detected."""
        detector = DirectedGraphCycleDetector()
        detector.add_edge("A", "B")
        detector.add_edge("B", "C")
        detector.add_edge("C", "A")
        self.assertTrue(detector.has_cycle())
        self.assertIsNone(detector.topological_sort())

    def test_dag_topological_sort(self):
        """Verify topological sort on a valid DAG produces valid linear dependency order."""
        detector = DirectedGraphCycleDetector()
        detector.add_edge("Core", "Auth")
        detector.add_edge("Core", "DB")
        detector.add_edge("Auth", "API")
        detector.add_edge("DB", "API")

        self.assertFalse(detector.has_cycle())
        order = detector.topological_sort()
        self.assertIsNotNone(order)
        self.assertEqual(len(order), 4)
        for u, v in [("Core", "Auth"), ("Core", "DB"), ("Auth", "API"), ("DB", "API")]:
            self.assertLess(order.index(u), order.index(v))


if __name__ == "__main__":
    unittest.main()
