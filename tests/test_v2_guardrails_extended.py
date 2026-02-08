# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.guardrails import (
    BreakerScope,
    CircuitBreakerConfig,
    DriftConfig,
    GuardrailsConfig,
)
from coreason_manifest.spec.v2.compliance import AuditLevel, ComplianceConfig, RetentionPolicy
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    GraphTopology,
    PolicyConfig,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
)


def test_guardrails_edge_case_invalid_values() -> None:
    """Test that invalid values raise ValidationError."""
    # Circuit Breaker: Failure rate > 1.0
    with pytest.raises(ValidationError):
        CircuitBreakerConfig(
            failure_rate_threshold=1.5,
            window_seconds=60,
            recovery_timeout_seconds=300,
            scope=BreakerScope.RECIPE,
        )

    # Circuit Breaker: Negative failure rate
    with pytest.raises(ValidationError):
        CircuitBreakerConfig(
            failure_rate_threshold=-0.1,
            window_seconds=60,
            recovery_timeout_seconds=300,
            scope=BreakerScope.RECIPE,
        )

    # Guardrails: Spot check rate > 1.0
    with pytest.raises(ValidationError):
        GuardrailsConfig(spot_check_rate=1.1)

    # Guardrails: Spot check rate < 0.0
    with pytest.raises(ValidationError):
        GuardrailsConfig(spot_check_rate=-0.01)


def test_guardrails_edge_case_empty_objects() -> None:
    """Test instantiation with minimal/empty arguments where optional."""
    # DriftConfig with all None
    drift = DriftConfig()
    assert drift.input_drift_threshold is None
    assert drift.output_drift_threshold is None
    assert drift.baseline_dataset_id is None

    # Guardrails with defaults
    guard = GuardrailsConfig()
    assert guard.circuit_breaker is None
    assert guard.drift_check is None
    assert guard.spot_check_rate == 0.0


def test_guardrails_complex_integration() -> None:
    """Test a complex recipe with Policy, Compliance, and Guardrails interacting."""
    guardrails = GuardrailsConfig(
        circuit_breaker=CircuitBreakerConfig(
            failure_rate_threshold=0.3,
            window_seconds=120,
            recovery_timeout_seconds=60,
            scope=BreakerScope.GLOBAL,
        ),
        drift_check=DriftConfig(
            input_drift_threshold=0.2,
            baseline_dataset_id="baseline-v1",
        ),
        spot_check_rate=0.1,
    )

    policy = PolicyConfig(
        max_retries=5,
        timeout_seconds=300,
        execution_mode="parallel",
        sensitive_tools=["tool_a"],
    )

    compliance = ComplianceConfig(
        audit_level=AuditLevel.FULL,
        retention=RetentionPolicy.ONE_YEAR,
        generate_pdf_report=True,
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Recipe", version="2.0.0"),
        status=RecipeStatus.DRAFT,
        interface=RecipeInterface(),
        policy=policy,
        compliance=compliance,
        guardrails=guardrails,
        topology=GraphTopology(
            nodes=[AgentNode(id="start", agent_ref="agent-x")],
            edges=[],
            entry_point="start",
        ),
    )

    # Verification
    assert recipe.guardrails is not None
    assert recipe.guardrails.circuit_breaker is not None
    assert recipe.guardrails.circuit_breaker.scope == BreakerScope.GLOBAL
    assert recipe.guardrails.spot_check_rate == 0.1

    assert recipe.policy is not None
    assert recipe.policy.max_retries == 5

    assert recipe.compliance is not None
    assert recipe.compliance.audit_level == AuditLevel.FULL

    # Hash check (implicit verification of dump stability)
    h1 = recipe.compute_hash()
    h2 = recipe.compute_hash()
    assert h1 == h2


def test_guardrails_serialization_roundtrip() -> None:
    """Test dumping to JSON and validating back."""
    original_guardrails = GuardrailsConfig(
        spot_check_rate=0.5,
        circuit_breaker=CircuitBreakerConfig(
            failure_rate_threshold=0.9,
            window_seconds=10,
            recovery_timeout_seconds=10,
            scope=BreakerScope.AGENT,
        ),
    )

    dumped = original_guardrails.dump()
    assert dumped["spot_check_rate"] == 0.5
    assert dumped["circuit_breaker"]["failure_rate_threshold"] == 0.9

    reloaded = GuardrailsConfig.model_validate(dumped)
    assert reloaded == original_guardrails
