# Frontend Integration & Graph Events

This document serves as the canonical guide for Engineering teams integrating the Coreason Engine with frontend applications (React, Flutter, Streamlit).

It covers two main topics:
1.  **Graph Structure Interchange:** How to render the static agent topology.
2.  **Graph Events:** How to subscribe to runtime updates (streaming, status changes).

---

## Part 1: Graph Structure Interchange

To render rich, interactive graphs in custom UIs (e.g., React Flow, Flutter CustomPainter), the `coreason-manifest` library provides a structured JSON export utility.

### The JSON Format

The `to_graph_json()` function converts a `RecipeDefinition` into a frontend-friendly JSON structure. This format is designed to be easily mapped to common graph libraries.

#### Usage

```python
from coreason_manifest.utils.viz import to_graph_json

graph_data = to_graph_json(my_recipe)
# Returns a Dict, which can be JSON-serialized
```

#### Schema & Sample Response

The output consists of a list of `nodes`, a list of `edges`, and a `theme` object.

**Key Field:** `original_id`
*   The `id` field in the JSON is sanitized (e.g., `Step 1` -> `Step_1`) to be safe for HTML/DOM usage.
*   The `original_id` field preserves the exact ID from the backend Pydantic model. **Use this ID** when sending callbacks or actions back to the engine.

```json
{
  "nodes": [
    {
      "id": "INPUTS",
      "type": "input",
      "label": "Inputs",
      "shape": "rect",
      "x": 0.0,
      "y": 0.0,
      "config": {
        "inputs": ["query", "context"]
      }
    },
    {
      "id": "research_step",
      "original_id": "research_step",
      "type": "agent",
      "label": "Research Step (Agent: Researcher)",
      "shape": "rect",
      "x": 100.0,
      "y": 50.0,
      "config": {
        "agent_ref": "Researcher",
        "instructions": "Find generic info..."
      }
    },
    {
      "id": "approval_gate",
      "original_id": "approval_gate",
      "type": "router",
      "label": "Approval Gate",
      "shape": "diamond",
      "x": 200.0,
      "y": 150.0,
      "config": {
        "input_key": "score"
      }
    }
  ],
  "edges": [
    {
      "source": "INPUTS",
      "target": "research_step",
      "label": null,
      "type": "implicit"
    },
    {
      "source": "research_step",
      "target": "approval_gate",
      "label": "success"
    }
  ],
  "theme": {
    "orientation": "TD",
    "primary_color": null,
    "node_styles": {
      "agent": "fill:#e3f2fd,stroke:#1565c0",
      "human": "fill:#fff3e0,stroke:#e65100"
    }
  }
}
```

### Flutter Implementation Guide

For a Flutter mobile app, follow this pattern to consume the JSON:

1.  **Fetch & Parse:** Call your backend API to get the JSON. Decode it into a Dart model.
2.  **Map Nodes to Widgets:**
    *   Iterate through `nodes`.
    *   Switch on `node.type`.
    *   `agent` -> return `AgentCardWidget(...)`
    *   `router` -> return `DiamondShapeWidget(...)`
    *   `human` -> return `InteractionCardWidget(...)`
3.  **Apply Theme:** Use the `theme` object in the payload to set colors dynamically. If `theme.primary_color` is present, override your local theme color for the graph edges.
4.  **Handle Interactions:** When a user taps a node, use `node.original_id` to fetch details or trigger an action on the backend.

### Streamlit Implementation Guide

For rapid internal tools or prototyping, use the Mermaid string generator instead of the raw JSON.

```python
import streamlit as st
from coreason_manifest.utils.viz import generate_mermaid_graph

# ... fetch recipe ...

mermaid_code = generate_mermaid_graph(recipe)

st.markdown(f"""
```mermaid
{mermaid_code}
```
""", unsafe_allow_html=True)
```

---

## Part 2: Graph Events & Runtime

This section defines the strict `GraphEvent` hierarchy used internally by the Coreason Engine to track granular lifecycle events of nodes. It also details the migration strategy to standard `CloudEvent` formats for external observability.

### Graph Events

`GraphEvent`s are pure data models representing the execution state of the engine. They are immutable (`frozen=True`) and strictly discriminated by the `event_type` field.

#### Hierarchy

All events inherit from `GraphEventBase` and include:
- `run_id`: The global execution run ID.
- `trace_id`: The W3C trace ID for distributed tracing.
- `node_id`: The ID of the specific node/step generating the event.
- `timestamp`: Unix timestamp (float).
- `sequence_id` (Optional): Ordering index.
- `visual_cue` (Optional): UI hints (e.g., "typing", "thinking").

#### Concrete Models

| Event Type | Model | Payload Field | Description |
| :--- | :--- | :--- | :--- |
| `NODE_START` | `GraphEventNodeStart` | `payload: Dict[str, Any]` | Node started execution. Contains input arguments. |
| `NODE_STREAM` | `GraphEventNodeStream` | `chunk: str` | Partial output stream (e.g., LLM token). |
| `NODE_DONE` | `GraphEventNodeDone` | `output: Dict[str, Any]` | Node finished successfully. Contains final output. |
| `ERROR` | `GraphEventError` | `error_message: str`, `stack_trace: Optional[str]` | Execution failed. |
| `COUNCIL_VOTE` | `GraphEventCouncilVote` | `votes: Dict[str, Any]` | Governance council voting results. |
| `NODE_RESTORED` | `GraphEventNodeRestored` | `status: str` | Node state restored from checkpoint. |
| `ARTIFACT_GENERATED` | `GraphEventArtifactGenerated` | `artifact_type: str`, `url: str` | A side-effect artifact (image, file) was created. |

#### Usage

```python
from coreason_manifest import GraphEventNodeStream

event = GraphEventNodeStream(
    run_id="run-1",
    trace_id="trace-1",
    node_id="step-1",
    timestamp=1700000000.0,
    chunk="Hello ",
    visual_cue="typing"
)
```

### Migration to CloudEvents

The `migrate_graph_event_to_cloud_event` utility transforms internal `GraphEvent`s into standard `CloudEvent`s for external consumption (e.g., by the Frontend or Observability backend).

#### Mapping Strategy

| Graph Event Field | CloudEvent Field | Logic |
| :--- | :--- | :--- |
| `event_type` | `type` | Converted to reverse-DNS, lowercase. <br> `NODE_START` -> `ai.coreason.node.start` |
| `node_id` | `source` | `urn:node:{node_id}` |
| Payload/Output | `data` | Varies by event. See below. |
| `trace_id` | `traceparent` | Mapped directly. |
| `visual_cue` | `com_coreason_ui_cue` | Custom extension field. |

#### Data Content Types & Payload Mapping

| Event Type | `datacontenttype` | `data` Structure |
| :--- | :--- | :--- |
| `NODE_STREAM` | `application/vnd.coreason.stream+json` | `{"chunk": "..."}` |
| `ERROR` | `application/vnd.coreason.error+json` | `{"error_message": "...", "stack_trace": "..."}` |
| `ARTIFACT_GENERATED` | `application/vnd.coreason.artifact+json` | `{"artifact_type": "...", "url": "..."}` |
| Others | `application/json` | The original `payload` or `output` dict. |

#### Example Migration

```python
from coreason_manifest import migrate_graph_event_to_cloud_event

cloud_event = migrate_graph_event_to_cloud_event(event)

# Resulting CloudEvent (JSON)
# {
#   "specversion": "1.0",
#   "id": "uuid...",
#   "source": "urn:node:step-1",
#   "type": "ai.coreason.node.stream",
#   "datacontenttype": "application/vnd.coreason.stream+json",
#   "time": "2023-11-14T...",
#   "data": { "chunk": "Hello " },
#   "traceparent": "trace-1",
#   "com_coreason_ui_cue": "typing"
# }
```
