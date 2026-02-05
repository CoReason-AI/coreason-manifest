# Agent Runtime Interfaces

This document describes the runtime interfaces defined in the **Runtime Contracts** trilogy (WP-Q, WP-R, WP-S). These interfaces standardize how agents interact with the UI, how clients interact with agents, and how agents interact with memory.

## 1. Presentation Schema (WP-Q)

The Presentation Layer defines how the agent communicates with the user interface. It replaces legacy, disparate event types with a unified `PresentationEvent` container.

### The Container

All presentation events are wrapped in a `PresentationEvent` object.

```python
class PresentationEvent(CoReasonBaseModel):
    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: CitationBlock | ProgressUpdate | MediaCarousel | MarkdownBlock | dict
```

### Event Types & Payloads

| Type | Model | Description |
| :--- | :--- | :--- |
| `CITATION_BLOCK` | `CitationBlock` | A list of references/citations. |
| `PROGRESS_INDICATOR` | `ProgressUpdate` | Status updates (running, complete, failed). |
| `MEDIA_CAROUSEL` | `MediaCarousel` | A collection of images or other media. |
| `MARKDOWN_BLOCK` | `MarkdownBlock` | Rich text content in Markdown format. |
| `THOUGHT_TRACE` | `dict` | Internal reasoning trace (often hidden or collapsed). |
| `USER_ERROR` | `dict` | Errors intended for the end-user. |

## 2. Agent Capabilities (WP-R)

Explicit contracts define how an agent delivers content and what features it supports.

### Capabilities Model

```python
class AgentCapabilities(CoReasonBaseModel):
    type: CapabilityType = CapabilityType.GRAPH
    delivery_mode: DeliveryMode = DeliveryMode.REQUEST_RESPONSE
    history_support: bool = True
```

### Delivery Modes

*   `REQUEST_RESPONSE`: The agent returns a single response after processing.
*   `SERVER_SENT_EVENTS`: The agent streams partial results and events via SSE.

### Capability Types

*   `ATOMIC`: A simple, single-step agent.
*   `GRAPH`: A complex, multi-step workflow or graph-based agent.

## 3. Active Memory Interface (WP-S)

The Active Memory Interface (`SessionHandle`) allows agents to programmatically interact with their session state and long-term memory.

### Protocol (`SessionHandle`)

This protocol is runtime-checkable and defines the standard methods an agent can rely on.

```python
class SessionHandle(Protocol):
    @property
    def session_id(self) -> str: ...

    @property
    def identity(self) -> Identity: ...

    async def history(self, limit: int = 10, offset: int = 0) -> list[Interaction]:
        """Retrieve recent conversation history."""
        ...

    async def recall(self, query: str, limit: int = 5, threshold: float = 0.7) -> list[str]:
        """Semantic search over long-term memory."""
        ...

    async def store(self, key: str, value: Any) -> None:
        """Store a value in the session state."""
        ...

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the session state."""
        ...
```
