# Standardized Presentation Schemas (V2)

The Coreason Presentation Layer (V2) enforces strictly typed, immutable Pydantic models for all user interface events. This ensures that the Frontend can deterministically render complex agent outputs such as citations, progress bars, and media carousels.

All presentation events are wrapped in a `PresentationEvent` container and discriminated by the `type` field.

## Core Concepts

*   **Strict Typing:** Uses `pydantic.AnyUrl` for URIs, `uuid.UUID` for IDs, and `Literal` for status fields.
*   **Immutability:** All models are `frozen=True`.
*   **Polymorphism:** The `PresentationEvent.data` field is a polymorphic union of specific payload models.

## The Container: `PresentationEvent`

Every event emitted to the UI follows this structure:

```python
class PresentationEvent(CoReasonBaseModel):
    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, MarkdownBlock, dict[str, Any]]
```

### Event Types (`PresentationEventType`)

*   `"thought_trace"`
*   `"citation_block"`
*   `"progress_indicator"`
*   `"media_carousel"`
*   `"markdown_block"`
*   `"user_error"`

## Payloads

### 1. Citation Block (`citation_block`)

Used to display a list of source references.

```python
class CitationItem(CoReasonBaseModel):
    source_id: str
    uri: AnyUrl
    title: str
    snippet: str | None = None

class CitationBlock(CoReasonBaseModel):
    items: list[CitationItem]
```

**JSON Example:**
```json
{
  "type": "citation_block",
  "data": {
    "items": [
      {
        "source_id": "doc-1",
        "uri": "https://example.com/report.pdf",
        "title": "Annual Report 2024",
        "snippet": "Revenue grew by 20%..."
      }
    ]
  }
}
```

### 2. Progress Indicator (`progress_indicator`)

Used to show the status of a long-running operation.

```python
class ProgressUpdate(CoReasonBaseModel):
    label: str
    status: Literal["running", "complete", "failed"]
    progress_percent: float | None = Field(None, ge=0.0, le=1.0)
```

**JSON Example:**
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

### 3. Media Carousel (`media_carousel`)

Used to display a gallery of images or other media.

```python
class MediaItem(CoReasonBaseModel):
    url: AnyUrl
    mime_type: str
    alt_text: str | None = None

class MediaCarousel(CoReasonBaseModel):
    items: list[MediaItem]
```

**JSON Example:**
```json
{
  "type": "media_carousel",
  "data": {
    "items": [
      {
        "url": "https://example.com/chart.png",
        "mime_type": "image/png",
        "alt_text": "Q3 Sales Chart"
      }
    ]
  }
}
```

### 4. Markdown Block (`markdown_block`)

Used for rich text content.

```python
class MarkdownBlock(CoReasonBaseModel):
    content: str
```

### 5. User Error (`user_error`)

Used for generic error reporting. The payload is a flexible dictionary (`dict[str, Any]`).

**JSON Example:**
```json
{
  "type": "user_error",
  "data": {
    "code": "rate_limit_exceeded",
    "message": "You have exceeded your daily quota."
  }
}
```
