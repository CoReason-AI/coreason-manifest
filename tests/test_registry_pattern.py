# tests/test_registry_pattern.py

from typing import Any

import pytest

from coreason_manifest.spec.core.flow import (
    DataSchema,
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.validator import validate_flow


def test_registry_tool_pack_lookup() -> None:
    # 1. Define a tool pack
    my_tool = ToolCapability(name="search_db", description="Search database")
    pack = ToolPack(
        kind="ToolPack",
        namespace="db_tools",
        tools=[my_tool],
        dependencies=[],
        env_vars=[],
    )

    # 2. Define definitions
    defs = FlowDefinitions(tool_packs={"db": pack})

    # 3. Create Agent referencing the tool
    agent = AgentNode(
        id="agent1",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p"),
        tools=["search_db"],  # valid because it's in the pack
        resilience=None,
    )

    # 4. Create Flow
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0"),
        definitions=defs,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    # 5. Validate
    errors = validate_flow(flow)
    assert not errors


def test_referential_integrity_failure() -> None:
    # 1. Agent references missing profile ID
    agent = AgentNode(
        id="agent1",
        type="agent",
        metadata={},
        profile="missing_profile_id",
        tools=[],
        resilience=None,
    )

    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")

    # Empty definitions
    defs = FlowDefinitions(profiles={})

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0"),
        definitions=defs,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    # 3. Expect an error code from validate_flow
    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_UNDEFINED_PROFILE_002" and e.details.get("profile_id") == "missing_profile_id" for e in errors)


def test_tool_integrity_failure() -> None:
    # 1. Agent references missing tool
    agent = AgentNode(
        id="agent1",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p"),
        tools=["missing_tool"],
        resilience=None,
    )

    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")

    # Empty definitions
    defs = FlowDefinitions(tool_packs={})

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0"),
        definitions=defs,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    # 3. Expect an error code from validate_flow
    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_MISSING_TOOL_001" and e.details.get("tool") == "missing_tool" for e in errors)


def test_tool_integrity_failure_graph() -> None:
    # Same as above but explicitly GraphFlow structure logic check if separate
    # Covered by test_tool_integrity_failure actually.
    # Let's ensure coverage for GraphFlow specifically if validator logic forks.

    agent = AgentNode(
        id="agent1",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p"),
        tools=["missing_tool"],
        resilience=None,
    )
    graph = Graph(nodes={"agent1": agent}, edges=[], entry_point="agent1")

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0"),
        definitions=FlowDefinitions(),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )

    errors = validate_flow(flow)
    assert any(e.code == "ERR_CAP_MISSING_TOOL_001" for e in errors)
