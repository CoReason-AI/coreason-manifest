import pytest
from coreason_manifest.definitions import (
    AgentManifest,
    KnowledgeArtifact,
    ArtifactType,
    EnrichmentLevel,
    TopologyGraph,
    TopologyNode,
    ToolCall,
    BECTestCase,
    CoReasonBaseModel
)
from unittest.mock import patch
from pydantic import ValidationError

def test_agent_manifest_instantiation():
    """Test that AgentManifest can be instantiated with valid data."""
    data = {
        "schema_version": "1.0",
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 10.0,
        "temperature": 0.5,
        "topology": "path/to/topology.yaml"
    }
    agent = AgentManifest(**data)
    assert agent.name == "test-agent"
    assert agent.version == "1.0.0"
    assert agent.model_config_id == "gpt-4"

def test_knowledge_artifact_instantiation():
    """Test that KnowledgeArtifact can be instantiated."""
    data = {
        "id": "hash123",
        "content": "# Test Content",
        "artifact_type": "TEXT",
        "source_urn": "urn:s3:test/file.md",
        "source_location": {"page": 1},
        "enrichment_level": "RAW",
        "sensitivity": "INTERNAL"
    }
    artifact = KnowledgeArtifact(**data)
    assert artifact.id == "hash123"
    assert artifact.artifact_type == ArtifactType.TEXT
    assert artifact.enrichment_level == EnrichmentLevel.RAW

def test_topology_graph_instantiation():
    """Test TopologyGraph structure."""
    nodes = [
        TopologyNode(
            id="node1",
            step_type="prompt",
            next_steps=["node2"],
            config={"prompt": "Hello"}
        ),
        TopologyNode(
            id="node2",
            step_type="tool",
            next_steps=[],
            config={"tool": "search"}
        )
    ]
    graph = TopologyGraph(nodes=nodes)
    assert len(graph.nodes) == 2

def test_topology_cycle_detection():
    """Test that cycles are detected in TopologyGraph."""
    nodes = [
        TopologyNode(id="A", step_type="logic", next_steps=["B"]),
        TopologyNode(id="B", step_type="logic", next_steps=["A"])  # Cycle
    ]
    with pytest.raises(ValidationError, match="Cycle detected"):
        TopologyGraph(nodes=nodes)

def test_topology_missing_node():
    """Test validation for missing node references."""
    nodes = [
        TopologyNode(id="A", step_type="logic", next_steps=["C"])  # C missing
    ]
    with pytest.raises(ValidationError, match="points to non-existent node"):
        TopologyGraph(nodes=nodes)

def test_topology_duplicate_ids():
    """Test validation for duplicate node IDs."""
    nodes = [
        TopologyNode(id="A", step_type="logic"),
        TopologyNode(id="A", step_type="logic")
    ]
    with pytest.raises(ValidationError, match="Duplicate node ID"):
        TopologyGraph(nodes=nodes)

def test_canonical_hash():
    """Test canonical hashing."""
    class TestModel(CoReasonBaseModel):
        a: int
        b: str

    obj1 = TestModel(a=1, b="test")
    obj2 = TestModel(b="test", a=1)
    assert obj1.canonical_hash() == obj2.canonical_hash()

    # Ensure hash changes with content
    obj3 = TestModel(a=2, b="test")
    assert obj1.canonical_hash() != obj3.canonical_hash()

def test_tool_sql_injection():
    """Test SQL injection prevention in ToolCall."""
    # Safe call
    ToolCall(tool_name="db", arguments={"query": "select * from users"})

    # Unsafe call
    with pytest.raises(ValidationError, match="Potential SQL injection"):
        ToolCall(tool_name="db", arguments={"query": "DROP TABLE users"})

    # Unsafe nested (needs whitespace before OR as per regex)
    with pytest.raises(ValidationError, match="Potential SQL injection"):
        ToolCall(tool_name="db", arguments={"params": {"q": "admin' OR 1=1"}})

    # Unsafe list
    with pytest.raises(ValidationError, match="Potential SQL injection"):
        ToolCall(tool_name="db", arguments={"queries": ["select *", "DROP TABLE users"]})

def test_bec_schema_validation():
    """Test JSON Schema validation in BECTestCase."""
    # Valid schema
    BECTestCase(
        id="test1",
        prompt="hello",
        expected_output_structure={"type": "object", "properties": {"a": {"type": "string"}}}
    )

    # Invalid schema
    with pytest.raises(ValidationError, match="Invalid JSON Schema"):
        BECTestCase(
            id="test2",
            prompt="hello",
            expected_output_structure={"type": "invalid_type_xyz"}
        )

def test_bec_schema_validation_none():
    """Test validation when structure is None."""
    # Should pass
    case = BECTestCase(id="test3", prompt="hi", expected_output_structure=None)
    assert case.expected_output_structure is None

    # Explicitly call validator to ensure coverage of the None check
    assert BECTestCase.validate_json_schema(None) is None

def test_bec_schema_validation_generic_exception():
    """Test generic exception handling during schema validation."""
    with patch("coreason_manifest.definitions.bec.validator_for", side_effect=Exception("Generic error")):
        with pytest.raises(ValidationError, match="Invalid JSON Schema: Generic error"):
             BECTestCase(
                id="test4",
                prompt="hi",
                expected_output_structure={"type": "object"}
            )
