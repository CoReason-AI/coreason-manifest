# MCP Resources

The Coreason Manifest supports the **Model Context Protocol (MCP)** "Resources" primitive, allowing agents to expose passive data streams (such as logs, files, or live status) to the host environment.

This transforms agents from simple "Tool Users" into "Context Providers."

## Overview

MCP Resources are defined in the `exposed_mcp_resources` field of an `AgentDefinition`. They declare *what* data an agent makes available, not *how* it is served (which is handled by the runtime).

## Schema

### MCPResourceDefinition

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `Literal["mcp_resource"]` | Discriminator (Always "mcp_resource"). |
| `name` | `str` | Human-readable name (e.g., "Application Logs"). |
| `uri` | `StrictUri` | The URI of the resource (e.g., `file:///app/logs/latest.log`). |
| `mimeType` | `str` (Optional) | MIME type (e.g., `text/plain`, `application/json`). |
| `description` | `str` (Optional) | Description for the LLM/Host. |
| `is_template` | `bool` | If `True`, the `uri` is a URI Template (RFC 6570). Default `False`. |
| `size_bytes` | `int` (Optional) | Hint about resource size. |

### ResourceScheme

The `uri` scheme must be one of:
*   `file`: Direct file access.
*   `http` / `https`: Web resources.
*   `mem`: Synthetic/In-memory data exposed by the agent.

## Example Usage

### Static Resource (File)

```yaml
definitions:
  debugger-agent:
    type: agent
    id: debugger-agent
    role: "Debugger"
    goal: "Fix bugs"
    exposed_mcp_resources:
      - type: mcp_resource
        name: "Application Logs"
        uri: "file:///var/log/app.log"
        mimeType: "text/plain"
        description: "Real-time logs from the application runtime."
```

### Dynamic Resource (Template)

```yaml
definitions:
  user-agent:
    type: agent
    id: user-agent
    role: "User Manager"
    goal: "Manage users"
    exposed_mcp_resources:
      - type: mcp_resource
        name: "User Profile"
        uri: "mem://users/{user_id}/profile"
        is_template: true
        mimeType: "application/json"
        description: "Get profile for a specific user ID."
```

## Python Usage

```python
from coreason_manifest.spec.v2.definitions import AgentDefinition, MCPResourceDefinition
from coreason_manifest.spec.v2.mcp_defs import ResourceScheme

resource = MCPResourceDefinition(
    name="System Status",
    uri="mem://system/status",
    mimeType="application/json",
    description="Current system health status."
)

agent = AgentDefinition(
    id="sys-admin",
    name="System Admin",
    role="Administrator",
    goal="Maintain system health",
    exposed_mcp_resources=[resource]
)
```
