# Recipe Manifests (Workflows)

The `coreason-manifest` package provides the schema definitions for **Recipes**, which are executable workflows managed by the `coreason-maco` runtime.

## Overview

A `RecipeManifest` defines a directed graph of nodes (steps) and edges (connections). It supports architectural triangulation via "Council" configurations and mixed-initiative workflows (human-in-the-loop).

Starting with v2, Recipes strictly define their **Interface** (Inputs/Outputs), **Internal State** (Memory), and **Build-time Parameters**.

## Schema Structure

### RecipeManifest

The root object for a workflow.

- **id**: Unique identifier for the recipe.
- **version**: Semantic version (e.g., `1.0.0`).
- **name**: Human-readable name.
- **description**: Detailed description.
- **interface**: Defines the Input/Output contract (`RecipeInterface`).
- **state**: Defines the internal memory schema (`StateDefinition`).
- **parameters**: Build-time configuration constants (`Dict[str, Any]`).
- **graph**: The topology (`GraphTopology`).

### RecipeInterface

Defines the contract for interacting with the recipe.

- **inputs**: JSON Schema defining valid entry arguments.
- **outputs**: JSON Schema defining the guaranteed structure of the final result.

### StateDefinition

Defines the shared memory available to all nodes in the graph.

- **schema**: JSON Schema of the keys available in the shared memory.
- **persistence**: Configuration for state durability (`ephemeral` or `persistent`).

### GraphTopology

Contains the nodes and edges.

- **nodes**: List of `Node` objects.
- **edges**: List of `Edge` objects.

### Nodes

Nodes are polymorphic and can be one of the following types:

#### 1. AgentNode (`type="agent"`)
Executes a specific atomic agent.
- **agent_name**: The name of the agent to call.

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
from coreason_manifest import (
    RecipeManifest, GraphTopology, AgentNode, HumanNode, Edge
)
from coreason_manifest.recipes import RecipeInterface, StateDefinition

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

# Define Interface
interface = RecipeInterface(
    inputs={
        "type": "object",
        "properties": {
            "topic": {"type": "string"}
        },
        "required": ["topic"]
    },
    outputs={
        "type": "object",
        "properties": {
            "summary": {"type": "string"}
        }
    }
)

# Define State
state = StateDefinition(
    schema={
        "type": "object",
        "properties": {
            "messages": {"type": "array"},
            "draft": {"type": "string"}
        }
    },
    persistence="ephemeral"
)

# Create Manifest
recipe = RecipeManifest(
    id="research_workflow",
    version="1.0.0",
    name="Research Approval Workflow",
    interface=interface,
    state=state,
    parameters={"model": "gpt-4"},
    graph=GraphTopology(
        nodes=[agent_node, human_node],
        edges=[edge]
    )
)

# Dump to JSON (use by_alias=True to correctly serialize state.schema)
print(recipe.model_dump_json(indent=2, by_alias=True))
```
