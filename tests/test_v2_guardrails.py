# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.guardrails import (
    BreakerScope,
    CircuitBreakerConfig,
    DriftConfig,
    GuardrailsConfig,
)
from coreason_manifest.spec.v2.recipe import (
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    GraphTopology,
    AgentNode,
    GraphEdge,
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata

def test_circuit_breaker_config():
    """Test CircuitBreakerConfig instantiation and validation."""
    config = CircuitBreakerConfig(
        failure_rate_threshold=0.2,
        window_seconds=120,
        recovery_timeout_seconds=600,
        scope=BreakerScope.RECIPE
    )
    assert config.failure_rate_threshold == 0.2
    assert config.window_seconds == 120
    assert config.recovery_timeout_seconds == 600
    assert config.scope == BreakerScope.RECIPE

def test_drift_config():
    """Test DriftConfig instantiation."""
    config = DriftConfig(
        input_drift_threshold=0.15,
        output_drift_threshold=0.25,
        baseline_dataset_id="dataset-xyz"
    )
    assert config.input_drift_threshold == 0.15
    assert config.output_drift_threshold == 0.25
    assert config.baseline_dataset_id == "dataset-xyz"

def test_guardrails_config_defaults():
    """Test GuardrailsConfig default values."""
    config = GuardrailsConfig()
    assert config.circuit_breaker is None
    assert config.drift_check is None
    assert config.spot_check_rate == 0.0

def test_recipe_definition_integration():
    """Test integrating GuardrailsConfig into RecipeDefinition."""
    guardrails = GuardrailsConfig(
        circuit_breaker=CircuitBreakerConfig(
            failure_rate_threshold=0.5,
            scope=BreakerScope.AGENT
        ),
        drift_check=DriftConfig(
            input_drift_threshold=0.1
        ),
        spot_check_rate=0.05
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Test Recipe", version="1.0.0"),
        status=RecipeStatus.DRAFT,
        interface=RecipeInterface(),
        guardrails=guardrails,
        topology=GraphTopology(
            nodes=[AgentNode(id="agent-1", agent_ref="agent-lib/v1/test-agent")],
            edges=[],
            entry_point="agent-1"
        )
    )

    assert recipe.guardrails is not None
    assert recipe.guardrails.spot_check_rate == 0.05
    assert recipe.guardrails.circuit_breaker.failure_rate_threshold == 0.5
    assert recipe.guardrails.drift_check.input_drift_threshold == 0.1

    # Verify serialization
    dumped = recipe.dump()
    assert "guardrails" in dumped
    assert dumped["guardrails"]["spot_check_rate"] == 0.05
    assert dumped["guardrails"]["circuit_breaker"]["scope"] == "agent"
