import pytest

from coreason_manifest.spec.core.engines import StandardReasoning
from coreason_manifest.spec.core.flow import (
    Edge,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.nodes import AgentNode, Brain
from coreason_manifest.spec.core.tools import ToolPack
from coreason_manifest.utils.langchain_adapter import flow_to_langchain_config
from coreason_manifest.utils.mcp_adapter import pack_to_mcp_resources
from coreason_manifest.utils.openai_adapter import node_to_openai_assistant


def test_mcp_adapter() -> None:
    pack = ToolPack(kind="ToolPack", namespace="utils", tools=["calculator", "weather"], dependencies=[], env_vars=[])
    mcp_res = pack_to_mcp_resources(pack)
    expected_mcp = [
        {"uri": "mcp://utils/calculator", "name": "calculator", "mimeType": "application/json"},
        {"uri": "mcp://utils/weather", "name": "weather", "mimeType": "application/json"},
    ]
    assert mcp_res == expected_mcp


def test_openai_adapter() -> None:
    pack = ToolPack(kind="ToolPack", namespace="utils", tools=["calculator", "weather"], dependencies=[], env_vars=[])
    brain = Brain(
        role="assistant",
        persona="helpful",
        reasoning=StandardReasoning(model="gpt-4o", thoughts_max=10, min_confidence=0.5),
        reflex=None,
    )
    node = AgentNode(id="agent1", metadata={}, supervision=None, type="agent", brain=brain, tools=["calculator"])
    openai_res = node_to_openai_assistant(node, [pack])
    expected_openai = {
        "name": "agent1",
        "instructions": "assistant helpful",
        "model": "gpt-4o",
        "tools": [{"type": "function", "function": {"name": "calculator"}}],
    }
    assert openai_res == expected_openai

    # Test with default tool_packs (None)
    openai_res_default = node_to_openai_assistant(node)
    expected_openai_default = {
        "name": "agent1",
        "instructions": "assistant helpful",
        "model": "gpt-4o",
        "tools": [],
    }
    assert openai_res_default == expected_openai_default


def test_langchain_adapter() -> None:
    meta = FlowMetadata(name="test", version="1.0", description="desc", tags=[])
    pack = ToolPack(kind="ToolPack", namespace="utils", tools=["calculator", "weather"], dependencies=[], env_vars=[])
    brain = Brain(
        role="assistant",
        persona="helpful",
        reasoning=StandardReasoning(model="gpt-4o", thoughts_max=10, min_confidence=0.5),
        reflex=None,
    )
    node1 = AgentNode(id="agent1", metadata={}, supervision=None, type="agent", brain=brain, tools=["calculator"])
    node2 = AgentNode(id="agent2", metadata={}, supervision=None, type="agent", brain=brain, tools=["weather"])

    # LinearFlow
    linear_flow = LinearFlow(
        kind="LinearFlow",
        metadata=meta,
        sequence=[node1, node2],
        definitions=FlowDefinitions(tool_packs={"pack": pack}),
    )
    lc_linear = flow_to_langchain_config(linear_flow)
    expected_lc_linear = {"type": "chain", "steps": ["agent1", "agent2"]}
    assert lc_linear == expected_lc_linear

    # GraphFlow
    graph = Graph(
        nodes={"agent1": node1, "agent2": node2}, edges=[Edge(source="agent1", target="agent2", condition="success")]
    )
    graph_flow = GraphFlow(
        kind="GraphFlow",
        metadata=meta,
        interface=FlowInterface(inputs={}, outputs={}),
        blackboard=None,
        graph=graph,
        definitions=FlowDefinitions(tool_packs={"pack": pack}),
    )
    lc_graph = flow_to_langchain_config(graph_flow)

    assert lc_graph["type"] == "graph"
    assert set(lc_graph["nodes"]) == {"agent1", "agent2"}
    assert lc_graph["edges"] == [("agent1", "agent2", "success")]


def test_langchain_adapter_invalid_input() -> None:
    with pytest.raises(ValueError, match="Unknown flow type"):
        flow_to_langchain_config("invalid")  # type: ignore
