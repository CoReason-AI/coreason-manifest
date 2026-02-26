from coreason_manifest.builder import AgentBuilder, NewLinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode
from coreason_manifest.spec.core.resilience import EscalationStrategy
from coreason_manifest.spec.core.co_intelligence import EscalationCriteria

def test_agent_builder_co_intelligence():
    builder = AgentBuilder("agent_1")
    builder.with_identity(role="assistant", persona="you are helpful")
    builder.with_human_steering(timeout=500)
    builder.with_escalation_rule(condition="x > 5", role="supervisor")

    agent = builder.build()

    assert isinstance(agent, AgentNode)
    assert isinstance(agent.resilience, EscalationStrategy)
    assert agent.resilience.timeout_seconds == 500
    assert agent.resilience.queue_name == "steering_queue"

    assert len(agent.escalation_rules) == 1
    assert agent.escalation_rules[0].condition == "x > 5"
    assert agent.escalation_rules[0].role == "supervisor"

def test_flow_builder_shadow_node():
    flow = NewLinearFlow("test_flow", "0.0.1", "test")
    flow.add_shadow_node(node_id="shadow_human", prompt="Check this", shadow_timeout=120)

    built_flow = flow.build()

    # Locate the node
    shadow_node = next(n for n in built_flow.steps if n.id == "shadow_human")

    assert isinstance(shadow_node, HumanNode)
    assert shadow_node.interaction_mode == "shadow"
    assert shadow_node.prompt == "Check this"
    assert isinstance(shadow_node.escalation, EscalationStrategy)
    assert shadow_node.escalation.timeout_seconds == 120
    assert shadow_node.escalation.queue_name == "shadow_queue"
