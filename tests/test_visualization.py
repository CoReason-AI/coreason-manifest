from pydantic import BaseModel

from coreason_manifest.builder.agent import AgentBuilder
from coreason_manifest.builder.capability import TypedCapability
from coreason_manifest.definitions.topology import AgentNode, HumanNode, LogicNode, RecipeNode, VisualMetadata


class DummyInput(BaseModel):
    query: str

class DummyOutput(BaseModel):
    result: str

def test_atomic_agent_mermaid() -> None:
    # Create an atomic agent (no nodes)
    builder = AgentBuilder(name="AtomicAgent")
    cap = TypedCapability(
        name="chat",
        description="Chat capability",
        input_model=DummyInput,
        output_model=DummyOutput
    )
    builder.with_capability(cap)

    agent = builder.build()
    mermaid = agent.to_mermaid()

    assert "graph TD" in mermaid
    assert 'Start((Start)) --> Agent["AtomicAgent"]' in mermaid

def test_graph_agent_mermaid() -> None:
    # Create a graph agent
    builder = AgentBuilder(name="GraphAgent")
    cap = TypedCapability(
        name="chat",
        description="Chat capability",
        input_model=DummyInput,
        output_model=DummyOutput
    )
    builder.with_capability(cap)

    # Add nodes
    # AgentNode
    node1 = AgentNode(
        id="node1",
        agent_name="SearchAgent",
        visual=VisualMetadata(label="Search Web")
    )
    # LogicNode
    node2 = LogicNode(
        id="node2",
        code="return True",
        visual=VisualMetadata(label="Check Result")
    )
    # HumanNode
    node3 = HumanNode(
        id="node3",
        visual=VisualMetadata(label="User Approval")
    )
    # RecipeNode (Default Case)
    node4 = RecipeNode(
        id="node4",
        recipe_id="some_recipe",
        input_mapping={},
        output_mapping={},
        visual=VisualMetadata(label="Sub Recipe")
    )

    builder.with_node(node1)
    builder.with_node(node2)
    builder.with_node(node3)
    builder.with_node(node4)

    # Add edges
    builder.with_edge("node1", "node2")
    builder.with_edge("node2", "node3", condition="is_valid")
    builder.with_edge("node3", "node4")

    builder.set_entry_point("node1")

    agent = builder.build()
    mermaid = agent.to_mermaid()

    # Check Header and Classes
    assert "graph TD" in mermaid
    assert "classDef agent" in mermaid
    assert "classDef logic" in mermaid
    assert "classDef human" in mermaid

    # Check Nodes
    # node1: agent, label "Search Web"
    # Expected: node1["Search Web"]:::agent
    assert 'node1["Search Web"]:::agent' in mermaid

    # node2: logic, label "Check Result"
    # Expected: node2{"Check Result"}:::logic
    assert 'node2{"Check Result"}:::logic' in mermaid

    # node3: human, label "User Approval"
    # Expected: node3("User Approval"):::human
    assert 'node3("User Approval"):::human' in mermaid

    # node4: recipe, label "Sub Recipe" (Default)
    # Expected: node4["Sub Recipe"]:::default
    assert 'node4["Sub Recipe"]:::default' in mermaid

    # Check Edges
    # node1 --> node2
    assert "node1 --> node2" in mermaid
    # node2 -- "is_valid" --> node3
    assert 'node2 -- "is_valid" --> node3' in mermaid
    # node3 --> node4
    assert "node3 --> node4" in mermaid

    # Check Entry Point
    assert "Start((Start)) --> node1" in mermaid
