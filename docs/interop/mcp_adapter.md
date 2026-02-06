# Model Context Protocol (MCP) Adapter

The **Model Context Protocol (MCP)** Adapter enables any `Coreason` agent to be instantly discoverable and usable by MCP-compliant clients (like Claude Desktop, Zed, or other AI IDEs) without writing custom wrappers.

This implementation represents the cutting edge of AI interoperability, projecting `AgentDefinition` interfaces directly into the MCP `Tool` format.

## Installation

The MCP functionality is provided as an optional extra to keep the core library lightweight.

```bash
pip install coreason-manifest[mcp]
```

## Usage

### 1. Converting an Agent to an MCP Tool

You can convert a Coreason Agent Definition into a raw dictionary compatible with the MCP Tool specification.

```python
from coreason_manifest import AgentDefinition, create_mcp_tool_definition

agent = AgentDefinition(
    id="research-agent",
    name="Research Assistant",
    role="Researcher",
    goal="Find information",
    interface={
        "inputs": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
)

tool_def = create_mcp_tool_definition(agent)
print(tool_def)
# Output:
# {
#   "name": "research_assistant",
#   "description": "Find information",
#   "inputSchema": { ... }
# }
```

### 2. Running an MCP Server

The `CoreasonMCPServer` class provides a fully functional MCP Server wrapper around your agent. It adheres to the "Kernel Purity" principle by requiring you to inject the execution logic (`runner_callback`).

```python
import asyncio
from coreason_manifest import AgentDefinition, CoreasonMCPServer

# 1. Define your agent
agent = AgentDefinition(...)

# 2. Define the execution logic (Dependency Injection)
async def my_execution_runner(inputs: dict) -> dict:
    # This is where you would call your actual agent runtime (e.g., Coreason MaCo)
    print(f"Executing agent with: {inputs}")
    return {"status": "success", "data": "Analysis complete."}

# 3. Create the server
server_adapter = CoreasonMCPServer(agent, runner_callback=my_execution_runner)

# 4. Run the server (depends on your transport, e.g., stdio)
# The underlying mcp.Server instance is available at .server
mcp_server = server_adapter.server

# Example: integration with an MCP transport would go here.
# See strict MCP documentation for transport details.
```

## Architecture

*   **Lazy Dependencies:** The `mcp` library is only imported when you use `CoreasonMCPServer` or import from `coreason_manifest.interop.mcp`. It is not a hard dependency.
*   **Strict Type Mapping:** The adapter uses the agent's JSON Schema (`interface.inputs`) directly as the MCP Tool input schema, ensuring perfect type fidelity for LLM callers.
*   **Sanitization:** Agent names are automatically sanitized (spaces to underscores, lowercase) to meet MCP tool naming strictness.
