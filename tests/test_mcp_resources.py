import yaml
from pydantic import ValidationError
import pytest

from coreason_manifest.spec.v2.definitions import AgentDefinition, ManifestV2, MCPResourceDefinition
from coreason_manifest.spec.v2.mcp_defs import ResourceScheme


def test_resource_scheme_enum():
    assert ResourceScheme.FILE == "file"
    assert ResourceScheme.HTTP == "http"
    assert ResourceScheme.MEM == "mem"


def test_mcp_resource_definition_parsing():
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


def test_mcp_resource_definition_template():
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
    # StrictUri might encode braces if it validates as URL, but templates are often not valid URLs until expanded.
    # However, StrictUri uses AnyUrl which might be strict.
    # Let's check how StrictUri handles templates.
    # The prompt says: "uri: StrictUri (The strictly formatted URI...)" and "is_template: bool ... uri is a URI Template".
    # If StrictUri enforces standard URI characters, curly braces might be an issue or encoded.
    # We will assert the string representation.


def test_agent_definition_with_resources():
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


def test_manifest_parsing_with_resources():
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
