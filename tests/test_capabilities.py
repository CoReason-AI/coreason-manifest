from coreason_manifest.spec.common.capabilities import AgentCapabilities, DeliveryMode, CapabilityType
from coreason_manifest.spec.v2.definitions import AgentDefinition


def test_capabilities_default_init() -> None:
    caps = AgentCapabilities()
    assert caps.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert caps.type == CapabilityType.GRAPH
    assert caps.history_support is True


def test_capabilities_custom_init() -> None:
    caps = AgentCapabilities(
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
        history_support=False,
        type=CapabilityType.ATOMIC
    )
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert caps.history_support is False
    assert caps.type == CapabilityType.ATOMIC


def test_agent_definition_integration() -> None:
    # capabilities in AgentDefinition might be a dict or object.
    # AgentDefinition uses AgentCapabilities model.
    agent = AgentDefinition(
        id="test-agent",
        name="Test Agent",
        role="Tester",
        goal="To test capabilities",
        capabilities=AgentCapabilities(delivery_mode=DeliveryMode.SERVER_SENT_EVENTS)
    )
    assert agent.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert agent.capabilities.history_support is True


def test_serialization() -> None:
    caps = AgentCapabilities()
    dumped = caps.dump()
    assert dumped["delivery_mode"] == "request_response"
    assert dumped["history_support"] is True
