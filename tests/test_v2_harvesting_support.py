from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    CollaborationConfig,
    CollaborationMode,
    OptimizationIntent,
    PolicyConfig,
    RecipeDefinition,
)
from coreason_manifest.spec.simulation import SimulationScenario, ValidationLogic
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData, ProvenanceType

def test_optimization_harvesting() -> None:
    """Verify Foundry attributes."""
    intent = OptimizationIntent(
        base_ref="old-v1",
        improvement_goal="Fix bugs",
        metric_name="faithfulness",
        teacher_model="gpt-4-turbo",
        max_demonstrations=3
    )
    assert intent.metric_name == "faithfulness"
    assert intent.max_demonstrations == 3

def test_collaboration_harvesting() -> None:
    """Verify Human-Layer attributes."""
    collab = CollaborationConfig(
        mode=CollaborationMode.INTERACTIVE,
        channels=["slack", "email"],
        timeout_seconds=3600,
        fallback_behavior="escalate"
    )
    assert "slack" in collab.channels
    assert collab.timeout_seconds == 3600

def test_policy_harvesting() -> None:
    """Verify Connect attributes."""
    policy = PolicyConfig(
        budget_cap_usd=50.00,
        sensitive_tools=["buy_stock", "delete_db"]
    )
    assert policy.budget_cap_usd == 50.0
    assert "delete_db" in policy.sensitive_tools

def test_simulation_harvesting() -> None:
    """Verify Simulacrum attributes embedded in Recipe."""
    scenario = SimulationScenario(
        id="test-1",
        description="Basic happy path",
        inputs={"q": "hello"},
        validation_logic=ValidationLogic.EXACT_MATCH
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(
            name="Test Recipe",
            provenance=ProvenanceData(type=ProvenanceType.HUMAN)
        ),
        interface={},
        tests=[scenario],
        topology=[
            AgentNode(id="step-1", agent_ref="agent-1")
        ]
    )

    assert len(recipe.tests) == 1
    assert recipe.tests[0].id == "test-1"
