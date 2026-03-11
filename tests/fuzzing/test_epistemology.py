from typing import Any

import hypothesis.strategies as st
from hypothesis import given

from coreason_manifest.spec.ontology import ExecutionNodeReceipt, LatentScratchpadReceipt, ThoughtBranchState
from coreason_manifest.utils.algebra import verify_merkle_proof

scalar_st = st.one_of(
    st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text()
)
complex_st = st.recursive(
    scalar_st, lambda c: st.one_of(st.lists(c, max_size=5), st.dictionaries(st.text(), c, max_size=5)), max_leaves=10
)


@given(inputs=complex_st, outputs=complex_st)
def test_tamper_evident_shatter_protocol(inputs: Any, outputs: Any) -> None:
    """The Shatter Protocol: Mutate a nested dict value and assert verify_merkle_proof collapses to False."""
    from hypothesis import assume

    assume(outputs != "tampered_data")

    n1 = ExecutionNodeReceipt(request_id="req_1", inputs=inputs, outputs=outputs, parent_hashes=[])

    """AGENT INSTRUCTION: Explicitly assert node_hash is not None for the parent_hashes parameter,
    because mypy thinks it could be None, but ExecutionNodeReceipt sets it to a string."""
    assert n1.node_hash is not None
    n2 = ExecutionNodeReceipt(request_id="req_2", inputs="hop2", outputs="hop2", parent_hashes=[n1.node_hash])

    assert n2.node_hash is not None
    n3 = ExecutionNodeReceipt(request_id="req_3", inputs="hop3", outputs="hop3", parent_hashes=[n2.node_hash])

    trace = [n1, n2, n3]
    assert verify_merkle_proof(trace) is True

    """AGENT INSTRUCTION: Force bypass of frozen model to simulate physical memory corruption."""
    object.__setattr__(n1, "outputs", "tampered_data")

    import pytest

    from coreason_manifest.spec.ontology import TamperFaultEvent

    with pytest.raises(TamperFaultEvent):
        verify_merkle_proof(trace)


def test_latent_scratchpad_trace_sorting_determinism() -> None:
    """Prove that object arrays are deterministically sorted by their specific lambda key."""
    b1 = ThoughtBranchState(branch_id="branch_Z", latent_content_hash="a" * 64)
    b2 = ThoughtBranchState(branch_id="branch_A", latent_content_hash="b" * 64)

    trace = LatentScratchpadReceipt(
        trace_id="trace_1",
        explored_branches=[b1, b2],
        discarded_branches=["branch_Z", "branch_A"],
        total_latent_tokens=100,
    )
    assert trace.discarded_branches == ["branch_A", "branch_Z"]
    assert trace.explored_branches[0].branch_id == "branch_A"
