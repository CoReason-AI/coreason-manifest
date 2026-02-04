# Runtime Recipe Definition (V1)

The **Runtime Recipe Definition** (often referred to as the V1 Recipe Manifest) is the strict, machine-optimized Pydantic model used by the Coreason Engine (MACO) to execute workflows. Unlike the [Coreason Agent Manifest (CAM V2)](../cap/specification.md), which is designed for human authoring, this format is designed for runtime validation, integrity, and performance.

> **Note:** V1 components have been moved to the `coreason_manifest.v1` namespace. This document describes the internal runtime format which is typically generated from V2 manifests via the V2 Bridge.

The root of the specification is the `RecipeManifest` class. It serves as the shared contract between the **Engine** (runtime) and the **Builder** (visual editor).

## Root Object (`RecipeManifest`)

```python
class RecipeManifest(CoReasonBaseModel):
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `str` | Unique identifier for the recipe. |
| `version` | `VersionStr` | Semantic version of the recipe (e.g., "1.0.0"). |
| `name` | `str` | Human-readable name of the recipe. |
| `description` | `Optional[str]` | Detailed description of the recipe. |
| `interface` | `RecipeInterface` | Defines the input/output contract for the Recipe. |
| `state` | `StateDefinition` | Defines the internal state (memory) of the Recipe. |
| `policy` | `Optional[PolicyConfig]` | Policy configuration. |
| `parameters` | `Dict[str, Any]` | Dictionary of build-time constants. |
| `topology` | `GraphTopology` | The topology definition of the workflow. |
| `integrity_hash` | `Optional[str]` | SHA256 hash of the canonical JSON representation of the topology. |
| `metadata` | `Dict[str, Any]` | Container for design-time data (UI coordinates, resolution logs). |

## Core Components

### 1. Interface (`RecipeInterface`)

Defines the contract for interacting with the recipe. This ensures that any caller (whether a user or another parent recipe) knows exactly what arguments to provide and what results to expect.

| Field | Type | Description |
| :--- | :--- | :--- |
| `inputs` | `Dict[str, Any]` | JSON Schema defining valid entry arguments. |
| `outputs` | `Dict[str, Any]` | JSON Schema defining the guaranteed structure of the final result. |

### 2. State (`StateDefinition`)

Defines the internal memory available to all nodes in the graph.

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema` | `Dict[str, Any]` | JSON Schema of the keys available in the shared memory. |
| `persistence` | `Literal["ephemeral", "persistent"]` | Configuration for state durability. Defaults to "ephemeral". |

### 3. Policy (`PolicyConfig`)

Configuration for execution policy and governance.

- **max_steps**: Execution limit on number of steps.
- **max_retries**: Maximum number of retries.
- **timeout**: Timeout in seconds.
- **human_in_the_loop**: Whether to require human approval.

### 4. Topology (`GraphTopology`)

The core execution graph. It contains the nodes and edges that define the workflow logic.

| Field | Type | Description |
| :--- | :--- | :--- |
| `nodes` | `List[Node]` | List of nodes in the graph. |
| `edges` | `List[Union[Edge, ConditionalEdge]]` | List of edges connecting the nodes. |
| `state_schema` | `Optional[StateDefinition]` | Optional schema definition for the graph state. |

**Validation Rule:** The topology enforces integrity by ensuring that every `source_node_id` and `target_node_id` referenced in edges exists within the `nodes` list.

## Nodes (`Node`)

Nodes are the atomic units of execution. The `Node` type is a polymorphic union of several specific node types.

Common attributes for all nodes (`BaseNode`):
- `id`: Unique identifier.
- `council_config`: Optional configuration for architectural triangulation (voting).
- `visual`: Visual metadata for the UI (icon, label, coordinates).
- `metadata`: Generic metadata for operational context (cost tracking, SLAs).

### AgentNode (`type="agent"`)
Executes a specific atomic agent.
- `agent_name` (`str`): The name of the atomic agent to call.
- `system_prompt` (`Optional[str]`): Overrides the registry default prompt.
- `config` (`Optional[Dict[str, Any]]`): Runtime-specific configuration (e.g., model parameters).
- `overrides` (`Optional[Dict[str, Any]]`): Runtime overrides for the agent.

### HumanNode (`type="human"`)
Pauses execution for user input or approval.
- `timeout_seconds` (`Optional[int]`): Optional timeout in seconds.

### LogicNode (`type="logic"`)
Executes pure Python logic.
- `code` (`str`): The Python logic code to execute.

### RecipeNode (`type="recipe"`)
Executes another Recipe as a sub-graph (Hierarchical Composition).
- `recipe_id` (`str`): The ID of the recipe to execute.
- `input_mapping` (`Dict`): Mapping of parent state keys to child input keys.
- `output_mapping` (`Dict`): Mapping of child output keys to parent state keys.

### MapNode (`type="map"`)
Spawns multiple parallel executions of a sub-branch (Map-Reduce).
- `items_path` (`str`): Dot-notation path to the list in the state.
- `processor_node_id` (`str`): The node (or subgraph) to run for each item.
- `concurrency_limit` (`int`): Max parallel executions.

## Edges (`Edge`)

Edges define the control flow between nodes.

### Standard Edge
Represents a direct connection or a simple conditional branch.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_node_id` | `str` | The ID of the source node. |
| `target_node_id` | `str` | The ID of the target node. |
| `condition` | `Optional[str]` | Optional Python expression for conditional branching. |

### ConditionalEdge
Represents dynamic routing where one source can lead to multiple possible targets based on logic.

| Field | Type | Description |
| :--- | :--- | :--- |
| `source_node_id` | `str` | The ID of the source node. |
| `router_logic` | `RouterDefinition` | A reference to a python function or a logic expression that determines the path. |
| `mapping` | `Dict[str, str]` | Map of router output values to target node IDs. |

### RouterDefinition

The `router_logic` field accepts a `RouterDefinition`, which is a union of:

1.  **`RouterRef` (String):** A dotted-path reference to a Python function (e.g., `my_module.routers.my_function`).
2.  **`RouterExpression` (Object):** A structured logic expression.

#### `RouterExpression`

| Field | Type | Description |
| :--- | :--- | :--- |
| `operator` | `str` | The operator (e.g., 'eq', 'gt'). |
| `args` | `List[Any]` | Arguments for the expression. |

## Visual Metadata (`VisualMetadata`)

Used explicitly by the **Builder** to render the graph but ignored by the Engine's execution logic.

| Field | Type | Description |
| :--- | :--- | :--- |
| `label` | `Optional[str]` | The label to display for the node. |
| `x_y_coordinates` | `Optional[List[float]]` | The X and Y coordinates on the canvas. |
| `icon` | `Optional[str]` | The icon to represent the node. |
| `animation_style` | `Optional[str]` | The animation style for the node. |

## Integrity & Security

The specification enforces strict integrity checks:

1.  **Integrity Hash**: The `integrity_hash` field ensures the topology has not been tampered with. It is verified by the Runtime before execution.
2.  **Edge Integrity**: The `validate_edge_integrity` function ensures no "dangling pointers" exist in the graph (all edges must point to valid nodes).
3.  **Strict Typing**: All models inherit from `CoReasonBaseModel` (Pydantic v2), enforcing strict type validation and `extra="forbid"`.

## Edge Cases & Validation

The schema enforces strict validation to prevent runtime errors. Common edge cases include:

1.  **Missing Routing Mapping**: A `ConditionalEdge` must have a non-empty `mapping` dictionary. Runtime logic that returns a value not present in `mapping` will cause an execution error.
2.  **Invalid Map-Reduce Config**: `MapNode` requires `concurrency_limit > 0`. A limit of 0 or negative will raise a validation error.
3.  **Recursion**: While `RecipeNode` allows nesting, the runtime is responsible for detecting infinite recursion loops (e.g., Recipe A -> Recipe B -> Recipe A).
4.  **State Schema Mismatch**: If a `state_schema` is defined, all nodes must output data compliant with that schema. This is enforced at runtime.

## Example Usage

Here is how to programmatically define a Recipe using the Runtime SDK:

```python
# Import V1 components from the v1 namespace
from coreason_manifest.v1 import (
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

# Create Manifest
# Note: In a real scenario, you'd define all referenced nodes (like step_3_publish)
# or the validation would fail.
recipe = RecipeManifest(
    id="research_workflow",
    version="1.0.0",
    name="Research Approval Workflow",
    interface=interface,
    state=state_def,
    parameters={"model": "gpt-4"},
    description="A simple approval workflow.",
    topology=GraphTopology(
        nodes=[agent_node, human_node], # + other nodes referenced in edges
        edges=[Edge(source_node_id="step_1", target_node_id="step_2"), router],
        state_schema=state_def
    )
)

# Dump to JSON (use by_alias=True to correctly serialize state.schema)
print(recipe.model_dump_json(indent=2, by_alias=True))
```
