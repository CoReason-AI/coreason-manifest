# Glass Box Visualization Engine

The `coreason-manifest` library includes a "Glass Box" visualization engine designed to render not just the static topology of an agent system, but its **runtime state** and **interactive capabilities**.

This engine follows the "Passive Shared Kernel" philosophy: it generates standard strings (Mermaid.js) and data structures (JSON) that can be rendered by any frontend (Streamlit, Flutter, React Flow) without importing heavy graphical dependencies.

## Key Features

1.  **Themable Mermaid.js:** Decouple logic from aesthetics using `GraphTheme`.
2.  **Runtime State Overlay:** Inject execution status (Running, Failed, Completed) into the graph.
3.  **JSON Interchange:** Export a structured JSON format for "Magentic" UIs (e.g., React Flow, Flutter).
4.  **BPMN 2.0 Compliance:** Standard shapes for Agents (Task), Routers (Gateway), and Humans (User Task).

## Usage

### 1. Generating a Static Flowchart (Mermaid)

The simplest usage generates a Mermaid string for documentation.

```python
from coreason_manifest.utils.viz import generate_mermaid_graph
from coreason_manifest.spec.common.presentation import GraphTheme

# Define your recipe (see Orchestration docs)
# recipe = ...

# Generate graph with a custom theme
theme = GraphTheme(
    orientation="LR",
    primary_color="#1565c0"
)

mermaid_code = generate_mermaid_graph(recipe, theme=theme)
print(mermaid_code)
```

### 2. Runtime State Overlay (Glass Box)

To visualize a "live" execution, pass a `RuntimeStateSnapshot`.

```python
from coreason_manifest.spec.common.presentation import RuntimeStateSnapshot, NodeStatus

# Snapshot of the engine's state
state = RuntimeStateSnapshot(
    node_states={
        "research_step": NodeStatus.COMPLETED,
        "approval_step": NodeStatus.RUNNING
    }
)

# The generated Mermaid code will now include CSS classes
# (e.g., class approval_step running;)
mermaid_code = generate_mermaid_graph(recipe, state=state)
```

**Supported States:**
*   `PENDING` (Default)
*   `RUNNING` (Pulsing animation)
*   `COMPLETED` (Green border)
*   `FAILED` (Red border)
*   `SKIPPED` (Dashed line)

### 3. JSON Export for Frontends

For rich UIs like Flutter or React Flow, use the JSON export utility. This provides raw node/edge data with sanitization and metadata.

```python
from coreason_manifest.utils.viz import to_graph_json

graph_data = to_graph_json(recipe)

# Structure:
# {
#   "nodes": [
#     { "id": "step1", "type": "agent", "label": "Research", "x": 0, "y": 0, "config": {...} }
#   ],
#   "edges": [
#     { "source": "step1", "target": "step2", "label": "success" }
#   ],
#   "theme": { ... }
# }
```

## Node Types & Visual Semantics

The engine maps Coreason Node types to BPMN 2.0 shapes:

| Node Type | Mermaid Shape | Meaning |
| :--- | :--- | :--- |
| `AgentNode` | `[Rect]` | Standard Task / Unit of Work |
| `RouterNode` | `{Rhombus}` | Exclusive Gateway (Decision) |
| `HumanNode` | `{{Hexagon}}` | User Task (Human Input) |
| `EvaluatorNode` | `([Stadium])` | Event-Based Gateway (Quality Gate) |
| `GenerativeNode` | `[[Subroutine]]` | Sub-Process (Complex Solver) |
| `SwitchStep` | `{Rhombus}` | Exclusive Gateway (ManifestV2) |
| `CouncilStep` | `[[Subroutine]]` | Parallel Gateway (ManifestV2) |

## Interactive Graphs

If a node has an `InteractionConfig` with `transparency="interactive"`, the engine generates a clickable binding:

```mermaid
click step_id call_interaction_handler "Tooltip"
```

This allows the hosting application to define a JavaScript callback (`call_interaction_handler`) to open a configuration modal or debug view when the node is clicked.
