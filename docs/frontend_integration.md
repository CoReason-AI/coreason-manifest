# Frontend Integration Guide: Communicating with the Coreason Engine

This guide details how the **Coreason Engine (MACO)** communicates with frontend clients (e.g., Flutter, React) using the `coreason-manifest` data structures.

## The Atomic Unit: `GraphEvent`

The `GraphEvent` is the fundamental unit of communication. It serves as the protocol for real-time updates from the engine to the UI.

In `coreason-manifest` v0.10.0+, `GraphEvent` is strictly defined as a **Discriminated Union** of specific Pydantic models. This ensures type safety and predictable payloads.

### Structure

Every event conforms to a specific schema based on its `event_type`.

```python
# Conceptual Structure (BaseGraphEvent)
class GraphEventNodeStart(BaseModel):
    event_type: Literal["NODE_START"]
    run_id: str            # Workflow execution ID
    trace_id: str          # OpenTelemetry Trace ID
    node_id: str           # The node related to this event
    timestamp: float       # Epoch timestamp
    sequence_id: Optional[int] # Optional ordering ID
    payload: NodeStarted   # Specific Payload Model
    visual_metadata: RuntimeVisualMetadata # Hints for UI (Pydantic Model)
```

### Key Fields

1.  **`event_type`**: The discriminator (e.g., `NODE_START`, `NODE_STREAM`, `NODE_DONE`).
2.  **`node_id`**: The ID of the node in the `GraphTopology` currently executing.
3.  **`trace_id`**: The OpenTelemetry Trace ID for distributed tracing.
4.  **`payload`**: The strictly typed data associated with the event.
5.  **`visual_metadata`**: A strictly typed `RuntimeVisualMetadata` object containing hints for the UI renderer.

---

## Visual Metadata (`RuntimeVisualMetadata`)

The `visual_metadata` field allows the backend graph logic to drive frontend animations without coupling the engine to UI implementation details. It is defined as a Pydantic model, not a loose dictionary.

### Fields

| Field | Description | Example Values |
| :--- | :--- | :--- |
| `animation` | The primary animation style to trigger. | `pulse`, `shake`, `slide_in`, `fade_out` |
| `color` | Hex code or semantic color name. | `#FF0000`, `success_green` |
| `progress` | Progress bar value (0.0 - 1.0). | `0.5`, `0.9` |
| `label` | Dynamic label override for the node. | `Thinking...`, `Searching Google` |

### Example Usage

```json
{
  "event_type": "NODE_START",
  "run_id": "run-123",
  "trace_id": "trace-abc",
  "node_id": "agent_research",
  "timestamp": 1700000000.0,
  "visual_metadata": {
    "animation": "pulse",
    "color": "#00AAFF",
    "label": "Researching Topic..."
  },
  "payload": { ... }
}
```

---

## Presentation Schemas ("UI-First" Artifacts)

In addition to workflow events, agents can emit standardized "Presentation Blocks" to render rich UI elements directly. These are defined in `coreason_manifest.definitions.presentation`.

These blocks are particularly useful for:
*   **Thinking Processes**: Showing the user what the agent is planning (`ThinkingBlock`).
*   **Structured Data**: Rendering tables or JSON views (`DataBlock`).
*   **Rich Text**: Displaying formatted answers (`MarkdownBlock`).
*   **Errors**: showing user-friendly error messages (`UserErrorBlock`).

See [Presentation Schemas](./presentation_schemas.md) for detailed documentation on these types.

---

## Event Types & Payloads

### 1. `NODE_INIT`
**When:** The engine acknowledges a node is about to run but hasn't started execution.
**UI Behavior:** Highlight the node, set state to "Pending".
**Payload:** `NodeInit`
- `type`: Node type (e.g., "AGENT").
- `visual_cue`: Default visual state (e.g., "IDLE").

### 2. `NODE_START`
**When:** Execution logic begins.
**UI Behavior:** Trigger "Running" animation (e.g., spinner, pulse).
**Payload:** `NodeStarted`
- `node_id`: ID of the node.
- `timestamp`: Start timestamp.
- `status`: "RUNNING".
- `input_tokens`: (Optional) Initial token count.
- `visual_cue`: "PULSE".

### 3. `NODE_STREAM`
**When:** The agent generates a token or chunk of text.
**UI Behavior:** Append text to the chat bubble or log view.
**Payload:** `NodeStream`
- `chunk`: The string fragment generated.
- `visual_cue`: "TEXT_BUBBLE".

### 4. `NODE_DONE`
**When:** Execution completes successfully.
**UI Behavior:** Mark node as complete (Green checkmark), stop animations.
**Payload:** `NodeCompleted`
- `output_summary`: Short summary of result.
- `status`: "SUCCESS".
- `visual_cue`: "GREEN_GLOW".
- `cost`: (Optional) Total cost of the step.

### 5. `NODE_SKIPPED`
**When:** A node is bypassed (e.g., in a conditional branch).
**UI Behavior:** Grey out the node.
**Payload:** `NodeSkipped`
- `status`: "SKIPPED".
- `visual_cue`: "GREY_OUT".

### 6. `EDGE_ACTIVE`
**When:** Control flow moves from one node to another.
**UI Behavior:** Animate the connecting line (Edge).
**Payload:** `EdgeTraversed`
- `source`: Source Node ID.
- `target`: Target Node ID.
- `animation_speed`: "FAST", "SLOW".

### 7. `COUNCIL_VOTE`
**When:** A voting step occurs in architectural triangulation.
**Payload:** `CouncilVote`
- `votes`: Dictionary of votes.

### 8. `ERROR`
**When:** A workflow error occurs.
**UI Behavior:** Flash red.
**Payload:** `WorkflowError`
- `error_message`: Description of the error.
- `stack_trace`: Debug info.
- `visual_cue`: "RED_FLASH".

### 9. `NODE_RESTORED`
**When:** A node is restored from state.
**UI Behavior:** Instant green/completed state.
**Payload:** `NodeRestored`
- `status`: "RESTORED".
- `visual_cue`: "INSTANT_GREEN".

### 10. `ARTIFACT_GENERATED`
**When:** An artifact (e.g., PDF) is created.
**Payload:** `ArtifactGenerated`
- `artifact_type`: e.g., "PDF".
- `url`: Location of the artifact.

---

## Integration with CloudEvents (Observability)

For external systems (webhooks, monitoring), `GraphEvent` objects are migrated to the **CloudEvents v1.0** standard using `migrate_graph_event_to_cloud_event()`.

- **Payload Mapping**: The strict `GraphEvent` payload is mapped to the `data` field of the CloudEvent.
- **UI Extension**: `visual_metadata` is moved to the `com_coreason_ui_metadata` extension attribute.
- **Cue Extension**: The primary visual cue is moved to `com_coreason_ui_cue`.

This allows the frontend to consume either the raw `GraphEvent` (via WebSocket) or the standardized `CloudEvent` (via Webhooks) while retaining all visual fidelity.
