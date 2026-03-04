# Prosperity-3.0
import pytest
from pydantic import ValidationError

from coreason_manifest.spec.intent_protocols import (
    ConstraintConfig,
    GracefulDegradationPolicy,
    UniversalIntentURI,
)
from coreason_manifest.workflow.nodes.liquid import (
    DecompositionStrategy,
    LiquidTopologyNode,
)


def test_liquid_topology_node_inheritance() -> None:
    config = ConstraintConfig(
        max_latency_ms=1000,
        requires_hipaa_compliance=False,
        allowed_compute_regions=["us-west-2"],
    )
    policy = GracefulDegradationPolicy(
        droppable_constraints=["max_latency_ms"],
        fallback_timeout_ms=5000,
        allow_synthetic_bootstrapping=True,
    )

    uri = UniversalIntentURI(
        scheme="ibo",
        ecosystem_target="registry-alpha",
        semantic_payload="Parse these logs",
        constraints=config,
        degradation_policy=policy,
    )
    decomp = DecompositionStrategy(
        max_micro_agents=3,
        allowed_sub_intents=["read", "parse"],
        require_human_oversight_on_synthesis=True,
    )

    node = LiquidTopologyNode(
        id="liquid-node-1",
        macro_intent=uri,
        decomposition=decomp,
        ephemeral_ttl_seconds=3600,
    )
    assert node.id == "liquid-node-1"
    assert node.type == "liquid"
    assert node.macro_intent == uri
    assert node.decomposition == decomp
    assert node.ephemeral_ttl_seconds == 3600


def test_liquid_topology_negative_ttl_validation() -> None:
    config = ConstraintConfig(
        max_latency_ms=1000,
        requires_hipaa_compliance=False,
        allowed_compute_regions=["us-west-2"],
    )
    uri = UniversalIntentURI(
        scheme="local",
        ecosystem_target="local",
        semantic_payload="Test",
        constraints=config,
    )
    decomp = DecompositionStrategy(
        max_micro_agents=2,
        allowed_sub_intents=["test"],
        require_human_oversight_on_synthesis=False,
    )

    with pytest.raises(ValidationError):
        LiquidTopologyNode(
            id="liquid-node-2",
            macro_intent=uri,
            decomposition=decomp,
            ephemeral_ttl_seconds=-5,
        )


def test_decomposition_strategy_max_agents_validation() -> None:
    with pytest.raises(ValidationError):
        DecompositionStrategy(
            max_micro_agents=0,  # Invalid, must be > 0
            allowed_sub_intents=["test"],
            require_human_oversight_on_synthesis=True,
        )
