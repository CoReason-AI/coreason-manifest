# MACO Recipe Specification

The **Recipe Specification** defines the standard for **Recipes**—executable workflows managed by the Coreason Engine (MACO) and designed via the MACO Builder.

A **Recipe** is a reusable "Standard Operating Procedure" (SOP) that defines a directed graph of nodes (steps) and edges (connections), along with strict interfaces for inputs, outputs, and state.

## The Recipe Manifest

The root of the specification is the `RecipeManifest` class. It serves as the shared contract between the **Engine** (runtime) and the **Builder** (visual editor).

### `RecipeManifest`

The executable specification for the MACO engine.

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

---

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

### 3. Topology (`GraphTopology`)

The core execution graph. It contains the nodes and edges that define the workflow logic.

| Field | Type | Description |
| :--- | :--- | :--- |
| `nodes` | `List[Node]` | List of nodes in the graph. |
| `edges` | `List[Union[Edge, ConditionalEdge]]` | List of edges connecting the nodes. |
| `state_schema` | `Optional[StateDefinition]` | Optional schema definition for the graph state. |

**Validation Rule:** The topology enforces integrity by ensuring that every `source_node_id` and `target_node_id` referenced in edges exists within the `nodes` list.

---

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

---

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

---

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
