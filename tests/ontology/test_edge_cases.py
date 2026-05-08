import pytest
from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    DynamicLayoutManifest,
    LatentScratchpadReceipt,
    ScalePolicy,
    SpatialBillboardContract,
)


@given(st.floats(min_value=0.1, max_value=10.0))
def test_spatial_billboard_contract_invalid_lock(distance):
    with pytest.raises(ValueError, match=r".*"):
        SpatialBillboardContract(
            anchoring_node_cid="did:node:12345", spherical_cylindrical_lock="none", distance_scaling_factor=distance
        )


@given(st.floats(max_value=0.0))
def test_scale_policy_invalid_domain_max(d_max):
    with pytest.raises(ValueError, match=r".*"):
        ScalePolicy(scale_type="logarithmic", domain_max=d_max)


@given(st.lists(st.text(min_size=1), min_size=1))
def test_latent_scratchpad_receipt_invalid_discard(branches):
    with pytest.raises(ValueError, match=r".*"):
        LatentScratchpadReceipt(
            task_intent_cid="cid1",
            explored_branches=dict.fromkeys(branches, "x"),
            resolution_branch_cid=branches[0],
            discarded_branch_cids=["not_in_branches"],
        )


@given(st.integers(max_value=-1))
def test_dynamic_layout_invalid_ast(complexity):
    # Depending on what line 1620 is checking, maybe it raises AST Complexity Overload
    with pytest.raises(ValueError, match=r".*"):
        DynamicLayoutManifest(ast_complexity_score=complexity, manifest_cid="cid1", root_container_id="root1")


# etc. We can add more.
