# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import (
    AgentCapabilities,
    AgentDefinition,
    CapabilityType,
    DeliveryMode,
    Manifest,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    StreamOpCode,
    StreamPacket,
)


def test_complex_stream_packet_nesting() -> None:
    """Test a StreamPacket containing a full PresentationEvent with complex data."""
    # 1. Create Data
    carousel = MediaCarousel(
        items=[
            MediaItem(
                url="https://example.com/1.png",
                mime_type="image/png",
                alt_text="Image 1",
            ),
            MediaItem(
                url="https://example.com/2.png",
                mime_type="image/png",
                alt_text="Image 2",
            ),
        ]
    )

    # 2. Wrap in Event
    event = PresentationEvent(type=PresentationEventType.MEDIA_CAROUSEL, data=carousel)

    # 3. Wrap in Stream Packet (simulating wire transport)
    # Note: StreamPacket.p is Union[..., Dict[str, Any]]. We must dump the event.
    packet = StreamPacket(op=StreamOpCode.EVENT, p=event.dump())

    # 4. Assertions
    assert packet.op == StreamOpCode.EVENT
    assert isinstance(packet.p, dict)
    assert packet.p["type"] == "media_carousel"
    assert len(packet.p["data"]["items"]) == 2
    assert packet.p["data"]["items"][1]["alt_text"] == "Image 2"


def test_full_manifest_integration() -> None:
    """Test defining an Agent with specific capabilities in a full Manifest."""
    manifest_yaml = """
    apiVersion: coreason.ai/v2
    kind: Agent
    metadata:
      name: "Complex Agent"
      version: "1.0.0"
    definitions:
      worker:
        type: agent
        id: worker
        name: Worker
        role: Worker
        goal: Work
        capabilities:
          type: atomic
          delivery_mode: server_sent_events
          history_support: false
    workflow:
      start: step1
      steps:
        step1:
          type: agent
          id: step1
          agent: worker
    """

    # Load from YAML string (simulated via dict to avoid yaml parser dep in test if possible,
    # but Manifest accepts dict).
    # Let's construct dict directly to be safe and precise.

    manifest_data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Agent",
        "metadata": {"name": "Complex Agent", "version": "1.0.0"},
        "definitions": {
            "worker": {
                "type": "agent",
                "id": "worker",
                "name": "Worker",
                "role": "Worker",
                "goal": "Work",
                "capabilities": {"type": "atomic", "delivery_mode": "server_sent_events", "history_support": False},
            }
        },
        "workflow": {"start": "step1", "steps": {"step1": {"type": "agent", "id": "step1", "agent": "worker"}}},
    }

    manifest = Manifest(**manifest_data)
    agent = manifest.definitions["worker"]

    assert isinstance(agent, AgentDefinition)
    assert agent.capabilities.type == CapabilityType.ATOMIC
    assert agent.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert agent.capabilities.history_support is False


def test_serialization_loop_complex() -> None:
    """Test round-trip serialization of a nested event structure."""
    original = PresentationEvent(
        type=PresentationEventType.MEDIA_CAROUSEL,
        data=MediaCarousel(items=[MediaItem(url="http://a", mime_type="a"), MediaItem(url="http://b", mime_type="b")]),
    )

    # Serialize
    json_str = original.to_json()

    # Deserialize
    restored = PresentationEvent.model_validate_json(json_str)

    assert restored.id == original.id
    assert isinstance(restored.data, MediaCarousel)
    assert len(restored.data.items) == 2
    # Check strict type preservation
    assert str(restored.data.items[0].url) == "http://a/"
