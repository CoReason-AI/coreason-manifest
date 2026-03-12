import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ComputeEngineProfile,
    ComputeRateContract,
    CoreasonBaseState,
    InformationClassificationProfile,
    RiskLevelPolicy,
    SaeLatentPolicy,
    SemanticSlicingPolicy,
)


def test_risk_level_policy_weight() -> None:
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2


def test_coreason_base_state_cached_hash() -> None:
    class DummyState(CoreasonBaseState):
        name: str

    state = DummyState(name="test")
    # First hash computes and caches
    h1 = hash(state)
    # Second hash retrieves from cache
    h2 = hash(state)
    assert h1 == h2
    assert hasattr(state, "_cached_hash")
    assert state._cached_hash == h1


def test_compute_engine_profile_sort_arrays() -> None:
    rate_card = ComputeRateContract(
        cost_per_million_input_tokens=0.01, cost_per_million_output_tokens=0.02, magnitude_unit="USD"
    )
    profile = ComputeEngineProfile(
        model_name="test",
        provider="test",
        context_window_size=1024,
        capabilities=["c", "a", "b"],
        rate_card=rate_card,
        supported_functional_experts=["z", "x", "y"],
    )
    assert profile.capabilities == ["a", "b", "c"]
    assert profile.supported_functional_experts == ["x", "y", "z"]


def test_semantic_slicing_policy_sort_arrays() -> None:
    policy = SemanticSlicingPolicy(
        permitted_classification_tiers=[
            InformationClassificationProfile.RESTRICTED,
            InformationClassificationProfile.PUBLIC,
        ],
        required_semantic_labels=["b", "a"],
        context_window_token_ceiling=100,
    )
    assert policy.permitted_classification_tiers == [
        InformationClassificationProfile.PUBLIC,
        InformationClassificationProfile.RESTRICTED,
    ]
    assert policy.required_semantic_labels == ["a", "b"]


def test_sae_latent_policy_smooth_decay_validation() -> None:
    # Missing smoothing profile
    with pytest.raises(ValidationError) as exc_info:
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=1.0,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            clamp_value=0.1,
            smoothing_profile=None,
        )
    assert "smoothing_profile must be provided" in str(exc_info.value)
