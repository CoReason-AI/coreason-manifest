import pytest
import yaml
from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2, MCPResourceDefinition

def test_mcp_resource_definition():
    res = MCPResourceDefinition(
        name="Application Logs",
        uri="file:///var/log/app.log",
        mimeType="text/plain",
        description="Real-time logs from the application runtime."
    )
    assert res.type == "mcp_resource"
    assert res.name == "Application Logs"
    assert str(res.uri) == "file:///var/log/app.log"
    assert res.mimeType == "text/plain"
    assert res.description == "Real-time logs from the application runtime."
    assert res.is_template is False

def test_mcp_resource_template():
    res = MCPResourceDefinition(
        name="User Profile",
        uri="mem://users/{user_id}/profile",
        is_template=True,
        mimeType="application/json"
    )
    assert res.is_template is True
    # Verify URI handling (encoded braces)
    assert "%7Buser_id%7D" in str(res.uri)

def test_agent_definition_with_resources():
    agent = AgentDefinition(
        id="debugger-agent",
        name="Debugger",
        role="Debugger",
        goal="Fix bugs",
        exposed_mcp_resources=[
            MCPResourceDefinition(
                name="App Logs",
                uri="file:///app/logs.txt"
            )
        ]
    )
    assert len(agent.exposed_mcp_resources) == 1
    assert agent.exposed_mcp_resources[0].name == "App Logs"

def test_manifest_parsing_with_resources():
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Debugger Manifest
workflow:
  start: step1
  steps:
    step1:
      id: step1
      type: logic
      code: "print('hello')"

definitions:
  app-logs:
    type: mcp_resource
    name: "Application Logs"
    uri: "file:///var/log/app.log"
    mimeType: "text/plain"
    description: "Real-time logs from the application runtime."

  user-profile-data:
    type: mcp_resource
    name: "User Profile"
    uri: "mem://users/{user_id}/profile"
    is_template: true
    mimeType: "application/json"

  debugger-agent:
    type: agent
    id: debugger-agent
    name: Debugger
    role: "Debugger"
    goal: "Fix bugs"
    exposed_mcp_resources:
      - name: "Application Logs"
        uri: "file:///var/log/app.log"
"""
    data = yaml.safe_load(yaml_content)
    manifest = ManifestV2(**data)

    assert "app-logs" in manifest.definitions
    assert "user-profile-data" in manifest.definitions

    logs = manifest.definitions["app-logs"]
    assert isinstance(logs, MCPResourceDefinition)
    assert logs.name == "Application Logs"

    agent = manifest.definitions["debugger-agent"]
    assert isinstance(agent, AgentDefinition)
    assert len(agent.exposed_mcp_resources) == 1
    assert agent.exposed_mcp_resources[0].name == "Application Logs"
