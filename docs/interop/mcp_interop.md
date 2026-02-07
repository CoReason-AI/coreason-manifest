# Model Context Protocol (MCP) Interoperability

The `coreason-manifest` library supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) as a first-class citizen for interoperability. This allows Coreason Agents to be seamlessly consumed by any MCP-compliant client (e.g., Claude Desktop, IDEs, or other agents).

## Overview

Coreason Agents are defined by strict `inputs` and `outputs` schemas in their `InterfaceDefinition`. This contract-first approach makes them perfect candidates for MCP Tools.

The library provides an **MCP Adapter** in `coreason_manifest.interop.mcp` that automatically projects an `AgentDefinition` into an MCP Tool structure.

## Installation

To use MCP features, you must install the optional dependency:

```bash
pip install coreason-manifest[mcp]
```

## Contract Verification (Mock Server)

The CLI includes a `serve-mcp` command designed for **Contract Verification**. It serves your agent as an MCP Tool over stdio, but instead of running the actual agent logic (which might require API keys, databases, or complex state), it uses the **Mock Generator** to produce valid, schema-compliant outputs.

This allows you to verify that your agent's interface is correctly understood by consumers *before* implementing the full logic.

### Usage

```bash
# Serve your agent definition
coreason serve-mcp my_agent.py:agent
```

### Example Workflow with Claude Desktop

1.  Define your agent in `agent.py`.
2.  Add the server config to `claude_desktop_config.json`:

    ```json
    {
      "mcpServers": {
        "my-agent": {
          "command": "coreason",
          "args": ["serve-mcp", "/absolute/path/to/my_agent.py:agent"]
        }
      }
    }
    ```

3.  Restart Claude Desktop.
4.  You can now "chat" with your agent definition. The tool call will return mocked data structure, proving that the input/output contract is valid.

## Using the Adapter Programmatically

You can also use the adapter in your own code to integrate Coreason Agents into custom MCP servers.

```python
from coreason_manifest.interop.mcp import CoreasonMCPServer, create_mcp_tool_definition
from my_agent import agent_definition

# 1. Get the raw tool schema
tool_schema = create_mcp_tool_definition(agent_definition)
print(tool_schema)

# 2. Create a server instance (requires an async runner callback)
async def my_runner(args: dict) -> dict:
    # Implement your actual execution logic here!
    return {"result": "Real execution result"}

server = CoreasonMCPServer(agent_definition, my_runner)

# 3. Run the server (e.g., over stdio)
import asyncio
asyncio.run(server.run_stdio())
```

This architecture allows the `coreason-manifest` library to remain a pure data definition library while enabling powerful runtime integrations through the toolbelt.
