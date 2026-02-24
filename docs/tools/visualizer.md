# Developer Tools: The Visualizer

The Visualizer module (`src/coreason_manifest/utils/visualizer.py`) bridges the gap between static definition and runtime observability. It transforms abstract JSON graphs into human-readable diagrams.

---

## Export Targets

### 1. `to_mermaid`
Generates Markdown-friendly flowcharts using [Mermaid.js](https://mermaid.js.org/) syntax. This is ideal for:
*   Embedding live graphs in `README.md`.
*   Generating documentation artifacts in CI/CD.
*   Quick debugging in the terminal.

### 2. `to_react_flow`
Generates a structured JSON payload (`{ nodes: [...], edges: [...] }`) designed to be consumed by modern React frontends (specifically [React Flow](https://reactflow.dev/)).
*   **Layouting:** It includes basic layout coordinates (via Kahn's algorithm layers) so the frontend doesn't start with a tangled mess.
*   **Metadata:** It embeds the full `Node` metadata, allowing the UI to show tooltips or detailed inspectors.

---

## Telemetry Injection (The Killer Feature)

The visualizer is not limited to static rendering. It can accept an **`ExecutionSnapshot`** (from the Telemetry schema) and overlay it onto the graph.

```python
# Python Usage
diagram = to_mermaid(
    flow=my_graph,
    snapshot=execution_trace  # The runtime record
)
```

**What this enables:**
1.  **Color Coding:** Nodes are automatically styled based on their `NodeState`.
    *   **Green:** `COMPLETED`
    *   **Red:** `FAILED`
    *   **Yellow:** `RUNNING`
    *   **Grey:** `SKIPPED`
2.  **Path Highlighting:** The visualizer highlights the `active_path` taken through the graph, making it instantly obvious which branch of a conditional switch was executed.

This transforms the visualizer from a documentation tool into a **debugging instrument**. You can visually replay a failed execution to see exactly where the logic diverged.
