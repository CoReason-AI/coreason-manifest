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
| `provenance` | `ProvenanceData | None` | Detailed provenance including fork lineage and modifications. |

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
*   **Extra Fields**: The schema strictly forbids extra fields (`extra="forbid"`) to prevent metadata drift. Standard fields like `version`, `description`, `created`, and `requires_auth` are explicitly defined.

## Provenance Data (New in 0.22.0)

The `ProvenanceData` model captures the origin and evolution of a workflow, supporting "Runtime-to-Design" loops where users fork and modify running agents.

### Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `str` | Origin type: `ai`, `human`, or `hybrid`. (Required) |
| `generated_by` | `str | None` | The system or model ID that generated this. |
| `generated_date` | `datetime | None` | Date of generation. |
| `derived_from` | `str | None` | The ID/URI of the parent recipe this was forked from. |
| `modifications` | `list[str]` | Human-readable log of changes applied to the parent. |
| `rationale` | `str | None` | Reasoning for generation. |
| `original_intent` | `str | None` | The original user prompt or goal. |
| `confidence_score` | `float | None` | Confidence score (0.0-1.0). |
| `methodology` | `str | None` | Methodology used (e.g., "MCTS", "Prompt Chaining"). |

### Example: Steered Fork

```python
from coreason_manifest.spec.v2.provenance import ProvenanceData, ProvenanceType
from coreason_manifest.spec.v2.definitions import ManifestMetadata

provenance = ProvenanceData(
    type=ProvenanceType.HUMAN,
    derived_from="recipe-v1-published",
    modifications=[
        "Changed input on step-3 (researcher)",
        "Added manual approval step"
    ],
    original_intent="Optimize for speed, sacrificing some depth."
)

metadata = ManifestMetadata(
    name="Optimized Workflow (Fork)",
    provenance=provenance
)
```
