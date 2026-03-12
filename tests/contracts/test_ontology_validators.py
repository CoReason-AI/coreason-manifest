import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BrowserDOMState,
    ConsensusPolicy,
    CoreasonBaseState,
    LatentSmoothingProfile,
    QuorumPolicy,
    RiskLevelPolicy,
    SaeLatentPolicy,
    SpatialBoundingBoxProfile,
)


def test_risk_level_policy_weight() -> None:
    """Test the weight property of RiskLevelPolicy."""
    assert RiskLevelPolicy.SAFE.weight == 0
    assert RiskLevelPolicy.STANDARD.weight == 1
    assert RiskLevelPolicy.CRITICAL.weight == 2


def test_coreason_base_state_hash() -> None:
    """Test the _cached_hash caching mechanism on CoreasonBaseState."""

    class DummyState(CoreasonBaseState):
        value: str

    state = DummyState(value="test")

    # First call computes the hash
    h1 = hash(state)

    # Second call returns the cached hash
    h2 = hash(state)

    assert h1 == h2
    assert hasattr(state, "_cached_hash")


def test_spatial_coordinate_state_geometry() -> None:
    """Test SpatialBoundingBoxProfile limits testing x and y boundaries."""
    # Valid geometry
    state = SpatialBoundingBoxProfile(x_min=0.1, x_max=0.5, y_min=0.2, y_max=0.8)
    assert state.x_min == 0.1
    assert state.y_max == 0.8

    # Invalid x geometry
    with pytest.raises(ValidationError, match=r"x_min cannot be strictly greater than x_max\."):
        SpatialBoundingBoxProfile(x_min=0.6, x_max=0.5, y_min=0.2, y_max=0.8)

    # Invalid y geometry
    with pytest.raises(ValidationError, match=r"y_min cannot be strictly greater than y_max\."):
        SpatialBoundingBoxProfile(x_min=0.1, x_max=0.5, y_min=0.9, y_max=0.8)


def test_quorum_rules_policy_bft_math() -> None:
    """Test Byzantine Fault Tolerance validators enforcing mathematically rigorous size bounds."""
    # Valid BFT setup (N >= 3f + 1, so 4 >= 3*1 + 1)
    policy = QuorumPolicy(
        min_quorum_size=4, max_tolerable_faults=1, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )
    assert policy.min_quorum_size == 4

    # Invalid BFT setup (3 < 3*1 + 1)
    with pytest.raises(ValidationError, match=r"Byzantine Fault Tolerance requires min_quorum_size \(N\) >= 3f \+ 1\."):
        QuorumPolicy(
            min_quorum_size=3,
            max_tolerable_faults=1,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )


def test_consensus_policy_pbft_requirements() -> None:
    """Test pbft strategy requires quorum_rules."""
    quorum = QuorumPolicy(
        min_quorum_size=4, max_tolerable_faults=1, state_validation_metric="ledger_hash", byzantine_action="quarantine"
    )

    # Valid pbft setup
    policy = ConsensusPolicy(strategy="pbft", quorum_rules=quorum)
    assert policy.strategy == "pbft"

    # Invalid pbft setup (missing quorum_rules)
    with pytest.raises(ValidationError, match=r"quorum_rules must be provided when strategy is 'pbft'\."):
        ConsensusPolicy(strategy="pbft")


def test_sae_latent_policy_smooth_decay() -> None:
    """Test violation action smooth_decay constraints."""
    profile = LatentSmoothingProfile(decay_function="exponential", transition_window_tokens=10, decay_rate_param=0.5)

    # Valid smooth_decay setup
    policy = SaeLatentPolicy(
        target_feature_index=1,
        monitored_layers=[1],
        max_activation_threshold=0.5,
        violation_action="smooth_decay",
        sae_dictionary_hash="a" * 64,
        smoothing_profile=profile,
        clamp_value=0.1,
    )
    assert policy.violation_action == "smooth_decay"

    # Invalid smooth_decay setup (missing smoothing_profile)
    with pytest.raises(
        ValidationError, match=r"smoothing_profile must be provided when violation_action is 'smooth_decay'\."
    ):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=0.5,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            clamp_value=0.1,
        )

    # Invalid smooth_decay setup (missing clamp_value)
    with pytest.raises(
        ValidationError,
        match=r"clamp_value must be provided as the target asymptote when violation_action is 'smooth_decay'\.",
    ):
        SaeLatentPolicy(
            target_feature_index=1,
            monitored_layers=[1],
            max_activation_threshold=0.5,
            violation_action="smooth_decay",
            sae_dictionary_hash="a" * 64,
            smoothing_profile=profile,
        )


def test_browser_dom_state_ssrf() -> None:
    """Test BrowserDOMState._enforce_spatial_safety for SSRF protection."""
    # Valid URL
    state = BrowserDOMState(
        current_url="https://example.com", viewport_size=(1920, 1080), dom_hash="123", accessibility_tree_hash="456"
    )
    assert state.current_url == "https://example.com"

    # Localhost forbidden
    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="http://localhost:8080",
            viewport_size=(1920, 1080),
            dom_hash="123",
            accessibility_tree_hash="456",
        )

    # Internal IP forbidden
    with pytest.raises(ValidationError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://192.168.1.1", viewport_size=(1920, 1080), dom_hash="123", accessibility_tree_hash="456"
        )

    # file:// scheme forbidden
    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="file:///etc/passwd", viewport_size=(1920, 1080), dom_hash="123", accessibility_tree_hash="456"
        )

    # IP in hex forbidden
    with pytest.raises(ValidationError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url="http://0x7f000001", viewport_size=(1920, 1080), dom_hash="123", accessibility_tree_hash="456"
        )

    # Local TLD forbidden
    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="http://server.local", viewport_size=(1920, 1080), dom_hash="123", accessibility_tree_hash="456"
        )
