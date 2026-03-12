import pytest

from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    MultimodalTokenAnchorState,
)


def test_document_layout_manifest_dag_cycles() -> None:
    # 1. Create dummy valid anchor to reuse
    anchor = MultimodalTokenAnchorState(
        token_span_start=0,
        token_span_end=10,
        visual_patch_hashes=[],
        bounding_box=(0.0, 0.0, 1.0, 1.0),
        block_type="paragraph",
    )

    # 2. Create some blocks
    block_a = DocumentLayoutRegionState(block_id="A", block_type="paragraph", anchor=anchor)
    block_b = DocumentLayoutRegionState(block_id="B", block_type="paragraph", anchor=anchor)
    block_c = DocumentLayoutRegionState(block_id="C", block_type="paragraph", anchor=anchor)

    # 3. Test a valid DAG (A -> B -> C)
    valid_manifest = DocumentLayoutManifest(
        blocks={"A": block_a, "B": block_b, "C": block_c}, chronological_flow_edges=[("A", "B"), ("B", "C")]
    )
    assert valid_manifest.blocks["A"] == block_a
    assert valid_manifest.blocks["B"] == block_b
    assert valid_manifest.blocks["C"] == block_c
    assert valid_manifest.chronological_flow_edges == [("A", "B"), ("B", "C")]

    # 4. Test missing source block
    with pytest.raises(ValueError, match=r"Source block 'D' does not exist\."):
        DocumentLayoutManifest(
            blocks={"A": block_a, "B": block_b, "C": block_c}, chronological_flow_edges=[("D", "B"), ("B", "C")]
        )

    # 5. Test missing target block
    with pytest.raises(ValueError, match=r"Target block 'D' does not exist\."):
        DocumentLayoutManifest(
            blocks={"A": block_a, "B": block_b, "C": block_c}, chronological_flow_edges=[("A", "B"), ("B", "D")]
        )

    # 6. Test a cyclic DAG (A -> B -> C -> A)
    with pytest.raises(ValueError, match=r"Reading order contains a cyclical contradiction\."):
        DocumentLayoutManifest(
            blocks={"A": block_a, "B": block_b, "C": block_c},
            chronological_flow_edges=[("A", "B"), ("B", "C"), ("C", "A")],
        )

    # 7. Test self cycle (A -> A)
    with pytest.raises(ValueError, match=r"Reading order contains a cyclical contradiction\."):
        DocumentLayoutManifest(blocks={"A": block_a}, chronological_flow_edges=[("A", "A")])

    # 8. Test diamond DAG (A -> B -> D, A -> C -> D)
    block_d = DocumentLayoutRegionState(block_id="D", block_type="paragraph", anchor=anchor)
    diamond_manifest = DocumentLayoutManifest(
        blocks={"A": block_a, "B": block_b, "C": block_c, "D": block_d},
        chronological_flow_edges=[("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
    )
    assert diamond_manifest is not None
