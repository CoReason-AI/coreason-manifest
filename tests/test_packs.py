# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    ManifestV2,
    ToolDefinition,
)
from coreason_manifest.spec.v2.packs import (
    MCPResourceDefinition,
    MCPServerDefinition,
    PackMetadata,
    ToolPackDefinition,
)
from coreason_manifest.spec.v2.skills import LoadStrategy, SkillDefinition


def test_tool_pack_structure() -> None:
    pack = ToolPackDefinition(
        id="feature-dev-v1",
        namespace="feature_dev",
        metadata=PackMetadata(
            name="feature-dev",
            version="1.0.0",
            description="Comprehensive feature development workflow.",
            author="Anthropic",
        ),
        agents=[
            AgentDefinition(
                id="code-architect",
                name="Code Architect",
                role="Architect",
                goal="Design software architecture.",
            )
        ],
        skills=[
            "git-commit-skill",
            SkillDefinition(
                id="spec-analysis",
                name="Spec Analyzer",
                description="Analyzes specifications.",
                load_strategy=LoadStrategy.LAZY,
                trigger_intent="Analyze requirements",
                instructions="Analyze the spec carefully.",
            ),
        ],
        tools=[],
        mcp_servers=[MCPServerDefinition(name="my-server", command="node", args=["server.js"])],
    )

    assert pack.id == "feature-dev-v1"
    assert pack.metadata.name == "feature-dev"
    assert len(pack.agents) == 1
    assert isinstance(pack.agents[0], AgentDefinition)
    assert pack.agents[0].id == "code-architect"
    assert len(pack.skills) == 2
    assert pack.skills[0] == "git-commit-skill"
    assert isinstance(pack.skills[1], SkillDefinition)
    assert len(pack.mcp_servers) == 1
    assert pack.mcp_servers[0].name == "my-server"


def test_manifest_integration() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata={"name": "Test Manifest"},
        workflow={
            "start": "step1",
            "steps": {"step1": {"type": "logic", "id": "step1", "code": "print('hello')"}},
        },
        definitions={
            "feature-dev-pack": ToolPackDefinition(
                id="feature-dev-v1",
                metadata=PackMetadata(name="feature-dev", description="Test Pack", author="Test Author"),
                agents=["agent-ref"],
                mcp_servers=[],
            )
        },
    )

    pack = manifest.definitions["feature-dev-pack"]
    assert isinstance(pack, ToolPackDefinition)
    assert pack.agents[0] == "agent-ref"


def test_mcp_resource_definition() -> None:
    resource = MCPResourceDefinition(
        uri="http://example.com/resource",
        name="Example Resource",
        description="A test resource.",
    )
    assert str(resource.uri) == "http://example.com/resource"


def test_pack_invalid_names() -> None:
    # Test invalid pack name (must be kebab-case)
    with pytest.raises(ValidationError) as excinfo:
        PackMetadata(name="Invalid Pack Name", description="Bad name", author="Me")
    assert "string_pattern_mismatch" in str(excinfo.value)

    # Test valid name
    metadata = PackMetadata(name="valid-pack-name", description="Good name", author="Me")
    assert metadata.name == "valid-pack-name"


def test_pack_missing_metadata_fields() -> None:
    # Missing required 'description'
    with pytest.raises(ValidationError):
        PackMetadata(name="my-pack", author="Me")  # type: ignore[call-arg]

    # Missing required 'author'
    with pytest.raises(ValidationError):
        PackMetadata(name="my-pack", description="desc")  # type: ignore[call-arg]


def test_pack_mixed_definitions() -> None:
    # Test a pack with mixed inline and referenced definitions
    agent_inline = AgentDefinition(id="inline-agent", name="Inline", role="Helper", goal="Help")

    tool_inline = ToolDefinition(id="inline-tool", name="InlineTool", uri="http://example.com/tool", risk_level="safe")

    pack = ToolPackDefinition(
        id="mixed-pack",
        metadata=PackMetadata(name="mixed-pack", description="Mixed definitions", author="Tester"),
        agents=[agent_inline, "ref-agent-id"],
        tools=["ref-tool-id", tool_inline],
        skills=[],
    )

    assert len(pack.agents) == 2
    assert isinstance(pack.agents[0], AgentDefinition)
    assert isinstance(pack.agents[1], str)

    assert len(pack.tools) == 2
    assert isinstance(pack.tools[0], str)
    assert isinstance(pack.tools[1], ToolDefinition)


def test_pack_invalid_mcp_server() -> None:
    # Missing command
    with pytest.raises(ValidationError):
        MCPServerDefinition(name="broken-server")  # type: ignore[call-arg]


def test_complex_nested_structure_in_manifest() -> None:
    # Verify a complex manifest with multiple packs and resources
    manifest = ManifestV2(
        kind="Recipe",
        metadata={"name": "Complex Manifest"},
        workflow={"start": "step1", "steps": {"step1": {"type": "logic", "id": "step1", "code": "pass"}}},
        definitions={
            "pack1": ToolPackDefinition(
                id="pack-1", metadata=PackMetadata(name="pack-1", description="P1", author="A1"), agents=["agent1"]
            ),
            "resource1": MCPResourceDefinition(uri="data://resource1", name="Resource 1"),
            "agent1": AgentDefinition(id="agent1", name="Agent 1", role="Worker", goal="Work"),
        },
    )

    assert "pack1" in manifest.definitions
    assert "resource1" in manifest.definitions
    assert "agent1" in manifest.definitions

    pack = manifest.definitions["pack1"]
    assert isinstance(pack, ToolPackDefinition)
    assert pack.agents == ["agent1"]


def test_pack_author_object() -> None:
    # Test author as an object
    metadata = PackMetadata(
        name="author-object-pack",
        description="Testing author object",
        author={"name": "Jane Doe", "email": "jane@example.com", "url": "https://example.com"},
    )
    # Pydantic should parse the dict into PackAuthor
    # But currently 'author' field is defined as `str | PackAuthor`.
    # Pydantic V2 handles dict -> Model conversion automatically if Union allows it.

    author_field = PackMetadata.model_fields["author"]
    assert author_field.annotation is not None
    assert isinstance(
        metadata.author,
        author_field.annotation.__args__[1],
    )  # Check if it's PackAuthor
    # Or simply access attributes if it converted correctly
    # Wait, strict checking might prevent implicit conversion if not handled carefully,
    # but Pydantic generally allows dict -> Model.

    # Let's verify specifically
    # Actually, accessing attributes directly on the Union might fail type checking,
    # but runtime should work if Pydantic instantiated the model.
    # To be safe and explicit:
    assert metadata.author.name == "Jane Doe"
    assert metadata.author.email == "jane@example.com"
