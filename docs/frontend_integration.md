# Frontend Integration & Graph Events

This document defines the strict `GraphEvent` hierarchy used internally by the Coreason Engine to track granular lifecycle events of nodes. It also details the migration strategy to standard `CloudEvent` formats for external observability.

## Graph Events

`GraphEvent`s are pure data models representing the execution state of the engine. They are immutable (`frozen=True`) and strictly discriminated by the `event_type` field.

### Hierarchy

All events inherit from `GraphEventBase` and include:
- `run_id`: The global execution run ID.
- `trace_id`: The W3C trace ID for distributed tracing.
- `node_id`: The ID of the specific node/step generating the event.
- `timestamp`: Unix timestamp (float).
- `sequence_id` (Optional): Ordering index.
- `visual_cue` (Optional): UI hints (e.g., "typing", "thinking").

### Concrete Models

| Event Type | Model | Payload Field | Description |
| :--- | :--- | :--- | :--- |
| `NODE_START` | `GraphEventNodeStart` | `payload: Dict[str, Any]` | Node started execution. Contains input arguments. |
| `NODE_STREAM` | `GraphEventNodeStream` | `chunk: str` | Partial output stream (e.g., LLM token). |
| `NODE_DONE` | `GraphEventNodeDone` | `output: Dict[str, Any]` | Node finished successfully. Contains final output. |
| `ERROR` | `GraphEventError` | `error_message: str`, `stack_trace: Optional[str]` | Execution failed. |
| `COUNCIL_VOTE` | `GraphEventCouncilVote` | `votes: Dict[str, Any]` | Governance council voting results. |
| `NODE_RESTORED` | `GraphEventNodeRestored` | `status: str` | Node state restored from checkpoint. |
| `ARTIFACT_GENERATED` | `GraphEventArtifactGenerated` | `artifact_type: str`, `url: str` | A side-effect artifact (image, file) was created. |

### Usage

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

## Migration to CloudEvents

The `migrate_graph_event_to_cloud_event` utility transforms internal `GraphEvent`s into standard `CloudEvent`s for external consumption (e.g., by the Frontend or Observability backend).

### Mapping Strategy

| Graph Event Field | CloudEvent Field | Logic |
| :--- | :--- | :--- |
| `event_type` | `type` | Converted to reverse-DNS, lowercase. <br> `NODE_START` -> `ai.coreason.node.start` |
| `node_id` | `source` | `urn:node:{node_id}` |
| Payload/Output | `data` | Varies by event. See below. |
| `trace_id` | `traceparent` | Mapped directly. |
| `visual_cue` | `com_coreason_ui_cue` | Custom extension field. |

### Data Content Types & Payload Mapping

| Event Type | `datacontenttype` | `data` Structure |
| :--- | :--- | :--- |
| `NODE_STREAM` | `application/vnd.coreason.stream+json` | `{"chunk": "..."}` |
| `ERROR` | `application/vnd.coreason.error+json` | `{"error_message": "...", "stack_trace": "..."}` |
| `ARTIFACT_GENERATED` | `application/vnd.coreason.artifact+json` | `{"artifact_type": "...", "url": "..."}` |
| Others | `application/json` | The original `payload` or `output` dict. |

### Example Migration

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
