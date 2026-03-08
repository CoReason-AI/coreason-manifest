import pytest
from pydantic import ValidationError

from coreason_manifest.state.persistence import ContinuousMutationPolicy


def test_continuous_mutation_policy_valid() -> None:
    policy = ContinuousMutationPolicy(
        mutation_paradigm="append_only",
        max_uncommitted_rows=5000,
        micro_batch_interval_ms=1000,
    )
    assert policy.max_uncommitted_rows == 5000


def test_continuous_mutation_policy_oom_prevention() -> None:
    with pytest.raises(ValidationError, match="max_uncommitted_rows must be <= 10000"):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only",
            max_uncommitted_rows=15000,
            micro_batch_interval_ms=1000,
        )


def test_continuous_mutation_policy_mor_allows_larger_bounds() -> None:
    policy = ContinuousMutationPolicy(
        mutation_paradigm="merge_on_read",
        max_uncommitted_rows=50000,
        micro_batch_interval_ms=5000,
    )
    assert policy.max_uncommitted_rows == 50000
