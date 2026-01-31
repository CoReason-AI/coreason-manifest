from coreason_manifest.definitions.agent import AgentDependencies, ToolRequirement, ToolRiskLevel


def test_tools_validation_valid_requirements() -> None:
    """Test valid ToolRequirements are accepted."""
    req1 = ToolRequirement(uri="https://example.com/tool", hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)
    req2 = ToolRequirement(
        uri="mcp://server/capability", hash="b" * 64, scopes=["read"], risk_level=ToolRiskLevel.STANDARD
    )

    deps = AgentDependencies(tools=[req1, req2])
    assert len(deps.tools) == 2
    assert str(deps.tools[0].uri) == "https://example.com/tool"
    assert deps.tools[1].risk_level == ToolRiskLevel.STANDARD


def test_tools_validation_empty_list() -> None:
    """Test empty list is valid."""
    deps = AgentDependencies(tools=[])
    assert len(deps.tools) == 0


def test_tools_serialization() -> None:
    """Test that tools are serialized correctly."""
    req = ToolRequirement(uri="https://example.com", hash="a" * 64, scopes=[], risk_level="safe")
    deps = AgentDependencies(tools=[req])

    dumped = deps.model_dump()
    assert str(dumped["tools"][0]["uri"]) == "https://example.com/"

    json_dump = deps.model_dump_json()
    assert '"https://example.com/"' in json_dump
