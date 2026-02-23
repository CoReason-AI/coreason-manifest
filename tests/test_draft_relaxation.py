from coreason_manifest.spec.core.flow import (
    DataSchema,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.utils.validator import validate_flow

def test_draft_relaxation_semantics() -> None:
    """
    Verify that Phase 3 refactor correctly relaxes semantic checks for draft flows
    while enforcing them for published flows.
    """
    # 1. Create a flow with missing tool reference
    brain = CognitiveProfile(role="assistant", persona="helper")
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"], # Semantic error
        metadata={},
        resilience=None,
    )
    graph = Graph(nodes={"agent-1": agent}, edges=[], entry_point="agent-1")

    # 2. Assert Draft is Valid (Relaxed)
    flow_draft = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test", version="1.0.0"),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    errors_draft = validate_flow(flow_draft)
    assert errors_draft == [], f"Draft flow should have no errors, but got: {errors_draft}"

    # 3. Assert Published is Invalid (Strict)
    flow_pub = flow_draft.model_copy(update={"status": "published"})
    errors_pub = validate_flow(flow_pub)
    assert any("requires tool 'missing-tool'" in e for e in errors_pub), "Published flow should detect missing tool"

def test_draft_relaxation_governance() -> None:
    """
    Verify governance validation (fallback references) is relaxed for drafts.
    """
    from coreason_manifest.spec.core.governance import CircuitBreaker, Governance

    # Governance with invalid fallback
    gov = Governance(
        circuit_breaker=CircuitBreaker(
            error_threshold_count=5,
            reset_timeout_seconds=60,
            fallback_node_id="missing_node" # Semantic error
        )
    )

    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile=CognitiveProfile(role="r", persona="p"),
        tools=[],
        metadata={},
        resilience=None,
    )

    graph = Graph(nodes={"agent-1": agent}, edges=[], entry_point="agent-1")

    # Draft
    flow_draft = GraphFlow(
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="test_gov", version="1.0.0"),
        governance=gov,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    errors_draft = validate_flow(flow_draft)
    # The guardrails require governance validation to run on all states, including drafts.
    # So we expect the Circuit Breaker Error even in draft mode.
    assert any("Circuit Breaker Error" in e and "missing_node" in e for e in errors_draft)

    # Published
    flow_pub = flow_draft.model_copy(update={"status": "published"})
    errors_pub = validate_flow(flow_pub)
    assert any("Circuit Breaker Error" in e and "missing_node" in e for e in errors_pub)
