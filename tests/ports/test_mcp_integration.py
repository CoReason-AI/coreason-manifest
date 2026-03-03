"""
Integration tests for the Native MCP Integration.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from mcp.server.fastmcp import FastMCP

from coreason_manifest.core.state.events import EpistemicAnchor, EpistemicEvent, EventType
from coreason_manifest.core.state.ledger import EpistemicLedger
from coreason_manifest.ports.mcp import create_mcp_server


@pytest.fixture
def ledger() -> EpistemicLedger:
    """Provide an empty EpistemicLedger for testing."""
    return EpistemicLedger()


@pytest.fixture
def mcp_server(ledger: EpistemicLedger) -> FastMCP:
    """Provide a configured MCP server connected to the ledger."""
    return create_mcp_server(ledger)


@pytest.mark.asyncio
async def test_mcp_resource_fetch_event(ledger: EpistemicLedger, mcp_server: FastMCP) -> None:
    """
    Test 1 (Resource): Prove that appending an event to the ledger allows the MCP Resource router
    to fetch it successfully via its epistemic:// URI.
    """
    event_id = str(uuid4())
    event = EpistemicEvent(
        event_id=event_id,
        timestamp=datetime.now(UTC),
        context_envelope={"test": "env"},
        event_type=EventType.SEMANTIC_EXTRACTED,
        payload={"data": "test_payload"},
        epistemic_anchor=EpistemicAnchor(),
    )
    await ledger.aappend(event)

    resource_uri = f"epistemic://ledger/events/{event_id}"

    # FastMCP exposes read_resource
    content_list = list(await mcp_server.read_resource(resource_uri))
    assert len(content_list) == 1
    content = content_list[0].content

    # Should be the canonical JSON representation
    parsed = json.loads(str(content))
    assert parsed["event_id"] == event_id
    assert parsed["payload"]["data"] == "test_payload"


@pytest.mark.asyncio
async def test_mcp_resource_not_found(mcp_server: FastMCP) -> None:
    """Test fetching a non-existent event."""
    # FastMCP routes errors, but typically exceptions in resource fetching might surface as errors
    with pytest.raises(ValueError, match="not found in ledger"):
        await mcp_server.read_resource("epistemic://ledger/events/nonexistent")


@pytest.mark.asyncio
async def test_mcp_tool_validation_success(ledger: EpistemicLedger, mcp_server: FastMCP) -> None:
    """
    Prove that calling the append_clinical_proposition tool with a strictly conforming
    payload appends it to the ledger.
    """
    payload = {
        "subject": {"entity_string": "Aspirin", "global_id": "C0004057"},
        "relation": "treats",
        "object": {"entity_string": "Headache", "global_id": "C0018681"},
        "p_value": 0.01,  # Statistical grounding
        "provenance": {
            "source_document_hash": "hash123",
            "page_number": 1,
            "bounding_box": (0.1, 0.2, 0.3, 0.4),
            "raw_text_crop": "Aspirin treats headache (p=0.01)",
        },
    }

    response = await mcp_server.call_tool("append_clinical_proposition", {"proposition": payload})

    # In FastMCP, call_tool returns a list of TextContent/ImageContent objects or strings
    # The return from the function is just formatted string "Successfully appended event ..."
    # Actually, in MCP the response might be a ToolResult or we can inspect the content
    # For fastmcp, call_tool returns strings or lists of things
    # Let's check the ledger directly to ensure it was appended
    events = ledger.get_events()
    assert len(events) == 1
    event = events[0]

    assert event.event_type == EventType.SEMANTIC_EXTRACTED
    assert event.payload["subject"]["entity_string"] == "Aspirin"
    assert "Successfully appended event" in str(response)


@pytest.mark.asyncio
async def test_mcp_tool_validation_failure(ledger: EpistemicLedger, mcp_server: FastMCP) -> None:
    """
    Test 2 (Tool Validation): Prove that calling the append_clinical_proposition tool with a statistically
    ungrounded payload raises a validation error BEFORE touching the ledger.
    """
    payload = {
        "subject": {"entity_string": "Aspirin", "global_id": "C0004057"},
        "relation": "treats",
        "object": {"entity_string": "Headache", "global_id": "C0018681"},
        # MISSING p_value or confidence_interval
        "provenance": {
            "source_document_hash": "hash123",
            "page_number": 1,
            "bounding_box": (0.1, 0.2, 0.3, 0.4),
            "raw_text_crop": "Aspirin might treat headache",
        },
    }

    # FastMCP uses Pydantic to validate tool arguments.
    # It catches ValidationError and wraps it in a ToolError or ValidationError
    try:
        await mcp_server.call_tool("append_clinical_proposition", {"proposition": payload})
        pytest.fail("Expected tool call to fail validation")
    except Exception as e:
        error_msg = str(e).lower()
        assert "validation error" in error_msg or "statistical grounding error" in error_msg

    # Ensure ledger wasn't touched
    assert len(ledger.get_events()) == 0


@pytest.mark.asyncio
async def test_mcp_prompt(mcp_server: FastMCP) -> None:
    """Test dynamic context injection via MCP Prompts."""
    prompt_result = await mcp_server.get_prompt(
        "auditor_recovery_prompt",
        {"suspense_reason": "bad_math_token", "hardware_profile": "H100-Cluster"},
    )

    # In FastMCP, get_prompt returns a Prompt object containing messages
    messages = prompt_result.messages
    assert len(messages) == 1

    # Safely access the text content or fallback to string representation
    msg_content = messages[0].content
    content_text = getattr(msg_content, "text", str(msg_content))

    assert "H100-Cluster" in content_text
    assert "bad_math_token" in content_text
    assert "verify the blurry bounding box or failing mathematical token carefully" in content_text
