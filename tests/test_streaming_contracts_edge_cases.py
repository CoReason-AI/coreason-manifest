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

from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
)
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2 as Manifest


def test_invalid_enum_values() -> None:
    """Test validation errors for invalid enum values."""
    with pytest.raises(ValidationError) as exc:
        AgentCapabilities(type="super_complex")  # type: ignore
    assert "Input should be 'atomic' or 'graph'" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        AgentCapabilities(delivery_mode="websocket")  # type: ignore
    assert "Input should be 'request_response' or 'server_sent_events'" in str(exc.value)


def test_legacy_list_format_failure() -> None:
    """Test that the old list format for delivery_mode raises a clear validation error."""
    with pytest.raises(ValidationError) as exc:
        AgentCapabilities(delivery_mode=["sse"])  # type: ignore
    # Pydantic's default error for wrong type
    assert "Input should be 'request_response' or 'server_sent_events'" in str(exc.value)


def test_none_values() -> None:
    """Test that None is not accepted for fields without default None."""
    with pytest.raises(ValidationError):
        AgentCapabilities(type=None)  # type: ignore

    with pytest.raises(ValidationError):
        AgentCapabilities(delivery_mode=None)  # type: ignore


def test_manifest_complex_configurations() -> None:
    """Test Manifest parsing with various capability configurations."""
    manifest_yaml = """
    apiVersion: coreason.ai/v2
    kind: Agent
    metadata:
        name: Complex Test
        version: 1.0.0
    definitions:
        atomic_sse:
            type: agent
            id: atomic_sse
            name: Streamer
            role: Bot
            goal: Chat
            capabilities:
                type: atomic
                delivery_mode: server_sent_events

        graph_req_res:
            type: agent
            id: graph_req_res
            name: Batch Processor
            role: Worker
            goal: Process
            capabilities:
                type: graph
                delivery_mode: request_response

        default_agent:
            type: agent
            id: default_agent
            name: Default
            role: Default
            goal: Default
            # capabilities should use defaults

    workflow:
        start: atomic_sse
        steps:
            atomic_sse:
                type: agent
                id: atomic_sse
                agent: atomic_sse
    """

    # We'll use the load_from_yaml utility indirectly via Model parsing for simplicity
    # or just parse the dict structure if we don't want to write a file.
    # But Manifest expects a dict if passed directly.
    import yaml
    data = yaml.safe_load(manifest_yaml)

    manifest = Manifest(**data)

    # Check Atomic SSE
    atomic_agent = manifest.definitions["atomic_sse"]
    assert isinstance(atomic_agent, AgentDefinition)
    assert atomic_agent.capabilities.type == CapabilityType.ATOMIC
    assert atomic_agent.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS

    # Check Graph Req/Res
    graph_agent = manifest.definitions["graph_req_res"]
    assert isinstance(graph_agent, AgentDefinition)
    assert graph_agent.capabilities.type == CapabilityType.GRAPH
    assert graph_agent.capabilities.delivery_mode == DeliveryMode.REQUEST_RESPONSE

    # Check Defaults
    default_agent = manifest.definitions["default_agent"]
    assert isinstance(default_agent, AgentDefinition)
    # Defaults: Graph, Req/Res
    assert default_agent.capabilities.type == CapabilityType.GRAPH
    assert default_agent.capabilities.delivery_mode == DeliveryMode.REQUEST_RESPONSE


def test_mixed_type_coercion() -> None:
    """Test that valid strings are coerced to Enums correctly."""
    caps = AgentCapabilities(
        type="atomic",
        delivery_mode="server_sent_events"
    )
    assert caps.type == CapabilityType.ATOMIC
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert isinstance(caps.type, CapabilityType)
    assert isinstance(caps.delivery_mode, DeliveryMode)
