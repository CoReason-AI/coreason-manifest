# Multi-Modal Inputs

As of version `0.12.0`, `coreason-manifest` supports a strictly typed structure for handling multi-modal inputs (text mixed with files). This replaces the loose `Dict[str, Any]` previously used in interactions, although the dictionary format remains supported for backward compatibility.

## The `MultiModalInput` Model

The `MultiModalInput` model serves as the standard container for user inputs. It wraps a list of `ContentPart` objects.

```python
from coreason_manifest.definitions.message import MultiModalInput, ContentPart, AttachedFile

# Example: A user asking to analyze a PDF
input_payload = MultiModalInput(
    parts=[
        ContentPart(
            text="Please analyze this financial report for risks.",
            attachments=[
                AttachedFile(id="file-uuid-1234-5678", mime_type="application/pdf")
            ]
        )
    ]
)
```

### `ContentPart`

A `ContentPart` represents a discrete unit of input. It allows associating text with specific files.

| Field | Type | Description |
| :--- | :--- | :--- |
| `text` | `Optional[str]` | The text content (e.g., instructions, questions). |
| `attachments` | `List[AttachedFile]` | A list of attached files, where each file has an `id` and optional `mime_type`. |

## Usage in Sessions

The `Interaction` model in `coreason_manifest.definitions.session` now accepts `MultiModalInput` in its `input` field.

```python
from coreason_manifest.definitions.session import Interaction

interaction = Interaction(
    input=input_payload,  # Strictly typed MultiModalInput
    output={"role": "assistant", "content": "Analysis complete."},
)
```

## JSON Serialization

Like all `CoReasonBaseModel`s, `MultiModalInput` serializes to standard JSON:

```json
{
  "parts": [
    {
      "text": "Please analyze this financial report for risks.",
      "attachments": [
        {
          "id": "file-uuid-1234-5678",
          "mime_type": "application/pdf"
        }
      ]
    }
  ]
}
```

## Backward Compatibility

The `Interaction` input field is defined as `Union[MultiModalInput, Dict[str, Any]]`. This means existing agents that rely on unstructured dictionaries will continue to work without modification.

```python
# Legacy style (still valid)
interaction = Interaction(
    input={"text": "Hello world"},
    output=...
)
```
