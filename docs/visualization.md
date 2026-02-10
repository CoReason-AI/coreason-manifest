# Glass Box Visualization Engine

The `coreason-manifest` library includes a "Glass Box" visualization engine designed to render not just the static topology of an agent system, but its **runtime state** and **interactive capabilities**.

## The Passive Visualization Engine

Adhering to the "Shared Kernel" philosophy, the visualization engine in `coreason_manifest.utils.viz` is strictly **passive**. It does not run a server, open sockets, or require heavy dependencies like `matplotlib` or `graphviz`.

Instead, it converts a `RecipeDefinition` (or `ManifestV2`) into:
1.  **Mermaid.js Strings:** For rapid documentation, prototyping, and markdown rendering.
2.  **Structured JSON:** For consumption by production UIs (React Flow, Flutter, Streamlit).

This ensures that the manifest package remains a lightweight data library while enabling rich observability.

## Glass Box Observability

The engine supports "Time Travel" debug views by accepting a `RuntimeStateSnapshot`. This allows you to overlay execution status (e.g., "Running", "Failed") onto the static graph structure.

### `generate_mermaid_graph`

```python
def generate_mermaid_graph(
    agent: ManifestV2 | RecipeDefinition,
    theme: GraphTheme | None = None,
    state: RuntimeStateSnapshot | None = None,
) -> str:
    ...
```

### Example: Rendering a Failed State

By passing a `RuntimeStateSnapshot` with node statuses, you can generate a graph that highlights exactly where a process failed.

```python
from coreason_manifest.utils.viz import generate_mermaid_graph
from coreason_manifest.spec.common.presentation import (
    RuntimeStateSnapshot,
    NodeStatus,
    GraphTheme
)

# 1. Create a Snapshot of the execution state
# (In a real app, this would come from the engine's event log)
snapshot = RuntimeStateSnapshot(
    node_states={
        "research_step": NodeStatus.COMPLETED,
        "critique_step": NodeStatus.FAILED,  # This will be red
        "rewrite_step": NodeStatus.SKIPPED   # This will be dashed
    },
    active_path=["research_step", "critique_step"]
)

# 2. Generate the Mermaid graph with the snapshot
mermaid_code = generate_mermaid_graph(my_recipe, state=snapshot)

# 3. Render in Markdown (e.g., inside a Jupyter Notebook or Streamlit)
# st.markdown(f"```mermaid\n{mermaid_code}\n```")
```

## Theming

The visual appearance of the graph is fully customizable via the `GraphTheme` schema. This allows consuming applications to inject brand colors and style overrides without modifying the core library.

```python
theme = GraphTheme(
    primary_color="#6200ea",  # Brand Primary
    orientation="LR",         # Left-to-Right layout
    node_styles={
        "agent": "fill:#ede7f6,stroke:#6200ea,stroke-width:2px",
        "failed": "fill:#ffebee,stroke:#c62828,stroke-width:3px"
    }
)
```

## BPMN 2.0 Semantics

The engine maps Coreason concepts to standard BPMN 2.0 shapes to ensure familiarity for business users and system architects.

| Node Type | Shape | Visual Representation | Meaning |
| :--- | :--- | :--- | :--- |
| **`AgentNode`** | Rectangle | `[ Task ]` | A unit of work performed by an Agent. |
| **`RouterNode`** | Rhombus | `{ Decision }` | A gateway that routes flow based on logic. |
| **`HumanNode`** | Hexagon | `{{ Interaction }}` | A step requiring human input or approval. |
| **`CouncilStep`** | Double-lined Rect | `[[ Sub-process ]]` | A complex governance or voting process. |

### Legend
*   **Rectangle (`[ ]`)**: Standard Task.
*   **Rhombus (`{ }`)**: Exclusive Gateway (Decision).
*   **Hexagon (`{{ }}`)**: User Task (Interaction).
*   **Double-lined Rect (`[[ ]]`)**: Sub-process or Collapsed Activity.
