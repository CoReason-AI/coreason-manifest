# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.resources import McpServerRequirement, RuntimeEnvironment, ToolDefinition, ToolParameter


def test_tool_parameter() -> None:
    param = ToolParameter(name="query", type="string", description="Search query")
    assert param.name == "query"
    assert param.type == "string"
    assert param.required is True


def test_tool_definition() -> None:
    tool = ToolDefinition(
        name="brave_search",
        description="Search the web",
        parameters={"properties": {"query": {"type": "string"}}},
        is_consequential=True,
        namespace="brave",
    )
    assert tool.name == "brave_search"
    assert tool.is_consequential is True
    assert tool.namespace == "brave"


def test_runtime_environment() -> None:
    mcp_req = McpServerRequirement(name="github", required_tools=["create_issue"])
    env = RuntimeEnvironment(mcp_servers=[mcp_req], python_version="3.11")
    assert env.mcp_servers[0].name == "github"
    assert env.python_version == "3.11"

    # Test defaults
    env_default = RuntimeEnvironment()
    assert env_default.mcp_servers == []
    assert env_default.python_version == "3.12"
