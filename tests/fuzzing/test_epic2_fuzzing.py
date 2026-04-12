import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ArtifactCorruptionEvent,
    DocumentLayoutRegionState,
    HierarchicalDOMManifest,
    MultimodalTokenAnchorState,
    OpticalParsingSLA,
    TabularCellState,
    TabularMatrixProfile,
)


# 1. OpticalParsingSLA
@given(
    st.builds(
        OpticalParsingSLA,
        force_ocr=st.booleans(),
        bitmap_dpi_resolution=st.integers(min_value=72, max_value=600),
        table_structure_recognition=st.booleans(),
    )
)
def test_optical_parsing_sla_valid(sla: OpticalParsingSLA) -> None:
    assert 72 <= sla.bitmap_dpi_resolution <= 600


@given(dpi=st.one_of(st.integers(max_value=71), st.integers(min_value=601)))
def test_optical_parsing_sla_invalid_dpi(dpi: int) -> None:
    with pytest.raises(ValidationError):
        OpticalParsingSLA(bitmap_dpi_resolution=dpi)


# 2. Tabular Matrix
@given(
    st.builds(
        TabularCellState,
        cell_cid=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
        row_index=st.integers(min_value=0, max_value=100),
        column_index=st.integers(min_value=0, max_value=100),
        row_span=st.integers(min_value=1, max_value=10),
        column_span=st.integers(min_value=1, max_value=10),
        text_payload=st.text(max_size=10000),
    )
)
def test_tabular_cell_valid(cell: TabularCellState) -> None:
    assert cell.row_index >= 0


@given(
    rows=st.integers(min_value=1, max_value=50),
    cols=st.integers(min_value=1, max_value=50),
)
def test_tabular_matrix_valid_physics(rows: int, cols: int) -> None:
    cell = TabularCellState(cell_cid="c1", row_index=rows - 1, column_index=cols - 1, text_payload="")
    profile = TabularMatrixProfile(matrix_cid="m1", total_rows=rows, total_columns=cols, cells=[cell])
    assert profile.total_rows == rows


@given(
    rows=st.integers(min_value=1, max_value=50),
    cols=st.integers(min_value=1, max_value=50),
)
def test_tabular_matrix_invalid_physics(rows: int, cols: int) -> None:
    cell = TabularCellState(cell_cid="c1", row_index=rows, column_index=cols, text_payload="")
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: Tabular cell geometry exceeds defined matrix dimensions."
    ):
        TabularMatrixProfile(matrix_cid="m1", total_rows=rows, total_columns=cols, cells=[cell])


# 3. DocumentLayoutRegionState with Tabular
def test_document_layout_region_tabular() -> None:
    anchor = MultimodalTokenAnchorState.model_construct(_fields_set=set(), anchor_cid="a1")
    m = TabularMatrixProfile(matrix_cid="m1", total_rows=1, total_columns=1, cells=[])

    # valid
    r1 = DocumentLayoutRegionState(block_cid="b1", block_class="table", anchor=anchor, tabular_matrix=m)
    assert r1.block_class == "table"

    # invalid
    with pytest.raises(
        ValidationError,
        match=r"Topological Contradiction: tabular_matrix can only be populated if block_class is 'table'.",
    ):
        DocumentLayoutRegionState(block_cid="b1", block_class="paragraph", anchor=anchor, tabular_matrix=m)


# 4. ArtifactCorruptionEvent
@given(
    st.builds(
        ArtifactCorruptionEvent,
        event_cid=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
        timestamp=st.floats(min_value=0.0, max_value=253402300799.0),
        artifact_cid=st.from_regex(r"^[a-zA-Z0-9_.:-]+$", fullmatch=True),
        corruption_class=st.sampled_from(["drm_locked", "malformed_bytes", "ocr_failure", "unsupported_format"]),
        diagnostic_hash=st.from_regex(r"^[a-f0-9]{64}$", fullmatch=True),
    )
)
def test_artifact_corruption_event(event: ArtifactCorruptionEvent) -> None:
    assert event.topology_class == "artifact_corruption"


# 5. HierarchicalDOMManifest DAG validation
def test_hierarchical_dom_dag() -> None:
    anchor = MultimodalTokenAnchorState.model_construct(_fields_set=set(), anchor_cid="a1")
    b1 = DocumentLayoutRegionState(block_cid="b1", block_class="paragraph", anchor=anchor)
    b2 = DocumentLayoutRegionState(block_cid="b2", block_class="paragraph", anchor=anchor)
    b3 = DocumentLayoutRegionState(block_cid="b3", block_class="paragraph", anchor=anchor)

    blocks = {"b1": b1, "b2": b2, "b3": b3}

    # valid DAG
    edges = [("b1", "b2"), ("b2", "b3")]
    dom = HierarchicalDOMManifest(dom_cid="d1", root_block_cid="b1", blocks=blocks, containment_edges=edges)
    assert dom.topology_class == "hierarchical_dom"

    # invalid - missing root
    with pytest.raises(ValidationError, match=r"Topological Contradiction: root_block_cid not found in blocks."):
        HierarchicalDOMManifest(dom_cid="d1", root_block_cid="missing", blocks=blocks, containment_edges=[])

    # invalid - ghost pointer
    with pytest.raises(ValidationError, match=r"Ghost pointer: Containment edge references undefined block."):
        HierarchicalDOMManifest(dom_cid="d1", root_block_cid="b1", blocks=blocks, containment_edges=[("b1", "ghost")])

    # invalid - cycle
    with pytest.raises(
        ValidationError, match=r"Topological Contradiction: Hierarchical DOM tree contains a spatial cycle."
    ):
        HierarchicalDOMManifest(
            dom_cid="d1", root_block_cid="b1", blocks=blocks, containment_edges=[("b1", "b2"), ("b2", "b1")]
        )
