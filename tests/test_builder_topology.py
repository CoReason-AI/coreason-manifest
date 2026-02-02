import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.builder.agent import AgentBuilder
from coreason_manifest.builder.capability import TypedCapability
from coreason_manifest.definitions.agent import CapabilityType, ToolRequirement
from coreason_manifest.definitions.topology import LogicNode


class SimpleInput(BaseModel):
    query: str


class SimpleOutput(BaseModel):
    result: str


def get_valid_agent_builder(name: str = "TestAgent") -> AgentBuilder:
    cap = TypedCapability(
        name="test_cap",
        description="A test capability",
        input_model=SimpleInput,
        output_model=SimpleOutput,
        type=CapabilityType.ATOMIC,
    )
    return AgentBuilder(name=name).with_capability(cap).with_system_prompt("System Prompt").with_model("gpt-4o")


def test_builder_with_tools() -> None:
    agent = (
        get_valid_agent_builder(name="ToolAgent")
        .with_tool_requirement(
            uri="mcp://google/search",
            hash="a" * 64,  # Valid SHA256 length
            scopes=["read"],
        )
        .build()
    )
    assert len(agent.dependencies.tools) == 1
    tool = agent.dependencies.tools[0]
    assert isinstance(tool, ToolRequirement)
    assert str(tool.uri) == "mcp://google/search"


def test_builder_topology() -> None:
    node_a = LogicNode(id="start", type="logic", code="print('start')")
    node_b = LogicNode(id="end", type="logic", code="print('end')")

    agent = (
        get_valid_agent_builder(name="GraphAgent")
        .with_node(node_a)
        .with_node(node_b)
        .with_edge("start", "end")
        .set_entry_point("start")
        .build()
    )

    assert len(agent.config.nodes) == 2
    assert len(agent.config.edges) == 1
    assert agent.config.entry_point == "start"


def test_builder_validation_failure() -> None:
    """Attempt to build a graph with nodes but without setting an entry point."""
    node_a = LogicNode(id="start", type="logic", code="print('start')")

    builder = get_valid_agent_builder(name="InvalidGraphAgent").with_node(node_a)

    with pytest.raises(ValidationError) as excinfo:
        builder.build()

    # Check that the error message contains the expected validation error
    assert "Graph execution requires an 'entry_point'" in str(excinfo.value)
