# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.definitions.agent import AgentDependencies, ToolRequirement, ToolRiskLevel


def test_tools_validation_valid_requirements() -> None:
    """Test valid ToolRequirements are accepted."""
    req1 = ToolRequirement(uri="https://example.com/tool", hash="a" * 64, scopes=[], risk_level=ToolRiskLevel.SAFE)
    req2 = ToolRequirement(
        uri="mcp://server/capability", hash="b" * 64, scopes=["read"], risk_level=ToolRiskLevel.STANDARD
    )

    deps = AgentDependencies(tools=[req1, req2])
    assert len(deps.tools) == 2

    # Assert types to satisfy mypy union checks
    tool0 = deps.tools[0]
    assert isinstance(tool0, ToolRequirement)
    assert str(tool0.uri) == "https://example.com/tool"

    tool1 = deps.tools[1]
    assert isinstance(tool1, ToolRequirement)
    assert tool1.risk_level == ToolRiskLevel.STANDARD


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
