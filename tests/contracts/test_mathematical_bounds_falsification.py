import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ComputationalThermodynamicsProfile,
    DistributionProfile,
    MultimodalTokenAnchorState,
    UtilityJustificationGraphReceipt,
)


def test_thermodynamic_bounds_reject_nan() -> None:
    with pytest.raises(ValidationError, match="remaining_free_energy cannot be NaN or Infinity"):
        ComputationalThermodynamicsProfile.model_validate(
            {
                "thermodynamics_cid": "t_001",
                "target_topology_cid": "c_001",
                "max_stochastic_diffusions": 100,
                "computational_free_energy_budget": 10.0,
                "current_diffusions": 1,
                "remaining_free_energy": float("nan"),
            }
        )


def test_spatial_bounds_reject_inf() -> None:
    with pytest.raises(ValidationError, match="Spatial bounds cannot be Infinity"):
        MultimodalTokenAnchorState.model_validate(
            {
                "token_span_start": 0,  # nosec B105
                "token_span_end": 10,  # nosec B105
                "block_class": "paragraph",
                "bounding_box": (0.0, 0.0, float("inf"), 100.0),
                "visual_patch_hashes": [],
            }
        )


def test_spatial_bounds_reject_nan() -> None:
    with pytest.raises(ValidationError, match="Spatial bounds cannot be NaN"):
        MultimodalTokenAnchorState.model_validate(
            {
                "token_span_start": 0,  # nosec B105
                "token_span_end": 10,  # nosec B105
                "block_class": "paragraph",
                "bounding_box": (0.0, float("nan"), 100.0, 100.0),
                "visual_patch_hashes": [],
            }
        )


def test_confidence_interval_contradiction() -> None:
    with pytest.raises(ValidationError, match=r"confidence_interval_95 must have interval(.*)"):
        DistributionProfile.model_validate(
            {"distribution_type": "gaussian", "mean": 0.0, "variance": 1.0, "confidence_interval_95": (1.0, 0.5)}
        )


def test_superposition_variance_zero() -> None:
    obj = UtilityJustificationGraphReceipt.model_construct(
        optimizing_vectors={"a": 1.0},
        degrading_vectors={"b": 1.0},
        ensemble_spec={"concurrent_branch_cids": ["did:example:branch"], "fusion_function": "weighted_consensus"},  # type: ignore[arg-type]
        superposition_variance_threshold=0.0,
    )
    with pytest.raises(ValueError, match=r"variance threshold is 0.0"):
        obj._enforce_mathematical_interlocks()  # type: ignore[operator]


def test_tensor_poisoning_inf() -> None:
    obj = UtilityJustificationGraphReceipt.model_construct(
        optimizing_vectors={"a": float("inf")},
        degrading_vectors={},
        superposition_variance_threshold=0.1,
        ensemble_spec=None,
    )
    with pytest.raises(ValueError, match="Tensor Poisoning Detected"):
        obj._enforce_mathematical_interlocks()  # type: ignore[operator]
