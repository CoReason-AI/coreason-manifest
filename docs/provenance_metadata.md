# AI Provenance Metadata

The `ManifestMetadata` in Coreason Manifest V2 includes specific fields to track the provenance of AI-generated workflows. These fields allow systems like `coreason-strategist` to embed reasoning, confidence scores, and original intent directly into the manifest.

## Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Human-readable name of the workflow/agent. (Required) |
| `generation_rationale` | `str | None` | Reasoning behind the creation or selection of this workflow. |
| `confidence_score` | `float | None` | A score (0.0 - 1.0) indicating the system's confidence in this workflow. |
| `original_user_intent` | `str | None` | The original user prompt or goal that resulted in this workflow. |
| `generated_by` | `str | None` | The model or system ID that generated this manifest (e.g., 'coreason-strategist-v1'). |
| `design_metadata` | `DesignMetadata | None` | UI-specific metadata (aliased as `x-design`). |

## Usage

When generating a manifest programmatically (e.g., from an LLM planning step), populate these fields to ensure traceability.

```python
from coreason_manifest.spec.v2.definitions import ManifestMetadata

metadata = ManifestMetadata(
    name="Cloud Migration Plan",
    generation_rationale="Selected 'Blue/Green Deployment' strategy to minimize downtime based on user constraints.",
    confidence_score=0.92,  # Normalized from 0-100 to 0.0-1.0
    original_user_intent="Create a safe migration plan for the payment service.",
    generated_by="coreason-strategist-v2",
)
```

## Validation

*   **Confidence Score**: Must be between `0.0` and `1.0` inclusive.
*   **Extra Fields**: The schema permits extra fields (`extra="allow"`) to support forward compatibility and custom metadata, but the fields above are strictly typed.
