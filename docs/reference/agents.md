# Agents

## Overview
The Agent module defines the blueprint for an autonomous AI agent. `AgentDefinition` encapsulates identity, tools, and cognitive architecture. `ToolRequirement` handles external dependencies.

This definition works in conjunction with [Agent Capabilities](capabilities.md) to define runtime behavior, and adheres to [Governance Policies](governance.md) for tool safety.

## Application Pattern
This pattern shows how to define a minimal agent with a remote tool dependency.

```python
# Example: Creating an Agent Definition
from coreason_manifest import (
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
# Agent Definition

## Architecture

This diagram illustrates the composition of an `AgentDefinition`, highlighting its relationships with resources (Model), tools, and knowledge.

```mermaid
classDiagram
    %% SOTA Styling Init
    %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffecb3', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#e1f5fe'}}}%%

    class AgentDefinition {
        +str id
        +str name
        +str role
        +str goal
        +str backstory
        +list~str~ knowledge
        +list~str~ skills
        +InterfaceDefinition interface
        +AgentCapabilities capabilities
        +AgentRuntimeConfig runtime
        +EvaluationProfile evaluation
        +ModelProfile resources
    }
    class ModelProfile {
        +str provider
        +str model_id
        +RateCard pricing
        +ResourceConstraints constraints
    }
    class ToolRequirement {
        +str uri
        +str hash
    }
    class InlineToolDefinition {
        +str name
        +str description
        +dict parameters
        +str code_hash
    }
    class InterfaceDefinition {
        +dict inputs
        +dict outputs
    }

    %% Composition
    AgentDefinition *-- ModelProfile : resources
    AgentDefinition *-- InterfaceDefinition : interface

    %% Aggregation/Composition for tools (Polymorphic list)
    AgentDefinition o-- ToolRequirement : tools (reference)
    AgentDefinition *-- InlineToolDefinition : tools (embedded)

    %% Note: Knowledge is represented as a list of strings (IDs/Paths) within AgentDefinition

    %% Styling Classes
    classDef root fill:#ffecb3,stroke:#ffb74d,stroke-width:2px;
    classDef config fill:#e1f5fe,stroke:#4fc3f7,stroke-width:1px;
    classDef tool fill:#e0f2f1,stroke:#4db6ac,stroke-width:1px;

    %% Apply Styles
    class AgentDefinition root;
    class ModelProfile,InterfaceDefinition config;
    class ToolRequirement,InlineToolDefinition tool;
```
