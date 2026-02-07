# Inline Tool Definitions

Coreason Manifest V2 supports **Inline Tool Definitions**, allowing you to define tools directly within an Agent's manifest. This capability enables "Serverless Agents" that do not require external MCP (Model Context Protocol) servers for simple logic like calculation, formatting, or data transformation.

## Overview

The `tools` field in an `AgentDefinition` supports three types of entries:

1.  **ID Reference**: A string pointing to a `ToolDefinition` in the `definitions` section (Legacy/Standard).
2.  **Remote Requirement**: A direct reference to an external MCP server via URI.
3.  **Inline Definition**: A full tool definition embedded directly in the list, including its schema.

## 1. ID Reference (Standard)

The tool is defined in the `definitions` block and referenced by its ID.

```yaml
definitions:
  my_tool:
    type: tool
    id: tool-1
    name: Search
    uri: mcp://search-server
    risk_level: safe

  my_agent:
    type: agent
    tools: ["tool-1"]  # References 'tool-1' above
```

## 2. Remote Requirement

You can reference a remote tool directly by its URI without creating a separate definition block.

```yaml
definitions:
  my_agent:
    type: agent
    tools:
      - type: remote
        uri: "mcp://weather-server"
      # Shorthand string format is also supported and auto-converted:
      # - "mcp://weather-server"
```

## 3. Inline Definition (Serverless)

You can define the tool's interface (JSON Schema) directly. This is ideal for tools where the implementation might be injected by the runtime or handled via code interpretation.

```yaml
definitions:
  calculator_agent:
    type: agent
    name: Math Wizard
    tools:
      - type: inline
        name: add_numbers
        description: "Adds two numbers together."
        parameters:
          type: object
          properties:
            a:
              type: integer
              description: "First number"
            b:
              type: integer
              description: "Second number"
          required: ["a", "b"]
```

## Validation Logic

The system enforces strict validation on the `tools` list:

*   **Polymorphism**: The list can contain mixed types (references, remote requirements, and inline definitions).
*   **Normalization**: String entries are automatically converted to `ToolRequirement(type="remote", uri=...)` for backward compatibility.
*   **Integrity**:
    *   If a tool entry is a **ID Reference** (simple string like `tool-1`), it **must** exist in the `definitions` block.
    *   If a tool entry is a **Remote URI** (e.g., `mcp://...`), it is valid even if not explicitly defined in `definitions`.
    *   **Inline Tools** are self-contained and require valid JSON Schema in the `parameters` field.

## Example: Mixed Usage

```yaml
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Hybrid Agent
definitions:
  # Shared Tool Definition
  shared_search:
    type: tool
    id: search
    name: Google Search
    uri: mcp://google
    risk_level: standard

  my_agent:
    type: agent
    id: hybrid_agent
    tools:
      # 1. Reference to shared definition
      - "search"

      # 2. Direct remote reference
      - type: remote
        uri: "mcp://calculator"

      # 3. Inline definition
      - type: inline
        name: format_date
        description: "Format a date string."
        parameters:
          type: object
          properties:
            date: {type: string}
            format: {type: string}
```
