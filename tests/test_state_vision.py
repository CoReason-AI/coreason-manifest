# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    MathematicalNotationExtractionState,
    MultimodalTokenAnchorState,
    TabularCellState,
    TabularMatrixExtractionState,
)


def test_layout_cycle_prevention() -> None:
    anchor = MultimodalTokenAnchorState(token_span_start=0, token_span_end=10)
    block1 = DocumentLayoutRegionState(block_id="b1", block_type="paragraph", anchor=anchor)
    block2 = DocumentLayoutRegionState(block_id="b2", block_type="paragraph", anchor=anchor)

    with pytest.raises(ValidationError, match="cyclical contradiction"):
        DocumentLayoutManifest(blocks={"b1": block1, "b2": block2}, reading_order_edges=[("b1", "b2"), ("b2", "b1")])


def test_tabular_collision_prevention() -> None:
    anchor = MultimodalTokenAnchorState(token_span_start=0, token_span_end=10)
    # Cell 1 spans (0,0), (0,1), (1,0), (1,1)
    cell1 = TabularCellState(row_index=0, col_index=0, row_span=2, col_span=2, content="A", anchor=anchor)
    # Cell 2 tries to occupy (1,1)
    cell2 = TabularCellState(row_index=1, col_index=1, row_span=1, col_span=1, content="B", anchor=anchor)

    with pytest.raises(ValidationError, match="Geometric Collision Detected"):
        TabularMatrixExtractionState(cells=[cell1, cell2])


def test_mathematical_ungrounded_prevention() -> None:
    empty_anchor = MultimodalTokenAnchorState()  # Neither bounding_box nor token_span
    with pytest.raises(ValidationError, match="definitive visual or token bounding box"):
        MathematicalNotationExtractionState(
            math_type="inline", syntax="latex", expression="E=mc^2", anchor=empty_anchor
        )
