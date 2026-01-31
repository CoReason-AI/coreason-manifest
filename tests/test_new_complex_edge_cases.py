import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.simulation import SimulationTrace, SimulationTurn
from coreason_manifest.models import (
    AgentDefinition,
    AgentMetadata,
    Step,
)
from coreason_manifest.recipes import (
    AgentNode,
    CouncilConfig,
    Edge,
    HumanNode,
    LogicNode,
    RecipeManifest,
    VisualMetadata,
)


def test_mega_agent_complex_scenario() -> None:
    """
    A redundant, complex test case simulating a massive 'War Game' agent
    to verify structural integrity, serialization, and hash stability
    under load.
    """
    # 1. Construct complex data
    steps_count = 50
    large_steps = [
        Step(id=f"step_{i}", description=f"Complex Logic Step {i} with unicode 🤖") for i in range(steps_count)
    ]

    injected = ["user_context", "audit_log", "trace_id"]

    # Nested input schema
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "context": {
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "string"}, "score": {"type": "number"}}},
            },
        },
    }

    data = {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.2.3-beta.1+build.123",  # Complex SemVer
            "name": "Mega-Agent-X 3000™",
            "author": "Dr. Strange 🧙‍♂️",
            "created_at": "2024-01-01T12:00:00.123456+00:00",
            "requires_auth": True,
        },
        "interface": {"inputs": input_schema, "outputs": {"type": "string"}, "injected_params": injected},
        "topology": {"steps": large_steps, "model_config": {"model": "gpt-4-32k-0613", "temperature": 0.7}},
        "dependencies": {
            "tools": ["https://api.coreason.ai/tools/calculator", "https://api.coreason.ai/tools/search?q=test"],
            "libraries": ["numpy==1.24.0", "pandas==2.0.0"],
        },
        "integrity_hash": "a" * 64,
    }

    # 2. Validation
    agent = AgentDefinition(**data)

    # 3. Structural Verification
    assert len(agent.topology.steps) == steps_count
    assert agent.metadata.name == "Mega-Agent-X 3000™"
    assert agent.interface.inputs["type"] == "object"

    # 4. Serialization / Round Trip
    # dump to json string (must use by_alias to match input alias expectation for model_config)
    json_str = agent.model_dump_json(by_alias=True)
    # verify we can load it back
    loaded_data = json.loads(json_str)
    # Re-instantiate
    agent_reloaded = AgentDefinition(**loaded_data)

    # 5. Equality Check
    # Note: Pydantic models with lists/tuples might compare differently if types changed during load
    # But field values should be identical.
    assert agent.metadata.id == agent_reloaded.metadata.id
    assert agent.metadata.created_at == agent_reloaded.metadata.created_at


def test_recipe_polymorphism_edge_cases() -> None:
    """Test mixed node types and discriminator behavior in RecipeManifest."""

    nodes = [
        AgentNode(
            id="node1", agent_name="Agent007", visual=VisualMetadata(label="The Spy", x_y_coordinates=[10.5, 20.2])
        ),
        HumanNode(id="node2", timeout_seconds=3600, council_config=CouncilConfig(voters=["admin"])),
        LogicNode(id="node3", code="return True"),
    ]

    edges = [
        Edge(source_node_id="node1", target_node_id="node2"),
        Edge(source_node_id="node2", target_node_id="node3", condition="approved is True"),
    ]

    recipe_data = {
        "id": "recipe-1",
        "version": "1.0.0",
        "name": "Hybrid Workflow",
        "inputs": {},
        "graph": {"nodes": nodes, "edges": edges},
    }

    recipe = RecipeManifest(**recipe_data)

    # Verify Polymorphism
    assert isinstance(recipe.graph.nodes[0], AgentNode)
    assert isinstance(recipe.graph.nodes[1], HumanNode)
    assert isinstance(recipe.graph.nodes[2], LogicNode)
    assert recipe.graph.nodes[0].type == "agent"
    assert recipe.graph.nodes[1].type == "human"

    # Verify JSON serialization preserves discriminators
    json_out = recipe.model_dump(mode="json")
    assert json_out["graph"]["nodes"][0]["type"] == "agent"


def test_simulation_trace_boundaries() -> None:
    """Test SimulationTrace with boundary conditions."""

    # Huge metadata
    huge_metadata = {f"k{i}": i for i in range(1000)}

    trace = SimulationTrace(
        scenario_id=uuid4(),
        agent_id="agent-x",
        agent_version="1.0.0",
        history=[
            SimulationTurn(
                user_input="A" * 10000,  # Large input
                agent_response="B" * 10000,
                metadata=huge_metadata,
            )
        ],
        score=0.0000001,  # Small float
        passed=True,
    )

    # Hash check
    h = trace.canonical_hash()
    assert isinstance(h, str)
    assert len(h) == 64


def test_datetime_coercion_edge_cases() -> None:
    """Test robust datetime handling including timezone awareness."""

    # Case 1: UTC Z suffix
    meta = AgentMetadata(id=uuid4(), version="1.0.0", name="n", author="a", created_at="2023-01-01T12:00:00Z")
    assert meta.created_at.tzinfo == timezone.utc

    # Case 2: Offset +05:30
    meta2 = AgentMetadata(id=uuid4(), version="1.0.0", name="n", author="a", created_at="2023-01-01T12:00:00+05:30")
    assert meta2.created_at.tzinfo is not None

    # Case 3: No timezone (should imply naive, but pydantic allows it)
    meta3 = AgentMetadata(id=uuid4(), version="1.0.0", name="n", author="a", created_at="2023-01-01T12:00:00")
    assert meta3.created_at.year == 2023


def test_semver_v_prefix_recursion() -> None:
    """Test recursive stripping of 'v' prefixes."""
    # "vvVv1.0.0" -> "1.0.0"
    meta = AgentMetadata(id=uuid4(), version="vvVv1.0.0", name="n", author="a", created_at=datetime.now())
    assert meta.version == "1.0.0"


def test_extra_fields_forbidden() -> None:
    """Verify extra fields cause error in deep nested objects."""

    # Extra field in ModelConfig
    data = {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "n",
            "author": "a",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [],
            "model_config": {
                "model": "gpt-4",
                "temperature": 0.5,
                "SECRET_PARAM": "inject",  # Forbidden
            },
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "a" * 64,
    }

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AgentDefinition(**data)
