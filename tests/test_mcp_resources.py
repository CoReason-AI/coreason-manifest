import yaml

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2, MCPResourceDefinition
from coreason_manifest.spec.v2.mcp_defs import ResourceScheme


def test_resource_scheme_enum() -> None:
    assert ResourceScheme.FILE.value == "file"
    assert ResourceScheme.HTTP.value == "http"
    assert ResourceScheme.MEM.value == "mem"


def test_mcp_resource_definition_parsing() -> None:
    yaml_content = """
type: mcp_resource
name: "Application Logs"
uri: "file:///var/log/app.log"
mimeType: "text/plain"
description: "Real-time logs from the application runtime."
"""
    data = yaml.safe_load(yaml_content)
    resource = MCPResourceDefinition(**data)
    assert resource.type == "mcp_resource"
    assert resource.name == "Application Logs"
    assert str(resource.uri) == "file:///var/log/app.log"
    assert resource.mimeType == "text/plain"
    assert resource.description == "Real-time logs from the application runtime."
    assert resource.is_template is False


def test_mcp_resource_definition_template() -> None:
    yaml_content = """
type: mcp_resource
name: "User Profile"
uri: "mem://users/{user_id}/profile"
is_template: true
mimeType: "application/json"
"""
    data = yaml.safe_load(yaml_content)
    resource = MCPResourceDefinition(**data)
    assert resource.is_template is True
    # The prompt says: "uri: StrictUri (The strictly formatted URI...)"
    # and "is_template: bool ... uri is a URI Template".
    # We will assert the string representation.
    assert "mem://users/" in str(resource.uri)


def test_agent_definition_with_resources() -> None:
    yaml_content = """
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
    agent = AgentDefinition(**data)
    assert len(agent.exposed_mcp_resources) == 1
    assert agent.exposed_mcp_resources[0].name == "Application Logs"
    assert str(agent.exposed_mcp_resources[0].uri) == "file:///var/log/app.log"


def test_manifest_parsing_with_resources() -> None:
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Resource Manifest
workflow:
  start: step1
  steps:
    step1:
      id: step1
      type: logic
      code: "pass"
definitions:
  # A resource that points to a specific log file
  app-logs:
    type: mcp_resource
    name: "Application Logs"
    uri: "file:///var/log/app.log"
    mimeType: "text/plain"
    description: "Real-time logs from the application runtime."

  # A dynamic resource template
  user-profile-data:
    type: mcp_resource
    name: "User Profile"
    uri: "mem://users/{user_id}/profile"
    is_template: true
    mimeType: "application/json"

  # The Agent exposing these resources
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
    manifest_data = yaml.safe_load(yaml_content)
    manifest = ManifestV2(**manifest_data)

    assert "app-logs" in manifest.definitions
    assert isinstance(manifest.definitions["app-logs"], MCPResourceDefinition)

    assert "user-profile-data" in manifest.definitions
    assert isinstance(manifest.definitions["user-profile-data"], MCPResourceDefinition)

    assert "debugger-agent" in manifest.definitions
    agent = manifest.definitions["debugger-agent"]
    assert isinstance(agent, AgentDefinition)
    assert len(agent.exposed_mcp_resources) == 1


def test_edge_case_empty_resources() -> None:
    yaml_content = """
type: agent
id: simple-agent
name: Simple
role: "Simple"
goal: "Be simple"
exposed_mcp_resources: []
"""
    data = yaml.safe_load(yaml_content)
    agent = AgentDefinition(**data)
    assert agent.exposed_mcp_resources == []


def test_complex_mixed_resources() -> None:
    yaml_content = """
type: agent
id: complex-agent
name: Complex
role: "Complex"
goal: "Be complex"
exposed_mcp_resources:
  - name: "Log File"
    uri: "file:///var/log/syslog"
  - name: "Web Hook"
    uri: "https://api.example.com/status"
  - name: "Memory Dump"
    uri: "mem://debug/dump"
"""
    data = yaml.safe_load(yaml_content)
    agent = AgentDefinition(**data)
    resources = agent.exposed_mcp_resources
    assert len(resources) == 3
    schemes = {str(r.uri).split(":")[0] for r in resources}
    assert "file" in schemes
    assert "https" in schemes
    assert "mem" in schemes


def test_mcp_resource_equality() -> None:
    res1 = MCPResourceDefinition(name="Res1", uri="file:///tmp/1")
    res2 = MCPResourceDefinition(name="Res1", uri="file:///tmp/1")
    res3 = MCPResourceDefinition(name="Res2", uri="file:///tmp/2")

    assert res1 == res2
    assert res1 != res3
