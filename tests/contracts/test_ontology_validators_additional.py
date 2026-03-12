import pytest

from coreason_manifest.spec.ontology import (
    ActivationSteeringContract,
    AdjudicationRubricProfile,
    ComputeEngineProfile,
    ComputeRateContract,
    DynamicLayoutManifest,
    GradingCriterionProfile,
    PermissionBoundaryPolicy,
    RedactionPolicy,
)


def test_dynamic_layout_manifest_valid() -> None:
    """Test valid t-strings with allowed AST nodes."""
    manifest = DynamicLayoutManifest(layout_tstring="f'Valid {name}'")
    assert manifest.layout_tstring == "f'Valid {name}'"

    manifest2 = DynamicLayoutManifest(layout_tstring="'Just a constant string'")
    assert manifest2.layout_tstring == "'Just a constant string'"


def test_dynamic_layout_manifest_syntax_error() -> None:
    """Test t-strings that cause SyntaxError (which are just regular strings ignoring ast parsing)."""
    manifest = DynamicLayoutManifest(layout_tstring="This is just a random invalid python syntax string")
    assert manifest.layout_tstring == "This is just a random invalid python syntax string"


def test_dynamic_layout_manifest_kinetic_bleed() -> None:
    """Test t-strings that contain forbidden AST nodes (like ast.Call)."""
    with pytest.raises(ValueError, match="Kinetic execution bleed detected"):
        DynamicLayoutManifest(layout_tstring="f'{os.system(\"rm -rf /\")}'")


def test_compute_engine_profile_sorting() -> None:
    """Test that capabilities and supported_functional_experts are sorted deterministically."""
    rate = ComputeRateContract(
        cost_per_million_input_tokens=1.0,
        cost_per_million_output_tokens=2.0,
        magnitude_unit="USD",
    )
    profile = ComputeEngineProfile(
        model_name="test-model",
        provider="test-provider",
        context_window_size=8192,
        capabilities=["write", "read", "execute", "analyze"],
        supported_functional_experts=["synthesizer", "falsifier", "coder"],
        rate_card=rate,
    )

    assert profile.capabilities == ["analyze", "execute", "read", "write"]
    assert profile.supported_functional_experts == ["coder", "falsifier", "synthesizer"]


def test_permission_boundary_policy_sorting() -> None:
    """Test that allowed_domains and auth_requirements are sorted deterministically."""
    policy = PermissionBoundaryPolicy(
        network_access=True,
        file_system_mutation_forbidden=True,
        allowed_domains=["z-domain.com", "a-domain.com", "m-domain.com"],
        auth_requirements=["oauth2:google", "mtls:internal", "basic:auth"],
    )

    assert policy.allowed_domains == ["a-domain.com", "m-domain.com", "z-domain.com"]
    assert policy.auth_requirements == ["basic:auth", "mtls:internal", "oauth2:google"]


def test_permission_boundary_policy_none() -> None:
    """Test that allowed_domains and auth_requirements handle None correctly without sorting errors."""
    policy = PermissionBoundaryPolicy(
        network_access=False,
        file_system_mutation_forbidden=True,
        allowed_domains=None,
        auth_requirements=None,
    )

    assert policy.allowed_domains is None
    assert policy.auth_requirements is None


def test_activation_steering_contract_sorting() -> None:
    contract = ActivationSteeringContract(
        steering_vector_hash="a" * 64, injection_layers=[10, 2, 5], scaling_factor=1.5, vector_modality="additive"
    )
    assert contract.injection_layers == [2, 5, 10]


def test_adjudication_rubric_profile_sorting() -> None:
    c1 = GradingCriterionProfile(criterion_id="c_beta", description="Beta criterion", weight=10.0)
    c2 = GradingCriterionProfile(criterion_id="c_alpha", description="Alpha criterion", weight=5.0)
    rubric = AdjudicationRubricProfile(rubric_id="rubric1", criteria=[c1, c2], passing_threshold=15.0)
    assert rubric.criteria[0].criterion_id == "c_alpha"
    assert rubric.criteria[1].criterion_id == "c_beta"


def test_redaction_policy_sorting() -> None:
    from coreason_manifest.spec.ontology import InformationClassificationProfile

    policy = RedactionPolicy(
        rule_id="r1",
        classification=InformationClassificationProfile.PUBLIC,
        target_pattern="email",
        target_regex_pattern=".*",
        context_exclusion_zones=["/path/z", "/path/a"],
        action="redact",
    )
    assert policy.context_exclusion_zones == ["/path/a", "/path/z"]
