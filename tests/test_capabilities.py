# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.capabilities import AgentCapabilities, DeliveryMode
from coreason_manifest.v2.spec.definitions import AgentDefinition


def test_capabilities_default_init() -> None:
    caps = AgentCapabilities()
    assert caps.delivery_mode == [DeliveryMode.SSE]
    assert caps.history_support is True


def test_capabilities_custom_init() -> None:
    caps = AgentCapabilities(delivery_mode=[DeliveryMode.REQUEST_RESPONSE], history_support=False)
    assert caps.delivery_mode == [DeliveryMode.REQUEST_RESPONSE]
    assert caps.history_support is False


def test_agent_definition_integration() -> None:
    agent = AgentDefinition(id="test-agent", name="Test Agent", role="Tester", goal="To test capabilities")
    assert agent.capabilities.delivery_mode == [DeliveryMode.SSE]
    assert agent.capabilities.history_support is True


def test_serialization() -> None:
    caps = AgentCapabilities()
    dumped = caps.dump()
    assert dumped["delivery_mode"] == ["sse"]
    assert dumped["history_support"] is True
