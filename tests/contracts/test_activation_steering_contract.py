import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ActivationSteeringContract


# 1. Parameterize Invalid Hashes for Atomicity
@pytest.mark.parametrize(
    ("invalid_hash", "expected_match"),
    [
        ("a" * 63, "String should match pattern"),
        ("a" * 65, "String should match pattern"),
        ("A" * 64, "String should match pattern"),  # Uppercase rejection
        ("g" * 64, "String should match pattern"),  # Non-hex character rejection
    ],
)
def test_activation_steering_contract_cryptographic_bounds(invalid_hash: str, expected_match: str) -> None:
    with pytest.raises(ValidationError, match=expected_match):
        ActivationSteeringContract(
            steering_vector_hash=invalid_hash,
            injection_layers=[5],
            scaling_factor=1.0,
            vector_modality="additive",
        )


# 2. Fuzz the sorting determinism
@given(layers=st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=50))
def test_activation_steering_contract_deterministic_sort(layers: list[int]) -> None:
    """Prove the contract mathematically collapses arbitrary layers into sorted deterministic state."""
    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64,
        injection_layers=layers,
        scaling_factor=2.5,
        vector_modality="additive",
    )

    assert contract.injection_layers == sorted(layers)
