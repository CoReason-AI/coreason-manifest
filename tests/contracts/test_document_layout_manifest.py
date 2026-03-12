import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    MultimodalTokenAnchorState,
)


def create_region(block_id: str) -> DocumentLayoutRegionState:
    return DocumentLayoutRegionState(
        block_id=block_id,
        block_type="paragraph",
        anchor=MultimodalTokenAnchorState(
            token_span_start=0,
            token_span_end=10,
        ),
    )


def test_document_layout_manifest_valid_dag() -> None:
    manifest = DocumentLayoutManifest(
        blocks={
            "A": create_region("A"),
            "B": create_region("B"),
            "C": create_region("C"),
        },
        chronological_flow_edges=[("A", "B"), ("B", "C")],
    )
    assert len(manifest.blocks) == 3


def test_document_layout_manifest_invalid_source() -> None:
    with pytest.raises(ValidationError, match="Source block 'X' does not exist"):
        DocumentLayoutManifest(
            blocks={
                "A": create_region("A"),
                "B": create_region("B"),
            },
            chronological_flow_edges=[("X", "B")],
        )


def test_document_layout_manifest_invalid_target() -> None:
    with pytest.raises(ValidationError, match="Target block 'Y' does not exist"):
        DocumentLayoutManifest(
            blocks={
                "A": create_region("A"),
                "B": create_region("B"),
            },
            chronological_flow_edges=[("A", "Y")],
        )


def test_document_layout_manifest_cyclic_contradiction() -> None:
    with pytest.raises(ValidationError, match=r"Reading order contains a cyclical contradiction\."):
        DocumentLayoutManifest(
            blocks={
                "A": create_region("A"),
                "B": create_region("B"),
                "C": create_region("C"),
            },
            chronological_flow_edges=[("A", "B"), ("B", "C"), ("C", "A")],
        )
