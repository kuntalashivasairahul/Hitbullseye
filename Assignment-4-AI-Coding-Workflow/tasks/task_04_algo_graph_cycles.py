"""Task 4: Algorithm - Directed Graph Cycle Detector & Topological Sort.

Employs 3-color DFS (White=0, Gray=1, Black=2) to detect cycles, extract circular paths,
and compute topological orderings for Directed Acyclic Graphs (DAGs).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


class DirectedGraphCycleDetector:
    """Directed graph analyzer for circular dependencies and topological sorting."""

    WHITE = 0  # Unvisited
    GRAY = 1   # Visiting (current recursion stack)
    BLACK = 2  # Visited & fully processed

    def __init__(self):
        self.adj: Dict[str, List[str]] = {}
        self.nodes: Set[str] = set()

    def add_edge(self, u: str, v: str) -> None:
        """Add directed edge from u to v."""
        self.nodes.add(u)
        self.nodes.add(v)
        self.adj.setdefault(u, []).append(v)
        self.adj.setdefault(v, [])

    def has_cycle(self) -> bool:
        """Check if any cycle exists in the graph."""
        colors: Dict[str, int] = {node: self.WHITE for node in self.nodes}

        def dfs(node: str) -> bool:
            colors[node] = self.GRAY
            for neighbor in self.adj.get(node, []):
                if colors[neighbor] == self.GRAY:
                    return True  # Back-edge found!
                if colors[neighbor] == self.WHITE and dfs(neighbor):
                    return True
            colors[node] = self.BLACK
            return False

        for node in sorted(self.nodes):
            if colors[node] == self.WHITE:
                if dfs(node):
                    return True
        return False

    def find_all_cycles(self) -> List[List[str]]:
        """Find distinct elementary cycles in the directed graph."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()

        def dfs_path(curr: str, path: List[str]):
            for neighbor in self.adj.get(curr, []):
                if neighbor in path:
                    idx = path.index(neighbor)
                    cycle = path[idx:] + [neighbor]
                    # Canonical rotation to avoid duplicate cycles
                    canon = cycle[:-1]
                    min_idx = canon.index(min(canon))
                    canon_rotated = canon[min_idx:] + canon[:min_idx] + [canon[min_idx]]
                    if canon_rotated not in cycles:
                        cycles.append(canon_rotated)
                elif neighbor not in visited:
                    dfs_path(neighbor, path + [neighbor])

        for node in sorted(self.nodes):
            dfs_path(node, [node])
            visited.add(node)

        return cycles

    def topological_sort(self) -> Optional[List[str]]:
        """Return topological order if graph is a DAG, or None if cycles exist."""
        if self.has_cycle():
            return None

        visited: Set[str] = set()
        order: List[str] = []

        def dfs(node: str):
            visited.add(node)
            for neighbor in sorted(self.adj.get(node, [])):
                if neighbor not in visited:
                    dfs(neighbor)
            order.append(node)

        for node in sorted(self.nodes):
            if node not in visited:
                dfs(node)

        return order[::-1]
