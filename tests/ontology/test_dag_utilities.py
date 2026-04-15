# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for pure-Python DAG utility functions."""

from hypothesis import given, settings
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    _pure_python_is_dag,
    _pure_python_longest_path_length,
)


class TestPurePythonIsDag:
    """Verify Kahn's algorithm implementation."""

    def test_empty_graph_is_dag(self) -> None:
        assert _pure_python_is_dag({}) is True

    def test_single_node_is_dag(self) -> None:
        assert _pure_python_is_dag({"a": []}) is True

    def test_linear_chain_is_dag(self) -> None:
        assert _pure_python_is_dag({"a": ["b"], "b": ["c"], "c": []}) is True

    def test_diamond_is_dag(self) -> None:
        adj = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
        assert _pure_python_is_dag(adj) is True

    def test_simple_cycle_not_dag(self) -> None:
        assert _pure_python_is_dag({"a": ["b"], "b": ["a"]}) is False

    def test_self_loop_not_dag(self) -> None:
        assert _pure_python_is_dag({"a": ["a"]}) is False

    def test_triangle_cycle_not_dag(self) -> None:
        assert _pure_python_is_dag({"a": ["b"], "b": ["c"], "c": ["a"]}) is False

    @given(
        st.integers(min_value=2, max_value=10).flatmap(
            lambda n: st.just({str(i): [str(j) for j in range(i + 1, min(i + 3, n))] for i in range(n)})
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_forward_only_edges_are_dag(self, adjacency: dict[str, list[str]]) -> None:
        """A graph with only forward edges (i -> j where j > i) is always a DAG."""
        assert _pure_python_is_dag(adjacency) is True


class TestPurePythonLongestPathLength:
    """Verify longest path computation via topological-order DP."""

    def test_empty_graph(self) -> None:
        assert _pure_python_longest_path_length({}) == 0

    def test_single_node(self) -> None:
        assert _pure_python_longest_path_length({"a": []}) == 0

    def test_linear_chain_length(self) -> None:
        # a -> b -> c -> d: longest path = 3 edges
        adj = {"a": ["b"], "b": ["c"], "c": ["d"], "d": []}
        assert _pure_python_longest_path_length(adj) == 3

    def test_diamond_longest_path(self) -> None:
        # a -> b -> d, a -> c -> d: longest = 2 edges
        adj = {"a": ["b", "c"], "b": ["d"], "c": ["d"], "d": []}
        assert _pure_python_longest_path_length(adj) == 2

    def test_wide_graph(self) -> None:
        # a -> b, a -> c, a -> d: longest = 1 edge
        adj = {"a": ["b", "c", "d"], "b": [], "c": [], "d": []}
        assert _pure_python_longest_path_length(adj) == 1

    @given(
        st.integers(min_value=2, max_value=15).flatmap(
            lambda n: st.just({str(i): [str(i + 1)] if i < n - 1 else [] for i in range(n)})
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_linear_chain_property(self, adjacency: dict[str, list[str]]) -> None:
        """A linear chain of n nodes has n-1 edges as its longest path."""
        n = len(adjacency)
        assert _pure_python_longest_path_length(adjacency) == n - 1
