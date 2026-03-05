import random
from typing import Any

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.telemetry.custody import ExecutionNode, verify_merkle_proof

# Strategy to generate scalar JSON-like values
scalar_st = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)

# Complex deep JSON-like objects (dicts, lists, sets)
complex_st = st.recursive(
    scalar_st,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(), children, max_size=5),
        st.sets(st.one_of(st.integers(), st.text(), st.booleans()), max_size=5),  # Sets need hashable items
    ),
    max_leaves=10,
)


@given(payload=complex_st)
def test_determinism_proof(payload: Any) -> None:
    """
    1. The Determinism Proof:
    Prove that generating a hash for a deeply nested, randomly generated execution
    payload yields the exact same SHA-256 string 100 out of 100 times.
    """
    node = ExecutionNode(request_id="req_1", inputs=payload, outputs=payload, parent_hashes=[])

    expected_hash = node.generate_node_hash()

    for _ in range(100):
        assert node.generate_node_hash() == expected_hash


@given(inputs=complex_st, outputs=complex_st)
def test_tamper_evident_proof(inputs: Any, outputs: Any) -> None:
    """
    2. The Tamper Evident Proof (The Shatter Protocol):
    Generate a valid 3-hop Merkle trace. Explicitly mutate a single byte of data
    in the outputs dictionary of Node 1. Prove that passing this mutated trace to
    verify_merkle_proof decisively returns False because the downstream parent hashes shatter.
    """
    assume(outputs != "tampered_data")
    n1 = ExecutionNode(request_id="req_1", inputs=inputs, outputs=outputs, parent_hashes=[])
    assert n1.node_hash is not None
    n2 = ExecutionNode(request_id="req_2", inputs="hop2", outputs="hop2", parent_hashes=[n1.node_hash])
    assert n2.node_hash is not None
    n3 = ExecutionNode(request_id="req_3", inputs="hop3", outputs="hop3", parent_hashes=[n2.node_hash])

    trace = [n1, n2, n3]
    assert verify_merkle_proof(trace) is True

    # Force mutation bypassing Pydantic validation and our node_hash generation
    object.__setattr__(n1, "outputs", "tampered_data")

    # n1's computed hash will now differ from its asserted node_hash, OR if it recomputed,
    # n2's parent_hashes would not contain the newly computed hash. Both break the chain.
    assert verify_merkle_proof(trace) is False


@given(inputs=complex_st, outputs=complex_st)
def test_temporal_shuffle_proof(inputs: Any, outputs: Any) -> None:
    """
    3. The Temporal Shuffle Proof:
    Take a valid multi-hop trace, violently shuffle the array order using random.shuffle(),
    and pass it to the verifier. Prove that the verifier successfully validates the chain
    regardless of arrival order.
    """
    n1 = ExecutionNode(request_id="req_1", inputs=inputs, outputs=outputs, parent_hashes=[])
    assert n1.node_hash is not None
    n2 = ExecutionNode(request_id="req_2", inputs="hop2", outputs="hop2", parent_hashes=[n1.node_hash])
    assert n2.node_hash is not None
    n3 = ExecutionNode(request_id="req_3", inputs="hop3", outputs="hop3", parent_hashes=[n2.node_hash])
    n4 = ExecutionNode(request_id="req_4", inputs="hop4", outputs="hop4", parent_hashes=[n1.node_hash, n2.node_hash])

    trace = [n1, n2, n3, n4]

    for _ in range(10):
        random.shuffle(trace)
        assert verify_merkle_proof(trace) is True


@given(
    ssn=st.from_regex(r"\b\d{3}-\d{2}-\d{4}\b", fullmatch=True),
    api_key=st.from_regex(r"\bAPI_KEY_[a-zA-Z0-9]+\b", fullmatch=True),
)
def test_quarantine_proof(ssn: str, api_key: str) -> None:
    """
    4. The Quarantine Proof:
    Inject a toxic string (e.g., a fake SSN or API key) into a node's payload.
    Prove that the telemetry schemas (PrivacySentinel) redact the string before
    the Merkle hash is calculated, ensuring the hash itself does not become a toxic asset.
    """
    node = ExecutionNode(request_id="req_1", inputs={"secret": ssn}, outputs=[api_key], parent_hashes=[])

    # Assert redaction happened at validation
    assert node.inputs["secret"] == "[REDACTED]"  # noqa: S105
    assert node.outputs[0] == "[REDACTED]"

    # The generated hash should match the hash of the redacted payload
    expected_redacted_node = ExecutionNode(
        request_id="req_1", inputs={"secret": "[REDACTED]"}, outputs=["[REDACTED]"], parent_hashes=[]
    )

    assert node.generate_node_hash() == expected_redacted_node.generate_node_hash()
    assert node.node_hash == expected_redacted_node.node_hash


def test_missing_node_hash_verification() -> None:
    # A node whose hash is wiped out
    n1 = ExecutionNode(request_id="req_1", inputs="a", outputs="b", parent_hashes=[])
    # manually bypass validator and set to None
    object.__setattr__(n1, "node_hash", None)
    assert not verify_merkle_proof([n1])


def test_missing_parent_hash_verification() -> None:
    n1 = ExecutionNode(request_id="req_1", inputs="a", outputs="b", parent_hashes=[])
    # The parent does not exist in the trace
    n2 = ExecutionNode(request_id="req_2", inputs="c", outputs="d", parent_hashes=["missing_hash"])
    assert not verify_merkle_proof([n1, n2])


def test_canonicalize_tuple() -> None:
    # Test tuple canonicalization path
    n1 = ExecutionNode(request_id="req_1", inputs=("a", None, "b"), outputs=(), parent_hashes=[])
    assert n1.node_hash is not None


def test_redact_toxic_tuple_and_other() -> None:
    # Test tuple and non-string scalar types in redaction
    n1 = ExecutionNode(request_id="req_1", inputs=(1, True, "123-45-6789"), outputs=None, parent_hashes=[])
    assert n1.inputs == (1, True, "[REDACTED]")


def test_lineage_orphan_proof() -> None:
    """
    Assert that Pydantic raises a ValidationError due to the model validator
    when parent_request_id is provided but root_request_id is missing.
    """
    with pytest.raises(ValidationError, match="Orphaned Lineage: parent_request_id is set but root_request_id is None"):
        ExecutionNode(
            request_id="req_1",
            parent_request_id="parent_123",
            root_request_id=None,
            inputs="a",
            outputs="b",
            parent_hashes=[],
        )
