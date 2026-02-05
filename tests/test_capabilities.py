from coreason_manifest.spec.common.capabilities import AgentCapabilities, DeliveryMode
from coreason_manifest.spec.v2.definitions import AgentDefinition


def test_capabilities_default_init() -> None:
    caps = AgentCapabilities()
    assert caps.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert caps.history_support is True


def test_capabilities_custom_init() -> None:
    caps = AgentCapabilities(
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS, history_support=False
    )
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert caps.history_support is False


def test_agent_definition_integration() -> None:
    agent = AgentDefinition(
        id="test-agent", name="Test Agent", role="Tester", goal="To test capabilities"
    )
    assert agent.capabilities.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert agent.capabilities.history_support is True


def test_serialization() -> None:
    caps = AgentCapabilities()
    dumped = caps.dump()
    assert dumped["delivery_mode"] == "request_response"
    assert dumped["history_support"] is True
