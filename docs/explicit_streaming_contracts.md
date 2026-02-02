# Explicit Streaming Contracts

**Explicit Streaming Contracts** eliminate the ambiguity between *what* an agent does (its internal architecture) and *how* it delivers results to the client (the transport protocol).

## The Problem: Implicit Behavior

Previously, the `AgentCapability` model relied on the `type` field (`ATOMIC` vs `GRAPH`) to imply the delivery mechanism.
*   **Assumption:** "Atomic agents are fast, so they return JSON. Graph agents are slow, so they stream SSE."

This assumption is flawed:
1.  **Long-running Atomic Agents:** An atomic agent might generate a long report (LLM streaming) or call a slow tool. The client needs to know to keep the connection open and render partial tokens.
2.  **Fast Graph Agents:** A simple graph might just categorize an email and return a label instantly. Using SSE for this is overkill.

## The Solution: Decoupling Type and Delivery

We have introduced the `delivery_mode` field to the `AgentCapability` model. This creates a matrix of possibilities:

| Capability Type | Delivery Mode | Behavior | Use Case |
| :--- | :--- | :--- | :--- |
| `ATOMIC` | `REQUEST_RESPONSE` (Default) | Client awaits a single JSON response. | Simple QA, classification, data extraction. |
| `ATOMIC` | `SERVER_SENT_EVENTS` | Client listens for `CloudEvent` stream. | LLM token streaming, long tool execution updates. |
| `GRAPH` | `SERVER_SENT_EVENTS` | Client listens for `GraphEvent` stream. | Complex workflows, visual debugging, human-in-the-loop. |
| `GRAPH` | `REQUEST_RESPONSE` | Client awaits final workflow state. | "Black box" automation where intermediate steps don't matter. |

## Implementation

### Manifest Definition

The `AgentCapability` now includes:

```python
class DeliveryMode(str, Enum):
    REQUEST_RESPONSE = "request_response"
    SERVER_SENT_EVENTS = "server_sent_events"

class AgentCapability(CoReasonBaseModel):
    # ... other fields
    delivery_mode: DeliveryMode = Field(
        default=DeliveryMode.REQUEST_RESPONSE,
        description="The mechanism used to deliver the response."
    )
```

### Builder SDK

You can define this explicitly when building agents:

```python
from coreason_manifest.definitions.agent import DeliveryMode, CapabilityType

# Atomic agent that streams tokens
cap = TypedCapability(
    name="write_essay",
    input_model=TopicInput,
    output_model=EssayOutput,
    type=CapabilityType.ATOMIC,
    delivery_mode=DeliveryMode.SERVER_SENT_EVENTS  # <--- Explicit
)
```

## Client Impact

Frontend clients (React, Flutter) can now inspect the `delivery_mode` *before* making a request.

*   **If `REQUEST_RESPONSE`:** Use standard `fetch` or `axios.post`. Await the promise.
*   **If `SERVER_SENT_EVENTS`:** Use `EventSource` or a fetch-based stream reader. Hook up event listeners.

This eliminates "guesswork" and prevents connection timeouts on long requests that were mistakenly treated as standard HTTP calls.
