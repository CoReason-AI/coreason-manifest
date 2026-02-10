# Agents

## Overview
The Agent module defines the blueprint for an autonomous AI agent. `AgentDefinition` encapsulates identity, tools, and cognitive architecture. `ToolRequirement` handles external dependencies.

## Application Pattern
This pattern shows how to define a minimal agent with a remote tool dependency.

```python
# Example: Creating an Agent Definition
from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    ToolRequirement,
    InterfaceDefinition
)

# Define a tool dependency
github_tool = ToolRequirement(
    uri="mcp://github.com/tools/issue-tracker"
)

# Define the Agent
agent = AgentDefinition(
    id="github_bot",
    name="GitHub Issue Manager",
    role="Project Maintainer",
    goal="Triaging and responding to GitHub issues.",
    tools=[github_tool],
    interface=InterfaceDefinition(
        inputs={"type": "object", "properties": {"issue_url": {"type": "string"}}},
        outputs={"type": "object", "properties": {"summary": {"type": "string"}}}
    )
)
```

## API Reference

### AgentDefinition

::: coreason_manifest.spec.v2.definitions.AgentDefinition

### ToolRequirement

::: coreason_manifest.spec.v2.definitions.ToolRequirement
