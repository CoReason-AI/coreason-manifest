# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import BaseModel, Field

from coreason_manifest.builder import AgentBuilder, TypedCapability
from coreason_manifest.spec.common.capabilities import CapabilityType, DeliveryMode
from coreason_manifest.spec.v2.definitions import AgentDefinition


class SearchInput(BaseModel):
    query: str


class SearchOutput(BaseModel):
    results: list[str]


class EmptyModel(BaseModel):
    pass


class ConflictInput(BaseModel):
    query: int  # Different type from SearchInput (integer vs string)


def test_schema_auto_generation() -> None:
    search_cap = TypedCapability(
        name="WebSearch",
        description="Search",
        input_model=SearchInput,
        output_model=SearchOutput,
    )

    agent = AgentBuilder("TestAgent").with_capability(search_cap).build()

    inputs = agent.interface.inputs
    outputs = agent.interface.outputs

    assert "query" in inputs["properties"]
    assert inputs["properties"]["query"]["type"] == "string"
    assert "results" in outputs["properties"]
    assert outputs["properties"]["results"]["type"] == "array"


def test_fluent_chaining() -> None:
    agent = (
        AgentBuilder("TestAgent")
        .with_model("gpt-4")
        .with_system_prompt("Be helpful")
        .with_tool("tool-1")
        .with_knowledge("s3://bucket/doc.pdf")
        .build()
    )

    # Check ManifestMetadata
    assert agent.metadata.name == "TestAgent"

    # Check AgentDefinition
    agent_def = agent.definitions["TestAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.model == "gpt-4"
    assert agent_def.backstory == "Be helpful"
    assert "tool-1" in agent_def.tools
    assert "s3://bucket/doc.pdf" in agent_def.knowledge


def test_capability_configuration() -> None:
    # Default is REQUEST_RESPONSE and GRAPH
    agent = AgentBuilder("DefaultAgent").build()
    agent_def = agent.definitions["DefaultAgent"]
    assert isinstance(agent_def, AgentDefinition)
    assert agent_def.capabilities.type == CapabilityType.GRAPH
    assert agent_def.capabilities.delivery_mode == DeliveryMode.REQUEST_RESPONSE

    # Add ATOMIC and SSE
    cap = TypedCapability(
        name="StreamCap",
        description="Stream",
        input_model=SearchInput,
        output_model=SearchOutput,
        type=CapabilityType.ATOMIC,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    )

    agent_sse = AgentBuilder("SSEAgent").with_capability(cap).build()
    agent_def_sse = agent_sse.definitions["SSEAgent"]
    assert isinstance(agent_def_sse, AgentDefinition)

    # Last capability type wins in my implementation
    assert agent_def_sse.capabilities.type == CapabilityType.ATOMIC
    assert agent_def_sse.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS


def test_edge_empty_model() -> None:
    cap = TypedCapability(
        name="EmptyCap",
        description="Empty",
        input_model=EmptyModel,
        output_model=EmptyModel,
    )

    agent = AgentBuilder("EmptyAgent").with_capability(cap).build()

    # Pydantic EmptyModel schema: type object, properties {}
    assert agent.interface.inputs.get("properties") == {}
    assert agent.interface.outputs.get("properties") == {}


def test_edge_overlapping_properties() -> None:
    # Last writer wins
    cap1 = TypedCapability(
        name="Cap1",
        description="Cap1",
        input_model=SearchInput,  # query: str
        output_model=SearchOutput,
    )
    cap2 = TypedCapability(
        name="Cap2",
        description="Cap2",
        input_model=ConflictInput,  # query: int
        output_model=SearchOutput,
    )

    agent = AgentBuilder("ConflictAgent").with_capability(cap1).with_capability(cap2).build()

    # cap2 should win
    query_prop = agent.interface.inputs["properties"]["query"]
    assert query_prop["type"] == "integer"


def test_complex_capability_delivery_mode_precedence() -> None:
    # If one cap is SSE, the whole agent is marked as SSE (as per logic)
    cap_req = TypedCapability(
        name="ReqCap",
        description="Req",
        input_model=SearchInput,
        output_model=SearchOutput,
        delivery_mode=DeliveryMode.REQUEST_RESPONSE,
    )
    cap_sse = TypedCapability(
        name="SSECap",
        description="SSE",
        input_model=SearchInput,
        output_model=SearchOutput,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    )

    # Order: Req then SSE
    agent1 = AgentBuilder("Agent1").with_capability(cap_req).with_capability(cap_sse).build()
    agent1_def = agent1.definitions["Agent1"]
    assert isinstance(agent1_def, AgentDefinition)
    assert agent1_def.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS

    # Order: SSE then Req (SSE should stick if logic is "if ANY is sse")
    agent2 = AgentBuilder("Agent2").with_capability(cap_sse).with_capability(cap_req).build()
    agent2_def = agent2.definitions["Agent2"]
    assert isinstance(agent2_def, AgentDefinition)
    assert agent2_def.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS


class NestedModel(BaseModel):
    child: SearchInput


def test_nested_model_defs() -> None:
    cap = TypedCapability(
        name="Nested",
        description="Nested",
        input_model=NestedModel,
        output_model=SearchOutput,
    )
    agent = AgentBuilder("NestedAgent").with_capability(cap).build()

    assert "$defs" in agent.interface.inputs
    # Verify SearchInput is in $defs
    # Note: Pydantic might name it 'SearchInput' or similar
    assert "SearchInput" in agent.interface.inputs["$defs"]


class AliasModel(BaseModel):
    my_field: str = Field(..., alias="real_field_name")


def test_pydantic_aliases() -> None:
    cap = TypedCapability(
        name="AliasCap",
        description="Alias",
        input_model=AliasModel,
        output_model=EmptyModel,
    )
    agent = AgentBuilder("AliasAgent").with_capability(cap).build()

    props = agent.interface.inputs["properties"]
    # Pydantic JSON schema uses the alias by default
    assert "real_field_name" in props
    assert "my_field" not in props


def test_kitchen_sink_full_composition() -> None:
    """Complex case mixing tools, knowledge, prompt, model, and multiple capabilities."""
    cap1 = TypedCapability(
        name="Search",
        description="Search",
        input_model=SearchInput,
        output_model=SearchOutput,
    )
    cap2 = TypedCapability(
        name="Alias",
        description="Alias",
        input_model=AliasModel,
        output_model=EmptyModel,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
        type=CapabilityType.ATOMIC,
    )

    agent = (
        AgentBuilder("KitchenSink")
        .with_model("claude-3-opus")
        .with_system_prompt("System Prompt")
        .with_tool("tool-search")
        .with_tool("tool-calculator")
        .with_knowledge("s3://data/kb.pdf")
        .with_capability(cap1)
        .with_capability(cap2)
        .build()
    )

    agent_def = agent.definitions["KitchenSink"]
    assert isinstance(agent_def, AgentDefinition)

    # Verify Basics
    assert agent_def.model == "claude-3-opus"
    assert agent_def.backstory == "System Prompt"
    assert agent_def.tools == ["tool-search", "tool-calculator"]
    assert agent_def.knowledge == ["s3://data/kb.pdf"]

    # Verify Capability Logic (SSE wins, ATOMIC wins because it was last)
    assert agent_def.capabilities.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS
    assert agent_def.capabilities.type == CapabilityType.ATOMIC

    # Verify Interface Merging
    inputs = agent.interface.inputs["properties"]
    assert "query" in inputs  # from SearchInput
    assert "real_field_name" in inputs  # from AliasModel
    assert "results" in agent.interface.outputs["properties"]  # from SearchOutput
