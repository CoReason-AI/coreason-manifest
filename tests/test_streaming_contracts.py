import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.capabilities import AgentCapabilities, CapabilityType, DeliveryMode


def test_streaming_contracts_defaults() -> None:
    """Verify default values for streaming contracts."""
    caps = AgentCapabilities()
    assert caps.type == CapabilityType.GRAPH
    assert caps.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert caps.history_support is True


def test_streaming_contracts_explicit_configuration() -> None:
    """Verify explicit configuration of streaming contracts."""
    caps = AgentCapabilities(type=CapabilityType.ATOMIC, delivery_mode=DeliveryMode.SERVER_SENT_EVENTS)
    assert caps.type == CapabilityType.ATOMIC
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS


def test_streaming_contracts_immutability() -> None:
    """Verify that AgentCapabilities is immutable."""
    caps = AgentCapabilities()

    with pytest.raises(ValidationError):
        setattr(caps, "delivery_mode", DeliveryMode.SERVER_SENT_EVENTS)  # noqa: B010

    with pytest.raises(ValidationError):
        setattr(caps, "type", CapabilityType.ATOMIC)  # noqa: B010


def test_streaming_contracts_serialization() -> None:
    """Verify JSON serialization of streaming contracts."""
    caps = AgentCapabilities(type=CapabilityType.ATOMIC, delivery_mode=DeliveryMode.SERVER_SENT_EVENTS)
    json_output = caps.model_dump_json()
    assert '"atomic"' in json_output
    assert '"server_sent_events"' in json_output
