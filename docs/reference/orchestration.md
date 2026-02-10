# Orchestration

## Overview
The Orchestration module controls the lifecycle and execution graph of an AI agent workflow (Recipe). It defines the `RecipeDefinition` as the root manifest and `GraphTopology` for the control flow.

## Application Pattern
Here is an example of how to define a simple linear recipe using `RecipeDefinition` and `GraphTopology`.

```python
# Example: Defining a Recipe with a simple Agent loop
from coreason_manifest.spec.v2.recipe import (
    RecipeDefinition,
    GraphTopology,
    AgentNode,
    GraphEdge,
    RecipeStatus
)
from coreason_manifest.spec.v2.definitions import ManifestMetadata

# Define the Nodes
agent_node = AgentNode(
    id="research_agent",
    agent_ref="agents/researcher.yaml",
    system_prompt_override="You are a helpful research assistant."
)

# Define the Graph
topology = GraphTopology(
    nodes=[agent_node],
    edges=[],  # Single node has no edges
    entry_point="research_agent"
)

# Define the Recipe
recipe = RecipeDefinition(
    metadata=ManifestMetadata(
        name="Research Workflow",
        version="1.0.0"
    ),
    status=RecipeStatus.DRAFT,
    topology=topology,
    interface={} # Define inputs/outputs schema
)
```

## API Reference

### RecipeDefinition

::: coreason_manifest.spec.v2.recipe.RecipeDefinition

### GraphTopology

::: coreason_manifest.spec.v2.recipe.GraphTopology

### AgentNode

::: coreason_manifest.spec.v2.recipe.AgentNode
