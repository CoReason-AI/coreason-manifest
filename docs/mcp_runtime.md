# MCP Runtime & Governance

Coreason Manifest V2.2 (introduced in 0.22.0) adds first-class support for the **Model Context Protocol (MCP)**, allowing Recipes to declare their infrastructure requirements and govern tool access.

This document describes the schema for defining **Tool Capabilities**, **Runtime Environments**, and **Governance Policies**.

## 1. Tool Capabilities (`ToolDefinition`)

To enable static analysis and planning, tools must be defined with a schema that describes their interface. The `ToolDefinition` schema allows you to specify inputs, descriptions, and governance metadata.

```python
from coreason_manifest.spec.v2.resources import ToolDefinition, ToolParameter

tool = ToolDefinition(
    name="brave_search",
    description="Search the web for real-time information.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "count": {"type": "integer", "default": 5}
        },
        "required": ["query"]
    },
    # Critical for MCP Governance
    is_consequential=False,
    namespace="brave"
)
```

### Key Fields
*   **`name`**: The unique identifier for the tool (e.g., `github.create_issue`).
*   **`parameters`**: A JSON Schema object defining the expected inputs.
*   **`is_consequential`**: A boolean flag (default `False`). If `True`, the MCP Runtime MUST require human approval before executing this tool (side-effect protection).
*   **`namespace`**: The expected MCP server namespace (e.g., `github`).

## 2. Infrastructure Requirements (`RuntimeEnvironment`)

A Recipe can now declare the "Hardware" (MCP Servers) it requires to run. This allows the runtime to pre-flight check that all necessary connections are available before starting execution.

This is defined in the `environment` field of `RecipeDefinition`.

```python
from coreason_manifest.spec.v2.resources import RuntimeEnvironment, McpServerRequirement

environment = RuntimeEnvironment(
    mcp_servers=[
        McpServerRequirement(
            name="github",
            required_tools=["create_issue", "list_pull_requests"],
            version_constraint=">=1.0.0"
        ),
        McpServerRequirement(
            name="brave-search",
            required_tools=["search"]
        )
    ],
    python_version="3.12"
)
```

### `McpServerRequirement`
*   **`name`**: The name of the MCP server (must match the server configuration in the runtime).
*   **`required_tools`**: A list of tool names that *must* be available on this server.
*   **`version_constraint`**: Semantic version string (e.g., `>=1.0`) to ensure compatibility.

## 3. Governance Policy (`PolicyConfig`)

The `PolicyConfig` schema has been updated to support MCP-specific governance rules. Specifically, you can whitelist which MCP servers a recipe is allowed to access.

```python
from coreason_manifest.spec.v2.recipe import PolicyConfig

policy = PolicyConfig(
    max_retries=3,
    budget_cap_usd=10.0,
    # Whitelist of allowed MCP servers
    allowed_mcp_servers=["github", "brave-search"],
    # Tools that always require human confirmation
    sensitive_tools=["github.delete_repo"]
)
```

### `allowed_mcp_servers`
A list of strings representing the names of MCP servers that this recipe is permitted to access. If an agent attempts to use a tool from a server not in this list, the execution will be blocked by the governance layer.

## Full Example: Recipe with MCP Support

Here is a complete example of a `RecipeDefinition` that uses these new features.

```python
from coreason_manifest.spec.v2.recipe import (
    RecipeDefinition,
    PolicyConfig,
    RecipeInterface,
    AgentNode,
    GraphTopology,
    RecipeStatus
)
from coreason_manifest.spec.v2.resources import RuntimeEnvironment, McpServerRequirement
from coreason_manifest.spec.v2.definitions import ManifestMetadata

# 1. Define Environment
env = RuntimeEnvironment(
    mcp_servers=[
        McpServerRequirement(name="github", required_tools=["create_issue"])
    ]
)

# 2. Define Policy
policy = PolicyConfig(
    allowed_mcp_servers=["github"],
    sensitive_tools=["github.delete_repo"] # Extra safety
)

# 3. Define Recipe
recipe = RecipeDefinition(
    metadata=ManifestMetadata(name="Github Issue Creator"),
    interface=RecipeInterface(inputs={"title": {"type": "string"}}),
    environment=env,
    policy=policy,
    status=RecipeStatus.DRAFT,
    topology=GraphTopology(
        entry_point="create-task",
        nodes=[
            AgentNode(
                id="create-task",
                agent_ref="github-agent",
                inputs_map={"title": "title"}
            )
        ],
        edges=[]
    )
)
```
