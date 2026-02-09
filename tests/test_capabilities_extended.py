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

from coreason_manifest import AgentCapabilities, AgentDefinition, DeliveryMode, Manifest


def test_edge_case_invalid_delivery_mode() -> None:
    """Test that invalid strings raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        AgentCapabilities(delivery_mode="invalid_mode")
    assert "Input should be 'request_response' or 'server_sent_events'" in str(exc.value)


def test_strictness_extra_fields() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError) as exc:
        AgentCapabilities(extra_field="fail")  # type: ignore[call-arg]
    assert "Extra inputs are not permitted" in str(exc.value)


def test_immutability_deep() -> None:
    """Test that the model is truly frozen."""
    caps = AgentCapabilities()

    # Direct assignment - use setattr to bypass mypy read-only check but trigger runtime validation
    with pytest.raises(ValidationError):
        setattr(caps, "history_support", False)  # noqa: B010

    # Re-assigning the field should fail
    with pytest.raises(ValidationError):
        setattr(caps, "delivery_mode", DeliveryMode.SERVER_SENT_EVENTS)  # noqa: B010


def test_manifest_roundtrip_with_capabilities() -> None:
    """Test full integration with ManifestV2 serialization."""
    manifest_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Test Agent", "version": "1.0.0"},
        "definitions": {
            "my_agent": {
                "type": "agent",
                "id": "my_agent",
                "name": "My Agent",
                "role": "Assistant",
                "goal": "Help",
                "capabilities": {"delivery_mode": "request_response", "history_support": False},
            }
        },
        "workflow": {"start": "step1", "steps": {"step1": {"type": "agent", "id": "step1", "agent": "my_agent"}}},
    }

    # Load
    manifest = Manifest(**manifest_data)

    # Verify
    agent_def = manifest.definitions["my_agent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.capabilities.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert agent_def.capabilities.history_support is False

    # Dump
    dumped = manifest.model_dump(mode='json', by_alias=True, exclude_none=True)

    # Verify Dump
    agent_dump = dumped["definitions"]["my_agent"]
    assert agent_dump["capabilities"]["delivery_mode"] == "request_response"
    assert agent_dump["capabilities"]["history_support"] is False
