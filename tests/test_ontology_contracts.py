import pytest

from coreason_manifest.spec.ontology import (
    BrowserDOMState,
    DocumentLayoutManifest,
    DocumentLayoutRegionState,
    DynamicLayoutManifest,
    MultimodalTokenAnchorState,
    QuorumPolicy,
    SpatialBoundingBoxProfile,
)


def test_quorum_policy_bft_math():

    # Valid: 3 * 1 + 1 = 4. 4 >= 4 (Valid)
    valid_policy = QuorumPolicy(
        max_tolerable_faults=1, min_quorum_size=4, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    assert valid_policy.min_quorum_size == 4

    # Invalid: 3 * 1 + 1 = 4. 3 < 4 (Invalid)
    with pytest.raises(ValueError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1."):
        QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )


def test_spatial_bounding_box_geometry():

    # Valid
    box = SpatialBoundingBoxProfile(x_min=0.1, y_min=0.1, x_max=0.9, y_max=0.9)
    assert box.x_min == 0.1

    # Invalid x_min > x_max
    with pytest.raises(ValueError, match=r"x_min cannot be strictly greater than x_max."):
        SpatialBoundingBoxProfile(x_min=0.9, y_min=0.1, x_max=0.1, y_max=0.9)

    # Invalid y_min > y_max
    with pytest.raises(ValueError, match=r"y_min cannot be strictly greater than y_max."):
        SpatialBoundingBoxProfile(x_min=0.1, y_min=0.9, x_max=0.9, y_max=0.1)


def test_dynamic_layout_manifest_ast_safety():

    # Valid string
    valid_manifest = DynamicLayoutManifest(layout_tstring="f'{a} and {b}'")
    assert valid_manifest.layout_tstring == "f'{a} and {b}'"

    # Invalid: Contains function call (kinetic bleed)
    with pytest.raises(ValueError, match=r"Kinetic execution bleed detected: Forbidden AST node Call"):
        DynamicLayoutManifest(layout_tstring="f'{os.system(\"ls\")}'")

    # Invalid: Contains a completely different statement (like assignment)
    with pytest.raises(ValueError, match=r"Kinetic execution bleed detected: Forbidden AST node Assign"):
        DynamicLayoutManifest(layout_tstring="x = 1")


def test_document_layout_manifest_dag_integrity():

    anchor1 = MultimodalTokenAnchorState(token_span_start=0, token_span_end=10)
    anchor2 = MultimodalTokenAnchorState(token_span_start=11, token_span_end=20)
    anchor3 = MultimodalTokenAnchorState(token_span_start=21, token_span_end=30)

    block1 = DocumentLayoutRegionState(block_id="b1", block_type="paragraph", anchor=anchor1)
    block2 = DocumentLayoutRegionState(block_id="b2", block_type="paragraph", anchor=anchor2)
    block3 = DocumentLayoutRegionState(block_id="b3", block_type="paragraph", anchor=anchor3)

    blocks = {"b1": block1, "b2": block2, "b3": block3}

    # Valid DAG
    valid_manifest = DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=[("b1", "b2"), ("b2", "b3")])
    assert valid_manifest.blocks["b1"].block_id == "b1"

    # Invalid: Ghost node in source
    with pytest.raises(ValueError, match=r"Source block 'ghost' does not exist."):
        DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=[("ghost", "b2")])

    # Invalid: Ghost node in target
    with pytest.raises(ValueError, match=r"Target block 'ghost' does not exist."):
        DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=[("b1", "ghost")])

    # Invalid: Cycle
    with pytest.raises(ValueError, match=r"Reading order contains a cyclical contradiction."):
        DocumentLayoutManifest(blocks=blocks, chronological_flow_edges=[("b1", "b2"), ("b2", "b3"), ("b3", "b1")])


def test_browser_dom_state_ssrf_prevention():

    # Valid
    BrowserDOMState(
        current_url="https://www.google.com",
        viewport_size=(1920, 1080),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )

    # Invalid: file://
    with pytest.raises(ValueError, match=r"SSRF topological violation detected: file:// schema is forbidden"):
        BrowserDOMState(
            current_url="file:///etc/passwd",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    # Invalid: localhost
    with pytest.raises(ValueError, match=r"SSRF topological violation detected: localhost"):
        BrowserDOMState(
            current_url="http://localhost:8080",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    # Invalid: 127.0.0.1 (loopback)
    with pytest.raises(ValueError, match=r"SSRF mathematical bound violation detected: 127.0.0.1"):
        BrowserDOMState(
            current_url="http://127.0.0.1:8080",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )
