# Standardized Presentation Schemas

The `coreason-manifest` library defines a Standardized Presentation Layer to allow agents to emit UI-ready event schemas. This ensures consistent rendering of agent thoughts, citations, progress, and media across different frontend implementations.

## Overview

The presentation layer is built around the `PresentationEvent` wrapper, which encapsulates specific event types defined by the `PresentationEventType` enum.

### Presentation Event Types

| Type | Description |
| :--- | :--- |
| `THOUGHT_TRACE` | For inner monologue, reasoning chains, or planning steps. |
| `CITATION_BLOCK` | For sourcing facts with references to external documents or URLs. |
| `PROGRESS_INDICATOR` | For displaying status bars, spinners, or progress percentages. |
| `MEDIA_CAROUSEL` | For displaying collections of images, diagrams, or other media. |
| `MARKDOWN_BLOCK` | For standard rich text output. |

## Schemas

### PresentationEvent

The top-level wrapper for all presentation events.

```python
class PresentationEvent(CoReasonBaseModel):
    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, Dict[str, Any]]
```

### CitationBlock

A block containing a list of `CitationItem`s.

```python
class CitationItem(CoReasonBaseModel):
    source_id: str
    uri: AnyUrl
    title: str
    snippet: Optional[str]
    confidence: float

class CitationBlock(CoReasonBaseModel):
    citations: List[CitationItem]
```

**JSON Example:**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2023-10-27T10:00:00Z",
  "type": "CITATION_BLOCK",
  "data": {
    "citations": [
      {
        "source_id": "doc-1",
        "uri": "https://example.com/research.pdf",
        "title": "Analysis of AI Agents",
        "snippet": "Agents can autonomously execute tasks...",
        "confidence": 0.95
      }
    ]
  }
}
```

## Streaming Wire Format

When sending these events over a stream (Server-Sent Events), they are wrapped in a `StreamPacket`. See [SSE Wire Protocol Specification](./sse_wire_protocol.md) for details.

### ProgressUpdate

Used to report the status of a long-running operation.

```python
class ProgressUpdate(CoReasonBaseModel):
    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: Optional[float]
```

**JSON Example:**

```json
{
  "id": "...",
  "timestamp": "...",
  "type": "PROGRESS_INDICATOR",
  "data": {
    "label": "Indexing documents...",
    "status": "running",
    "progress_percent": 0.45
  }
}
```

### MediaCarousel

Used to display a set of media items.

```python
class MediaItem(CoReasonBaseModel):
    url: AnyUrl
    mime_type: str
    alt_text: Optional[str]

class MediaCarousel(CoReasonBaseModel):
    items: List[MediaItem]
```

**JSON Example:**

```json
{
  "id": "...",
  "timestamp": "...",
  "type": "MEDIA_CAROUSEL",
  "data": {
    "items": [
      {
        "url": "https://example.com/diagram.png",
        "mime_type": "image/png",
        "alt_text": "Architecture Diagram"
      }
    ]
  }
}
```

### Thought Trace & Markdown

For simple text or reasoning content, generic dictionaries or specific blocks (like `MARKDOWN_BLOCK`) are used.

**Thought Trace Example:**

```json
{
  "id": "...",
  "timestamp": "...",
  "type": "THOUGHT_TRACE",
  "data": {
    "thought": "I need to query the database for user preferences."
  }
}
```
