# Recipe Manifests (Workflows)

The `coreason-manifest` package provides the schema definitions for **Recipes**, which are executable workflows managed by the `coreason-maco` runtime. These definitions share the same underlying graph components (`Node`, `Edge`) as the Agent Topology.

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

Contains the nodes and edges, plus state configuration.

- **nodes**: List of `Node` objects.
- **edges**: List of `Edge` or `ConditionalEdge` objects.
- **state_schema**: (Optional) Definition of the graph's state structure and persistence.

#### StateSchema

Defines the data structure passed between nodes.

- **data_schema**: JSON Schema or Pydantic definition.
- **persistence**: Checkpointing strategy (e.g., `'memory'`, `'redis'`).

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

#### 4. RecipeNode (`type="recipe"`)
Executes another Recipe as a sub-graph (Hierarchical Composition).
- **recipe_id**: ID of the child recipe.
- **input_mapping**: Map parent state to child inputs.
- **output_mapping**: Map child outputs to parent state.

#### 5. MapNode (`type="map"`)
Executes a sub-branch in parallel for each item in a list (Map-Reduce).
- **items_path**: Path to the list in the state (e.g., `state.documents`).
- **processor_node_id**: The node/subgraph to run for each item.
- **concurrency_limit**: Max parallel executions.

### Edges

Connections between nodes.

#### Standard Edge
Simple transition.
- **source_node_id**: ID of the source node.
- **target_node_id**: ID of the target node.
- **condition**: Optional Python expression for conditional branching.

#### ConditionalEdge (Dynamic Routing)
Routes to one of multiple targets based on logic.
- **source_node_id**: ID of the source node.
- **router_logic**: Python function or expression determining the path.
- **mapping**: Map of router output values to target node IDs.

## Edge Cases & Validation

The schema enforces strict validation to prevent runtime errors. Common edge cases include:

1.  **Missing Routing Mapping**: A `ConditionalEdge` must have a non-empty `mapping` dictionary. Runtime logic that returns a value not present in `mapping` will cause an execution error.
2.  **Invalid Map-Reduce Config**: `MapNode` requires `concurrency_limit > 0`. A limit of 0 or negative will raise a validation error.
3.  **Recursion**: While `RecipeNode` allows nesting, the runtime is responsible for detecting infinite recursion loops (e.g., Recipe A -> Recipe B -> Recipe A).
4.  **State Schema Mismatch**: If a `state_schema` is defined, all nodes must output data compliant with that schema. This is enforced at runtime.

## Example Usage

```python
from coreason_manifest import (
    RecipeManifest, GraphTopology, AgentNode, HumanNode, Edge,
    ConditionalEdge, StateSchema
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

# Define Dynamic Routing
router = ConditionalEdge(
    source_node_id="step_2",
    router_logic="lambda state: 'approved' if state['approved'] else 'rejected'",
    mapping={
        "approved": "step_3_publish",
        "rejected": "step_1_revise"
    }
)

# Define State
state = StateSchema(
    data_schema={"type": "object", "properties": {"approved": {"type": "boolean"}}},
    persistence="redis"
)

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
    description="A simple approval workflow.",
    inputs={"topic": "str"},
    graph=GraphTopology(
        nodes=[agent_node, human_node],
        edges=[Edge(source_node_id="step_1", target_node_id="step_2"), router],
        state_schema=state
    )
)

# Dump to JSON (use by_alias=True to correctly serialize state.schema)
print(recipe.model_dump_json(indent=2, by_alias=True))
```
