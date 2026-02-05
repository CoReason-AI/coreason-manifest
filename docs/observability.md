# Observability & Tracing

`coreason-manifest` defines standard envelopes for emitting telemetry and audit logs from the Coreason Engine. These models ensure that all system events are machine-parsable, strictly typed, and compliant with industry standards.

## CloudEvent Envelope

We use the [CloudEvents 1.0 JSON Format](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md) for all system notifications and asynchronous events.

### Model: `CloudEvent`

A strict Pydantic model representing a CloudEvent.

**Import:**
```python
from coreason_manifest import CloudEvent
```

**Fields:**

| Field | Type | Description | Required | Default |
| :--- | :--- | :--- | :--- | :--- |
| `specversion` | `Literal["1.0"]` | The CloudEvents specification version. | Yes | `"1.0"` |
| `id` | `str` | Unique event identifier. | Yes | - |
| `source` | `str` | URI reference to the event producer (e.g., `urn:node:step-1`). | Yes | - |
| `type` | `str` | Reverse-DNS event type (e.g., `ai.coreason.node.started`). | Yes | - |
| `time` | `datetime` | Timestamp of occurrence (UTC). | Yes | - |
| `datacontenttype` | `Union[EventContentType, str]` | MIME type of the data. | Yes | `"application/json"` |
| `data` | `Optional[Dict[str, Any]]` | The event payload. | No | `None` |
| `traceparent` | `Optional[str]` | W3C Trace Context parent ID. | No | `None` |
| `tracestate` | `Optional[str]` | W3C Trace Context state. | No | `None` |

**Content Types (`EventContentType`):**

*   `JSON` = `"application/json"`
*   `STREAM` = `"application/vnd.coreason.stream+json"`
*   `ERROR` = `"application/vnd.coreason.error+json"`
*   `ARTIFACT` = `"application/vnd.coreason.artifact+json"`

**Example:**

```python
from datetime import datetime, timezone
from coreason_manifest import CloudEvent, EventContentType

event = CloudEvent(
    id="evt-123",
    source="urn:process:workflow-a",
    type="ai.coreason.workflow.completed",
    time=datetime.now(timezone.utc),
    data={"result": "success", "tokens": 150}
)

print(event.to_json())
```

---

## Reasoning Trace

Structured audit logs for tracking the execution lineage of Agents, Workflows, and Steps.

### Model: `ReasoningTrace`

**Import:**
```python
from coreason_manifest import ReasoningTrace
```

**Fields:**

| Field | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `request_id` | `UUID` | Unique ID for this specific trace entry. | Yes |
| `root_request_id` | `UUID` | The original user request ID (preserves lineage). | Yes |
| `parent_request_id` | `Optional[UUID]` | The ID of the parent span/step. | No |
| `node_id` | `str` | The name or ID of the step/component. | Yes |
| `status` | `str` | Execution status (`"success"`, `"failed"`). | Yes |
| `inputs` | `Optional[Dict]` | Input arguments to the node. | No |
| `outputs` | `Optional[Dict]` | Output results from the node. | No |
| `latency_ms` | `float` | Execution duration in milliseconds. | Yes |
| `timestamp` | `datetime` | Time of log entry. | Yes |

**Example:**

```python
from uuid import uuid4
from datetime import datetime, timezone
from coreason_manifest import ReasoningTrace

trace = ReasoningTrace(
    request_id=uuid4(),
    root_request_id=uuid4(),
    node_id="summarize-text",
    status="success",
    inputs={"text_length": 5000},
    outputs={"summary_length": 200},
    latency_ms=1250.5,
    timestamp=datetime.now(timezone.utc)
)
```
