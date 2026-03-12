import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ActivationSteeringContract


def test_activation_steering_contract_valid() -> None:
    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64,
        injection_layers=[12, 5, 8],
        scaling_factor=2.5,
        vector_modality="additive",
    )

    # Check that sorting was applied to injection_layers
    assert contract.injection_layers == [5, 8, 12]
    assert contract.scaling_factor == 2.5
    assert contract.vector_modality == "additive"


def test_activation_steering_contract_invalid_hash() -> None:
    # Hash too short
    with pytest.raises(ValidationError, match="steering_vector_hash"):
        ActivationSteeringContract(
            steering_vector_hash="a" * 63,
            injection_layers=[5],
            scaling_factor=1.0,
            vector_modality="additive",
        )

    # Hash has uppercase characters
    with pytest.raises(ValidationError, match="steering_vector_hash"):
        ActivationSteeringContract(
            steering_vector_hash="A" * 64,
            injection_layers=[5],
            scaling_factor=1.0,
            vector_modality="additive",
        )


def test_activation_steering_contract_invalid_injection_layers() -> None:
    # Array too short (min_length=1)
    with pytest.raises(ValidationError, match="injection_layers"):
        ActivationSteeringContract(
            steering_vector_hash="a" * 64,
            injection_layers=[],
            scaling_factor=1.0,
            vector_modality="additive",
        )


def test_activation_steering_contract_invalid_modality() -> None:
    # Invalid literal
    with pytest.raises(ValidationError, match="vector_modality"):
        ActivationSteeringContract(
            steering_vector_hash="a" * 64,
            injection_layers=[5],
            scaling_factor=1.0,
            vector_modality="multiply",  # type: ignore
        )
