# Frontend Integration Guide: Communicating with the Coreason Engine

This guide details how the **Coreason Engine (MACO)** communicates with frontend clients (e.g., Flutter, React) using the `coreason-manifest` data structures.

## The Atomic Unit: `GraphEvent`

The `GraphEvent` is the fundamental unit of communication. It serves as the protocol for real-time updates from the engine to the UI.

In `coreason-manifest` v0.10.0+, `GraphEvent` is strictly defined as a **Discriminated Union** of specific Pydantic models. This ensures type safety and predictable payloads.

### Structure

Every event conforms to a specific schema based on its `event_type`.

```python
# Conceptual Structure
class GraphEventNodeStart(BaseModel):
    event_type: Literal["NODE_START"]
    run_id: str
    node_id: str
    timestamp: float
    payload: NodeStarted  # Specific Payload Model
    visual_metadata: Dict[str, str]
```

### Key Fields

1.  **`event_type`**: The discriminator (e.g., `NODE_START`, `NODE_STREAM`, `NODE_DONE`).
2.  **`node_id`**: The ID of the node in the `GraphTopology` currently executing.
3.  **`payload`**: The strictly typed data associated with the event.
4.  **`visual_metadata`**: A dictionary of hints specifically for the UI renderer.

---

## Visual Metadata (`visual_metadata`)

The `visual_metadata` field allows the backend graph logic to drive frontend animations without coupling the engine to UI implementation details.

### Common Keys

| Key | Description | Example Values |
| :--- | :--- | :--- |
| `animation` | The primary animation style to trigger. | `pulse`, `shake`, `slide_in`, `fade_out` |
| `color` | Hex code or semantic color name. | `#FF0000`, `success_green` |
| `progress` | Progress bar value (0.0 - 1.0). | `0.5`, `0.9` |
| `label` | Dynamic label override for the node. | `Thinking...`, `Searching Google` |

### Example Usage

```json
{
  "event_type": "NODE_START",
  "node_id": "agent_research",
  "visual_metadata": {
    "animation": "pulse",
    "color": "#00AAFF",
    "label": "Researching Topic..."
  },
  "payload": { ... }
}
```

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
- `status`: "RUNNING"
- `input_tokens`: (Optional) Initial token count.
- `model`: (Optional) LLM model being used.

### 3. `NODE_STREAM`
**When:** The agent generates a token or chunk of text.
**UI Behavior:** Append text to the chat bubble or log view.
**Payload:** `NodeStream`
- `chunk`: The string fragment generated.
- `visual_cue`: "TEXT_BUBBLE"

### 4. `NODE_DONE`
**When:** Execution completes successfully.
**UI Behavior:** Mark node as complete (Green checkmark), stop animations.
**Payload:** `NodeCompleted`
- `output_summary`: Short summary of result.
- `status`: "SUCCESS"
- `cost`: (Optional) Total cost of the step.

### 5. `EDGE_ACTIVE`
**When:** Control flow moves from one node to another.
**UI Behavior:** Animate the connecting line (Edge).
**Payload:** `EdgeTraversed`
- `source`: Source Node ID.
- `target`: Target Node ID.
- `animation_speed`: "FAST", "SLOW".

---

## Integration with CloudEvents (Observability)

For external systems (webhooks, monitoring), `GraphEvent` objects are migrated to the **CloudEvents v1.0** standard using `migrate_graph_event_to_cloud_event()`.

- **Payload Mapping**: The strict `GraphEvent` payload is mapped to the `data` field of the CloudEvent.
- **UI Extension**: `visual_metadata` is moved to the `com_coreason_ui_metadata` extension attribute.
- **Cue Extension**: The primary visual cue is moved to `com_coreason_ui_cue`.

This allows the frontend to consume either the raw `GraphEvent` (via WebSocket) or the standardized `CloudEvent` (via Webhooks) while retaining all visual fidelity.
