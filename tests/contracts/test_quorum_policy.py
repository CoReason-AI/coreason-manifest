import hypothesis.strategies as st
import pytest
from hypothesis import assume, given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import QuorumPolicy


# 1. Fuzz the Valid BFT Topology Space
@given(f=st.integers(min_value=0, max_value=10000), buffer=st.integers(min_value=0, max_value=100))
def test_quorum_policy_bft_math_valid(f: int, buffer: int) -> None:
    """Mathematically prove that any N >= 3f + 1 succeeds."""
    n = (3 * f) + 1 + buffer

    policy = QuorumPolicy(
        max_tolerable_faults=f,
        min_quorum_size=n,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )
    assert policy.min_quorum_size == n
    assert policy.max_tolerable_faults == f


# 2. Fuzz the Invalid BFT Topology Space (Quarantine)
@given(f=st.integers(min_value=1, max_value=10000), deficit=st.integers(min_value=1, max_value=1000))
def test_quorum_policy_bft_math_invalid(f: int, deficit: int) -> None:
    """Mathematically prove that any N < 3f + 1 is structurally rejected."""
    n = (3 * f) + 1 - deficit
    # Ensure N doesn't drop below logical limits for Pydantic (e.g., min_size>0 if applicable)
    assume(n >= 1)

    with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1\."):
        QuorumPolicy(
            max_tolerable_faults=f,
            min_quorum_size=n,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
