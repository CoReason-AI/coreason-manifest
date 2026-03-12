import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import QuorumPolicy


def test_quorum_policy_bft_math() -> None:
    # Valid BFT Math: N = 4, f = 1 -> N >= 3(1) + 1 -> 4 >= 4 (Valid)
    policy_valid = QuorumPolicy(
        max_tolerable_faults=1,
        min_quorum_size=4,
        state_validation_metric="ledger_hash",
        byzantine_action="quarantine",
    )
    assert policy_valid.min_quorum_size == 4
    assert policy_valid.max_tolerable_faults == 1

    # Invalid BFT Math: N = 3, f = 1 -> N >= 3(1) + 1 -> 3 >= 4 (Invalid)
    with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1\."):
        QuorumPolicy(
            max_tolerable_faults=1,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )
