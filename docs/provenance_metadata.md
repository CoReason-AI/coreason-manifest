# AI Provenance Metadata

The `ManifestMetadata` in Coreason Manifest V2 includes a standardized `provenance` object to track the creation and modification of workflows. This structure supports both AI-generated and human-authored artifacts, ensuring traceability and supply chain security.

## Manifest Metadata

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `str` | Human-readable name. (Required) |
| `version` | `str` | Semantic version (e.g., `1.0.0`). (Default: `0.1.0`) |
| `provenance` | `ProvenanceData | None` | Provenance details. |
| `design_metadata` | `DesignMetadata | None` | UI-specific metadata (aliased as `x-design`). |

## Provenance Object (`ProvenanceData`)

The `provenance` field captures the "who, when, and why".

| Field | Type | Description |
| :--- | :--- | :--- |
| `type` | `Literal["ai", "human", "hybrid"]` | The primary source type. |
| `generated_by` | `str` | The system ID (AI) or user identifier (Human). |
| `generated_date` | `datetime | None` | Timestamp of generation. |
| `rationale` | `str | None` | Reasoning behind the design. |
| `original_intent` | `str | None` | The initial prompt (AI) or goal (Human). |
| `confidence_score` | `float | None` | Confidence (0.0 - 1.0) for AI content. |
| `methodology` | `str | None` | Technique used (e.g., `Chain-of-Thought`, `Manual Review`). |

## Usage Examples

### 1. AI-Generated Workflow

```python
from datetime import datetime, timezone
from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.provenance import ProvenanceData

metadata = ManifestMetadata(
    name="Cloud Migration Plan",
    version="0.1.0",
    provenance=ProvenanceData(
        type="ai",
        generated_by="coreason-strategist-v2",
        generated_date=datetime.now(timezone.utc),
        rationale="Selected Blue/Green deployment to minimize risk.",
        original_intent="Create a zero-downtime migration plan.",
        confidence_score=0.95
    )
)
```

### 2. Human-Authored Workflow

```python
metadata = ManifestMetadata(
    name="Manual Review Process",
    version="1.0.0",
    provenance=ProvenanceData(
        type="human",
        generated_by="alice@example.com",
        methodology="Peer Review",
        rationale="Standard operating procedure for Q2."
    )
)
```
