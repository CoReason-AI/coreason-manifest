import pytest
from coreason_manifest import simple_agent
from coreason_manifest.spec.v2.definitions import ManifestV2, AgentDefinition

def test_simple_agent_minimal():
    manifest = simple_agent(name="TestAgent")
    assert isinstance(manifest, ManifestV2)
    assert manifest.metadata.name == "TestAgent"
    assert "TestAgent" in manifest.definitions
    agent = manifest.definitions["TestAgent"]
    assert isinstance(agent, AgentDefinition)
    assert agent.id == "TestAgent"
    assert agent.goal == "Help the user" # default from AgentBuilder

def test_simple_agent_full_options():
    manifest = simple_agent(
        name="Researcher",
        prompt="You are a research assistant.",
        model="gpt-4",
        tools=["search-tool"],
        knowledge=["docs/info.txt"],
        inputs={"topic": {"type": "string"}},
        outputs={"report": {"type": "string"}},
    )

    agent = manifest.definitions["Researcher"]
    assert agent.backstory == "You are a research assistant."
    assert agent.model == "gpt-4"
    assert agent.tools == ["search-tool"]
    assert agent.knowledge == ["docs/info.txt"]

    # Check interface inputs - it should be wrapped in object/properties because we passed a dict without "type"
    assert manifest.interface.inputs["type"] == "object"
    assert "topic" in manifest.interface.inputs["properties"]
    assert manifest.interface.inputs["properties"]["topic"]["type"] == "string"

    # Check interface outputs
    assert manifest.interface.outputs["type"] == "object"
    assert "report" in manifest.interface.outputs["properties"]

def test_simple_agent_raw_schema():
    # Pass full schema with "type": "object"
    schema = {
        "type": "object",
        "properties": {"foo": {"type": "integer"}},
        "required": ["foo"]
    }
    manifest = simple_agent(name="SchemaAgent", inputs=schema)

    # Should use the schema directly
    assert manifest.interface.inputs == schema
    assert manifest.interface.inputs["type"] == "object"
    assert manifest.interface.inputs["required"] == ["foo"]
