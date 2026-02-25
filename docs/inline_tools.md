# Tools: Inline & Remote

Coreason Manifest V2 supports a flexible tool definition system, allowing agents to use both "Serverless" inline tools and remote MCP (Model Context Protocol) servers.

## Tool Types

The `tools` field in an `AgentDefinition` supports three distinct reference types:

1.  **Inline Definitions**: Full tool schema embedded directly in the agent (Serverless).
2.  **Remote Requirements**: Direct reference to an external MCP server via URI.
3.  **ID References**: Reference to a shared `ToolDefinition` block defined elsewhere in the manifest.

---

## 1. Inline Tools (Serverless)

**Inline Tool Definitions** allow you to define the *interface* (JSON Schema) of a tool directly within the manifest. This enables the runtime to inject implementation logic (e.g., via Code Interpreter or local functions) without requiring a separate MCP server.

### Schema
An `InlineToolDefinition` requires:
*   **`type`**: Must be `"inline"`.
*   **`name`**: The function name (e.g., `calculate_sum`).
*   **`description`**: What the tool does.
*   **`parameters`**: A valid JSON Schema object defining the arguments.

### Example: Calculator

```python
from coreason_manifest.spec.v2.definitions import AgentDefinition, InlineToolDefinition

agent = AgentDefinition(
    id="math-agent",
    name="Math Wizard",
    role="Mathematician",
    goal="Solve complex problems",
    tools=[
        InlineToolDefinition(
            name="calculate",
            description="Perform a mathematical calculation.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2')."
                    }
                },
                "required": ["expression"]
            }
        )
    ]
)
```

---

## 2. Remote Requirements (MCP)

For standard MCP servers, you can reference them directly by URI.

```yaml
tools:
  - type: remote
    uri: "mcp://google-search/v1"
```

*Shorthand:* You can also just provide the string URI, and the parser will auto-convert it.
```yaml
tools:
  - "mcp://google-search/v1"
```

---

## 3. ID References (Shared Definitions)

If multiple agents share the same tool configuration (e.g., specific risk levels), you can define it once in the `definitions` block and reference it by ID.

```yaml
definitions:
  # Shared Definition
  web-search:
    type: tool
    id: web-search-tool
    name: Google Search
    uri: mcp://google
    risk_level: critical  # Enforce strict policy

  researcher:
    type: agent
    tools:
      - "web-search-tool" # References the ID above
```

---

## Mixed Mode Example

Agents can mix and match all three types.

```yaml
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Hybrid Agent

definitions:
  hybrid_agent:
    type: agent
    id: hybrid-agent
    tools:
      # 1. Inline (Local)
      - type: inline
        name: get_time
        description: "Get current time"
        parameters: {type: object, properties: {}}

      # 2. Remote (External)
      - type: remote
        uri: "mcp://weather-service"

      # 3. Reference (Shared)
      - "corporate-knowledge-base"
```
