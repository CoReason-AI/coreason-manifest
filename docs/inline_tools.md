# Inline Tools: Serverless Agents

Coreason V2 introduces **Inline Tool Definitions**, enabling the creation of "Serverless Agents." These agents define their tool schemas directly within the manifest, allowing the runtime to inject implementation logic (e.g., via Code Interpreter or local functions) without requiring a separate MCP (Model Context Protocol) server.

## Concept: Serverless Capabilities

Traditionally, tools required a running MCP server. With Inline Tools, you can define the *interface* (JSON Schema) of a tool, and let the runtime handle the *implementation*. This is perfect for:
*   **Simple Logic**: Math, formatting, string manipulation.
*   **Ad-hoc Tasks**: One-off data transformations.
*   **Code Interpretation**: Defining functions that the LLM generates code for.

## Schema Definition

An `InlineToolDefinition` requires:
*   **`type`**: Must be `"inline"`.
*   **`name`**: The function name (e.g., `calculate_sum`).
*   **`description`**: What the tool does.
*   **`parameters`**: A valid JSON Schema object defining the arguments.

### Example: The Calculator Agent

Here is an `AgentDefinition` that possesses a built-in calculator tool. It does not need to connect to any external service to perform math.

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

print(f"Agent '{agent.name}' has {len(agent.tools)} tool(s).")
```

## Mixed Mode: Inline + Remote

Agents can mix and match Inline Tools with traditional Remote Tools (MCP).

```yaml
# yaml-language-server: $schema=../schema.json
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Hybrid Agent

definitions:
  hybrid_agent:
    type: agent
    id: hybrid-agent
    name: Hybrid Worker
    role: Assistant
    goal: Help the user
    tools:
      # 1. Inline Tool (Local)
      - type: inline
        name: get_current_time
        description: "Returns the current UTC time."
        parameters:
          type: object
          properties: {}

      # 2. Remote Tool (MCP Server)
      - type: remote
        uri: "mcp://google-search/v1"
```
