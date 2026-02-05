# Presentation Layer Specification

This document defines the strict data models for UI events, replacing generic message passing with structured, strictly-typed schemas. These events are delivered via the `PresentationEvent` container.

## Core Container: `PresentationEvent`

All presentation events are wrapped in a standard container.

```python
class PresentationEvent(CoReasonBaseModel):
    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: Union[CitationBlock, MediaCarousel, ProgressUpdate, MarkdownBlock, dict]
```

### Event Types (`PresentationEventType`)

*   `thought_trace`
*   `citation_block`
*   `progress_indicator`
*   `media_carousel`
*   `markdown_block`
*   `user_error`

## Data Models

All models are immutable (`frozen=True`) and strictly typed.

### Citation Block (`citation_block`)

Represents a collection of source references.

**Model:** `CitationBlock` containing list of `CitationItem`.

```json
{
  "type": "citation_block",
  "data": {
    "items": [
      {
        "source_id": "doc-1",
        "uri": "https://example.com/report.pdf",
        "title": "Annual Report 2024",
        "snippet": "Revenue increased by 20%..."
      }
    ]
  }
}
```

### Media Carousel (`media_carousel`)

Represents a gallery of rich media (images, files).

**Model:** `MediaCarousel` containing list of `MediaItem`.

```json
{
  "type": "media_carousel",
  "data": {
    "items": [
      {
        "url": "https://cdn.example.com/chart.png",
        "mime_type": "image/png",
        "alt_text": "Q3 Revenue Chart"
      }
    ]
  }
}
```

### Progress Indicator (`progress_indicator`)

Updates on long-running processes.

**Model:** `ProgressUpdate`.

```json
{
  "type": "progress_indicator",
  "data": {
    "label": "Analyzing documents...",
    "status": "running",
    "progress_percent": 0.45
  }
}
```

*   **Status Values:** `running`, `complete`, `failed`.

### Markdown Block (`markdown_block`)

Standard text content.

**Model:** `MarkdownBlock`.

```json
{
  "type": "markdown_block",
  "data": {
    "content": "## Analysis\n\nBased on the data..."
  }
}
```

### User Error (`user_error`)

Structured error reporting for the end-user.

**Model:** Generic `dict` (for flexibility) typically containing:

```json
{
  "type": "user_error",
  "data": {
    "message": "The requested file is too large.",
    "code": 413,
    "domain": "client",
    "retryable": false
  }
}
```
