# Tool Packs (Plugins)

The **Tool Pack** architecture (also known as Plugins) allows you to bundle capabilities—Tools, Skills, and Agents—into a single, distributable unit. This prevents the need to redefine common tools for every agent and supports the concept of reusable "libraries" of capabilities (e.g., a "Stripe Toolkit" or "DevOps Pack").

This architecture is inspired by the Anthropic Plugin structure.

## Overview

A `ToolPackDefinition` is a specialized definition type within the Manifest that groups related components under a common namespace.

### Key Concepts

*   **Pack Metadata**: Includes `name`, `version`, `author`, and `description`, aligning with standard package metadata.
*   **Namespace**: An optional prefix (e.g., `stripe`) that the runtime can use to organize tools (e.g., `stripe.charge`).
*   **Bundling**: A pack can contain:
    *   **Agents**: Specialized sub-agents or helpers.
    *   **Skills**: Procedural knowledge or playbooks.
    *   **Tools**: External or inline tool definitions.
    *   **MCP Servers**: Definitions for Model Context Protocol servers.

## Schema Definition

### ToolPackDefinition

```python
class ToolPackDefinition(CoReasonBaseModel):
    type: Literal["tool_pack"] = "tool_pack"
    id: str  # Unique ID for referencing this pack
    namespace: str | None  # Prefix for components
    metadata: PackMetadata

    # Components
    agents: list[AgentDefinition | str]
    skills: list[SkillDefinition | str]
    tools: list[ToolDefinition | str]
    mcp_servers: list[MCPServerDefinition]
```

### PackMetadata

```python
class PackMetadata(CoReasonBaseModel):
    name: str  # Kebab-case unique identifier
    version: str  # Semantic version
    description: str
    author: str | PackAuthor
    homepage: StrictUri | None
```

### PackAuthor

```python
class PackAuthor(CoReasonBaseModel):
    name: str | None
    email: str | None
    url: StrictUri | None
```

### MCPServerDefinition

Defines a Model Context Protocol server process that provides tools or resources.

```python
class MCPServerDefinition(CoReasonBaseModel):
    type: Literal["mcp_server"] = "mcp_server"
    name: str  # Name of the server
    command: str  # Command to execute
    args: list[str]  # Arguments for the command
    env: dict[str, str]  # Environment variables
```

### MCPResourceDefinition

Defines a passive data stream or resource exposed via MCP.

```python
class MCPResourceDefinition(CoReasonBaseModel):
    type: Literal["resource"] = "resource"
    uri: StrictUri  # URI of the resource
    name: str  # Name of the resource
    mime_type: str | None  # MIME type (optional)
    description: str | None  # Description (optional)
```

## Usage Example

Here is an example of how to define a reusable "Feature Dev Pack" and use it within a Manifest.

```yaml
definitions:
  # A Reusable Pack
  feature-dev-pack:
    type: tool_pack
    id: feature-dev-v1
    namespace: feature_dev
    metadata:
      name: "feature-dev"
      version: "1.0.0"
      description: "Comprehensive feature development workflow."
      author:
        name: "CoReason"
        email: "support@coreason.ai"
        url: "https://coreason.ai"

    # The Pack bundles specific agents and skills
    agents:
      - type: agent
        id: code-architect
        name: "Code Architect"
        role: "Architect"
        goal: "Design robust systems."

    skills:
      - "git-commit-skill"  # Reference to an external skill
      - type: skill         # Inline skill
        id: spec-analysis
        name: "Spec Analyzer"
        description: "Analyzes specifications."
        load_strategy: lazy
        trigger_intent: "Analyze requirements"
        instructions: "..."

    mcp_servers:
      - type: mcp_server
        name: "filesystem"
        command: "npx"
        args: ["-y", "@modelcontextprotocol/server-filesystem", "/users/src"]
        env:
            NODE_ENV: "production"

  # The main agent uses the Pack (future runtime implementation)
  lead-engineer:
    type: agent
    id: lead-engineer
    role: "Lead"
    capabilities:
      packs: ["feature-dev-v1"]
```

## Integration

The `ToolPackDefinition` is integrated into the root `ManifestV2` schema via the `definitions` field. This allows packs to be defined alongside other top-level definitions like Agents and Tools.

### Runtime Resolution

While the Manifest defines the *structure* of a pack, the *runtime* is responsible for:
1.  Resolving references (e.g., expanding string IDs to actual definitions).
2.  applying namespacing to tools and skills.
3.  Mounting MCP servers defined in the pack.
4.  Injecting the pack's capabilities into the context of agents that reference it.
