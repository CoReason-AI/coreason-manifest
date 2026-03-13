from typing import Any

import hypothesis.strategies as st
from hypothesis import given
from pydantic import TypeAdapter

from coreason_manifest.spec.ontology import (
    AnyIntent,
    ExecutionNodeReceipt,
    LatentProjectionIntent,
    LatentScratchpadReceipt,
    ThoughtBranchState,
)
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


@st.composite
def draw_latent_projection_intent(draw: st.DrawFn) -> dict[str, Any]:
    context_expansion_st = st.one_of(
        st.none(),
        st.fixed_dictionaries(
            {
                "expansion_paradigm": st.sampled_from(["sliding_window", "hierarchical_merge", "document_summary"]),
                "max_token_budget": st.integers(min_value=1),
                "surrounding_sentences_k": st.one_of(st.none(), st.integers(min_value=1)),
                "parent_merge_threshold": st.one_of(
                    st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
                ),
            }
        ),
    )

    topological_bounds_st = st.one_of(
        st.none(),
        st.fixed_dictionaries(
            {
                "max_hop_depth": st.integers(min_value=1),
                "allowed_causal_relationships": st.lists(
                    st.sampled_from(["causes", "confounds", "correlates_with", "undirected"]), min_size=1
                ),
                "enforce_isometry": st.booleans(),
            }
        ),
    )

    vector_embedding_st = st.fixed_dictionaries(
        {
            "vector_base64": st.just("bWFnaWM="),  # Valid base64
            "dimensionality": st.integers(),
            "model_name": st.text(),
        }
    )

    return {
        "type": "latent_projection",
        "synthetic_target_vector": draw(vector_embedding_st),
        "top_k_candidates": draw(st.integers(min_value=1)),
        "min_isometry_score": draw(st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        "topological_bounds": draw(topological_bounds_st),
        "context_expansion": draw(context_expansion_st),
    }


@given(payload=draw_latent_projection_intent())
def test_latent_projection_intent_fuzzing(payload: dict[str, Any]) -> None:
    adapter: TypeAdapter[AnyIntent] = TypeAdapter(AnyIntent)
    intent = adapter.validate_python(payload)

    assert isinstance(intent, LatentProjectionIntent)

    if intent.topological_bounds is not None:
        # Verify deterministic array sorting for mathematical fuzzing
        relationships = payload["topological_bounds"]["allowed_causal_relationships"]
        sorted_relationships = sorted(relationships)
        assert intent.topological_bounds.allowed_causal_relationships == sorted_relationships
