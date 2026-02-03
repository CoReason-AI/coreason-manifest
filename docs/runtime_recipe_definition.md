# Runtime Recipe Definition

The **Runtime Recipe Definition** (`RecipeManifest`) describes executable workflows managed by the `coreason-maco` runtime. These definitions serve as the "Machine Code" or "Intermediate Representation" (IR) that the execution engine understands.

While developers typically author workflows using the [Coreason Agent Manifest (V2)](coreason_agent_manifest.md) YAML format, they are compiled down to this structure for execution.

## Overview

A `RecipeManifest` defines a directed graph of nodes (steps) and edges (connections). It supports architectural triangulation via "Council" configurations and mixed-initiative workflows (human-in-the-loop).

It strictly defines:
*   **Interface**: Inputs and Outputs (JSON Schema).
*   **Internal State**: Shared memory schema and persistence.
*   **Topology**: The graph of execution nodes and edges.
*   **Policy**: Governance rules like timeouts and retries.

## Schema Structure

### RecipeManifest

The root object for a workflow, defined in `src/coreason_manifest/recipes.py`.

```python
class RecipeManifest(CoReasonBaseModel):
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier for the recipe. |
| `version` | `VersionStr` | Semantic version (e.g., `1.0.0`). |
| `name` | `str` | Human-readable name. |
| `description` | `Optional[str]` | Detailed description. |
| `interface` | `RecipeInterface` | Defines the Input/Output contract. |
| `state` | `StateDefinition` | Defines the internal memory schema. |
| `policy` | `Optional[PolicyConfig]` | Policy configuration. |
| `parameters` | `Dict[str, Any]` | Build-time configuration constants. |
| `topology` | `GraphTopology` | The topology definition of the workflow. |
| `integrity_hash` | `Optional[str]` | SHA256 hash of the topology. |
| `metadata` | `Dict[str, Any]` | Container for design-time data. |

### Core Components

#### 1. Interface (`RecipeInterface`)

Defines the contract for interacting with the recipe.

- **inputs**: JSON Schema defining valid entry arguments.
- **outputs**: JSON Schema defining the guaranteed structure of the final result.

#### 2. State (`StateDefinition`)

Defines the shared memory available to all nodes in the graph.

- **schema**: JSON Schema of the keys available in the shared memory.
- **persistence**: Configuration for state durability (`ephemeral` or `persistent`).

#### 3. Policy (`PolicyConfig`)

Configuration for execution policy and governance.

- **max_steps**: Execution limit on number of steps.
- **max_retries**: Maximum number of retries.
- **timeout**: Timeout in seconds.
- **human_in_the_loop**: Whether to require human approval.

#### 4. Topology (`GraphTopology`)

The core execution graph.

- **nodes**: List of `Node` objects.
- **edges**: List of `Edge` or `ConditionalEdge` objects.
- **state_schema**: (Optional) Definition of the graph's state structure and persistence.

**Validation**: The topology enforces integrity by ensuring that every `source_node_id` and `target_node_id` referenced in edges exists within the `nodes` list.

## Nodes

Nodes are the atomic units of execution, defined as a polymorphic union.

### AgentNode (`type="agent"`)
Executes a specific atomic agent.
- `agent_name`: The name of the atomic agent to call.
- `system_prompt`: Overrides the registry default prompt.
- `config`: Runtime-specific configuration (e.g., model parameters).
- `council_config`: Optional configuration for architectural triangulation (e.g., voting).
- `overrides`: Optional runtime overrides.

### HumanNode (`type="human"`)
Pauses execution for user input or approval.
- `timeout_seconds`: Optional timeout.

### LogicNode (`type="logic"`)
Executes pure Python logic.
- `code`: The Python logic code to execute.

### RecipeNode (`type="recipe"`)
Executes another Recipe as a sub-graph (Hierarchical Composition).
- `recipe_id`: ID of the child recipe.
- `input_mapping`: Map parent state to child inputs.
- `output_mapping`: Map child outputs to parent state.

### MapNode (`type="map"`)
Executes a sub-branch in parallel for each item in a list (Map-Reduce).
- `items_path`: Path to the list in the state (e.g., `state.documents`).
- `processor_node_id`: The node (or subgraph) to run for each item.
- `concurrency_limit`: Max parallel executions.

## Edges

Edges define the control flow between nodes.

### Standard Edge (`Edge`)
Simple transition or conditional branch.
- `source_node_id`: ID of the source node.
- `target_node_id`: ID of the target node.
- `condition`: Optional Python expression for conditional branching.

### Conditional Edge (`ConditionalEdge`)
Dynamic routing where one source can lead to multiple targets.
- `source_node_id`: ID of the source node.
- `router_logic`: A `RouterDefinition` determining the path.
- `mapping`: Map of router output values to target node IDs.

### Router Definition

The `router_logic` field accepts a `RouterDefinition`, which is a union of:

1.  **`RouterRef` (String):** A dotted-path reference to a Python function (e.g., `my_module.routers.my_function`).
2.  **`RouterExpression` (Object):** A structured logic expression with `operator` and `args`.

## Example Usage

```python
from coreason_manifest import (
    RecipeManifest, GraphTopology, AgentNode, HumanNode, Edge,
    ConditionalEdge, StateDefinition
)
from coreason_manifest.recipes import RecipeInterface

# Define Nodes
agent_node = AgentNode(
    id="step_1",
    type="agent",
    agent_name="ResearchAgent",
    visual={"label": "Research Phase"},
    overrides={"temperature": 0.2}
)

human_node = HumanNode(
    id="step_2",
    type="human",
    timeout_seconds=3600,
    visual={"label": "Approval"},
    metadata={"cost_center": "marketing"}
)

# Define Dynamic Routing
router = ConditionalEdge(
    source_node_id="step_2",
    router_logic="logic.approve_or_reject",
    mapping={
        "approved": "step_3_publish",
        "rejected": "step_1_revise"
    }
)

# Define State Schema
state_def = StateDefinition(
    schema={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "messages": {"type": "array"},
            "draft": {"type": "string"}
        }
    },
    persistence="persistent"
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

# Create Manifest
recipe = RecipeManifest(
    id="research_workflow",
    version="1.0.0",
    name="Research Approval Workflow",
    interface=interface,
    state=state_def,
    parameters={"model": "gpt-4"},
    description="A simple approval workflow.",
    topology=GraphTopology(
        nodes=[agent_node, human_node], # + referenced nodes
        edges=[Edge(source_node_id="step_1", target_node_id="step_2"), router],
        state_schema=state_def
    )
)

# Dump to JSON
print(recipe.model_dump_json(indent=2, by_alias=True))
```
