# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at [https://prosperitylicense.com/versions/3.0.0](https://prosperitylicense.com/versions/3.0.0)
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: [https://github.com/CoReason-AI/coreason-manifest](https://github.com/CoReason-AI/coreason-manifest)

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    MultimodalTokenAnchorState,
)


# 1. Base Factory for DRY Context Generation
def build_anchor() -> MultimodalTokenAnchorState:
    return MultimodalTokenAnchorState(
        token_span_start=0,
        token_span_end=10,
        visual_patch_hashes=[],
        bounding_box=(0.0, 0.0, 1.0, 1.0),
        block_type="paragraph",
    )


def build_block(block_id: str) -> DocumentLayoutRegionState:
    return DocumentLayoutRegionState(block_id=block_id, block_type="paragraph", anchor=build_anchor())


# 2. Atomic Parameterized Tests for Referential Integrity (Ghost Nodes)
@pytest.mark.parametrize(
    ("edges", "match_string"),
    [([("D", "B")], r"Source block 'D' does not exist"), ([("A", "D")], r"Target block 'D' does not exist")],
)
def test_document_layout_manifest_ghost_nodes(edges: list[tuple[str, str]], match_string: str) -> None:
    """Prove the topological boundary strictly severs missing coordinate references."""
    blocks = {"A": build_block("A"), "B": build_block("B"), "C": build_block("C")}
    with pytest.raises(ValidationError, match=match_string):
        DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=edges)


# 3. Atomic Parameterized Tests for Static Cycles
@pytest.mark.parametrize(
    "edges",
    [
        [("A", "A")],  # Self-cycle
        [("A", "B"), ("B", "C"), ("C", "A")],  # 3-node cycle
        [("A", "B"), ("B", "A")],  # 2-node cycle
    ],
)
def test_document_layout_manifest_static_cycles(edges: list[tuple[str, str]]) -> None:
    """Prove the manifest deterministically collapses when chronological paradoxes are injected."""
    blocks = {"A": build_block("A"), "B": build_block("B"), "C": build_block("C")}
    with pytest.raises(ValidationError, match=r"Reading order contains a cyclical contradiction"):
        DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=edges)


# 4. Fuzzing Valid DAG Topologies
@st.composite
def valid_dag_strategy(draw: st.DrawFn) -> dict[str, Any]:
    """Generates mathematically guaranteed DAGs by strictly pointing edges from lower to higher array indices."""
    node_ids = draw(st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=15, unique=True))
    edges: list[tuple[str, str]] = []
    for i in range(len(node_ids)):
        edges.extend((node_ids[i], node_ids[j]) for j in range(i + 1, len(node_ids)) if draw(st.booleans()))
    return {"nodes": node_ids, "edges": edges}


@given(dag_data=valid_dag_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_document_layout_manifest_fuzz_valid_dag(dag_data: dict[str, Any]) -> None:
    """
    AGENT INSTRUCTION: Fuzz the topological engine. Prove that any mathematically
    sound DAG is strictly accepted without hallucinating false-positive cycle rejections.
    """
    blocks = {n_id: build_block(n_id) for n_id in dag_data["nodes"]}
    manifest = DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=dag_data["edges"])

    assert len(manifest.blocks) == len(dag_data["nodes"])
    assert manifest.chronological_flow_edges == dag_data["edges"]
