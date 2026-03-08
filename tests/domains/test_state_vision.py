import pytest
from pydantic import ValidationError

from coreason_manifest.state.semantic import MultimodalTokenAnchor
from coreason_manifest.state.vision import (
    DocumentLayoutAnalysis,
    DocumentLayoutBlock,
    MathematicalNotationExtraction,
    TableCell,
    TabularDataExtraction,
)


def test_layout_cycle_prevention() -> None:
    anchor = MultimodalTokenAnchor(token_span_start=0, token_span_end=10)
    block1 = DocumentLayoutBlock(block_id="b1", block_type="paragraph", anchor=anchor)
    block2 = DocumentLayoutBlock(block_id="b2", block_type="paragraph", anchor=anchor)

    with pytest.raises(ValidationError, match="cyclical contradiction"):
        DocumentLayoutAnalysis(blocks={"b1": block1, "b2": block2}, reading_order_edges=[("b1", "b2"), ("b2", "b1")])


def test_tabular_collision_prevention() -> None:
    anchor = MultimodalTokenAnchor(token_span_start=0, token_span_end=10)
    # Cell 1 spans (0,0), (0,1), (1,0), (1,1)
    cell1 = TableCell(row_index=0, col_index=0, row_span=2, col_span=2, content="A", anchor=anchor)
    # Cell 2 tries to occupy (1,1)
    cell2 = TableCell(row_index=1, col_index=1, row_span=1, col_span=1, content="B", anchor=anchor)

    with pytest.raises(ValidationError, match="Geometric Collision Detected"):
        TabularDataExtraction(cells=[cell1, cell2])


def test_mathematical_ungrounded_prevention() -> None:
    empty_anchor = MultimodalTokenAnchor()  # Neither bounding_box nor token_span
    with pytest.raises(ValidationError, match="definitive visual or token bounding box"):
        MathematicalNotationExtraction(math_type="inline", syntax="latex", expression="E=mc^2", anchor=empty_anchor)


def test_statistical_chart_extraction_semantic_binding() -> None:
    from coreason_manifest.state.vision import AffineTransformMatrix, StatisticalChartExtraction

    axis_x = AffineTransformMatrix(
        pixel_min=0.0, pixel_max=100.0, domain_min=0.0, domain_max=12.0, scale_type="linear", unit="Months"
    )

    # Intentionally out-of-order dictionary
    extraction = StatisticalChartExtraction(
        axes={"x": axis_x},
        data_series=[{"x": 5.0, "survival_prob": 0.8}],
        legend_mappings={"#FF0000": "Placebo", "#0000FF": "Treatment"},
    )

    assert extraction.axes["x"].unit == "Months"
    # Prove the model_validator sorted the dictionary keys lexicographically
    keys = list(extraction.legend_mappings.keys())
    assert keys == ["#0000FF", "#FF0000"]
