# Multi-Modal Interactions

This document defines the data structures and patterns for supporting **Multi-Modal Interactions** in the Coreason ecosystem. This upgrades the system from relying on simple strings or loose dictionaries to using strictly typed Pydantic models for rich user inputs (interleaving text with files/images).

## Rationale

Modern agents often require inputs that go beyond simple text strings. Users may want to:
1.  Analyze a specific file.
2.  Ask a question about an image.
3.  Provide context via multiple attachments interleaved with instructions.

To support this safely and consistently across the "Shared Kernel," we introduce a set of strict, frozen data models.

## Data Models

All models are defined in `src/coreason_manifest/definitions/message.py` and inherit from `CoReasonBaseModel`.

### 1. `AttachedFile`

Represents a reference to a file that has already been uploaded to a blob storage or similar system. It does *not* contain the file content itself, but rather a stable identifier.

```python
class AttachedFile(CoReasonBaseModel):
    id: str  # Unique ID/UUID
    mime_type: Optional[str]  # e.g., "application/pdf"
```

### 2. `ContentPart`

A discrete unit of input. A user's turn may consist of multiple parts. A part can contain text, attachments, or both.

```python
class ContentPart(CoReasonBaseModel):
    text: Optional[str]
    attachments: List[AttachedFile] = []
```

### 3. `MultiModalInput`

The container for a rich user turn. This is the top-level object used when an input is complex.

```python
class MultiModalInput(CoReasonBaseModel):
    parts: List[ContentPart]
```

## Session Interaction

The `Interaction` model (in `src/coreason_manifest/definitions/session.py`) captures a single cycle of "User Request -> Assistant Response". To ensure backward compatibility, the `input` field is polymorphic.

```python
class Interaction(CoReasonBaseModel):
    # Supports strictly typed rich input, legacy simple strings, and legacy dictionaries
    input: Union[MultiModalInput, str, Dict[str, Any]]
    output: Optional[ChatMessage]
    timestamp: datetime
```

## Examples

### Scenario A: Simple Text (Legacy)

```python
interaction = Interaction(input="What is the time?")
```

### Scenario B: Analyze a PDF (Rich)

```python
file_ref = AttachedFile(id="doc-123", mime_type="application/pdf")
part = ContentPart(text="Please summarize this document.", attachments=[file_ref])
rich_input = MultiModalInput(parts=[part])

interaction = Interaction(input=rich_input)
```

### Scenario C: Mixed Content (Rich)

```python
# User: "Look at this image [IMG] and this log [LOG], then explain the error."
img = AttachedFile(id="img-001", mime_type="image/png")
log = AttachedFile(id="log-999", mime_type="text/plain")

part1 = ContentPart(text="Look at this image", attachments=[img])
part2 = ContentPart(text="and this log", attachments=[log])
part3 = ContentPart(text="then explain the error.")

rich_input = MultiModalInput(parts=[part1, part2, part3])
interaction = Interaction(input=rich_input)
```

## JSON Serialization

Because all models inherit from `CoReasonBaseModel`, they serialize cleanly to JSON using `.dump()`.

**Output for Scenario B:**
```json
{
  "input": {
    "parts": [
      {
        "text": "Please summarize this document.",
        "attachments": [
          {
            "id": "doc-123",
            "mime_type": "application/pdf"
          }
        ]
      }
    ]
  },
  "output": null,
  "timestamp": "2023-10-27T10:00:00Z"
}
```
