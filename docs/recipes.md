# Recipe Manifests (Workflows)

The `coreason-manifest` package provides the schema definitions for **Recipes**, which are executable workflows managed by the `coreason-maco` runtime. These definitions share the same underlying graph components (`Node`, `Edge`) as the Agent Topology.

## Overview

A `RecipeManifest` defines a directed graph of nodes (steps) and edges (connections). It supports architectural triangulation via "Council" configurations and mixed-initiative workflows (human-in-the-loop).

## Schema Structure

### RecipeManifest

The root object for a workflow.

- **id**: Unique identifier for the recipe.
- **version**: Semantic version (e.g., `1.0.0`).
- **name**: Human-readable name.
- **description**: Detailed description.
- **inputs**: Global variables the recipe accepts (JSON Schema).
- **graph**: The topology (`GraphTopology`).

### GraphTopology

Contains the nodes and edges.

- **nodes**: List of `Node` objects.
- **edges**: List of `Edge` objects.

### Nodes

Nodes are polymorphic and can be one of the following types:

#### 1. AgentNode (`type="agent"`)
Executes a specific atomic agent.
- **agent_name**: The name of the atomic agent to call.
- **council_config**: Optional configuration for architectural triangulation (e.g., voting).

#### 2. HumanNode (`type="human"`)
Pauses execution for user input or approval.
- **timeout_seconds**: Optional timeout.

#### 3. LogicNode (`type="logic"`)
Executes pure Python logic.
- **code**: The Python code to execute.

### Edges

Connections between nodes.

- **source_node_id**: ID of the source node.
- **target_node_id**: ID of the target node.
- **condition**: Optional Python expression for conditional branching.

## Example Usage

```python
from coreason_manifest.recipes import RecipeManifest
from coreason_manifest.definitions.topology import (
    GraphTopology, AgentNode, HumanNode, Edge
)

# Define Nodes
agent_node = AgentNode(
    id="step_1",
    type="agent",
    agent_name="ResearchAgent",
    visual={"label": "Research Phase"}
)

human_node = HumanNode(
    id="step_2",
    type="human",
    timeout_seconds=3600,
    visual={"label": "Approval"}
)

# Define Edge
edge = Edge(source_node_id="step_1", target_node_id="step_2")

# Create Manifest
recipe = RecipeManifest(
    id="research_workflow",
    version="1.0.0",
    name="Research Approval Workflow",
    description="A simple approval workflow.",
    inputs={"topic": "str"},
    graph=GraphTopology(
        nodes=[agent_node, human_node],
        edges=[edge]
    )
)

print(recipe.model_dump_json(indent=2))
```
