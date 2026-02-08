# Interactive Control Plane

The **Interactive Control Plane** transforms the Coreason Manifest from a static script into a "Glass Box" execution model. It allows any node in a recipe to declare *when* it should pause for human intervention and *what* parts of its state are mutable during execution.

## Overview

The Interactive Control Plane is configured via the `interaction` field on any `RecipeNode`. It supports:
*   **Transparency**: Controlling the visibility of internal node events.
*   **Intervention**: Pausing execution based on specific triggers (e.g., on failure, on completion).
*   **Steerability**: Whitelisting fields that can be modified by a human during a pause.

## Configuration (`InteractionConfig`)

The `InteractionConfig` object defines the behavior for a specific node.

```python
class InteractionConfig(CoReasonBaseModel):
    transparency: TransparencyLevel = Field(TransparencyLevel.OPAQUE)
    triggers: list[InterventionTrigger] = Field(default_factory=list)
    editable_fields: list[str] = Field(default_factory=list)
    enforce_contract: bool = Field(True)
    guidance_hint: str | None = Field(None)
```

### Transparency Levels

*   `OPAQUE` (Default): Black box execution. Only inputs and outputs are visible.
*   `OBSERVABLE`: "Glass Box" execution. The node emits internal thought traces and events.
*   `INTERACTIVE`: "Step-Through" execution. Implies `OBSERVABLE` and signals the runtime to expect pauses.

### Intervention Triggers

*   `ON_START`: Pause before node execution begins. Useful for tweaking inputs.
*   `ON_PLAN_GENERATION`: Pause after a `GenerativeNode` creates a plan. Useful for review and refinement.
*   `ON_FAILURE`: Pause when an error occurs. Useful for manual recovery.
*   `ON_COMPLETION`: Pause before the output is released. Useful for quality checks.

### Editable Fields

The `editable_fields` list acts as a whitelist for what a user can modify during a pause.
*   Examples: `['inputs']`, `['system_prompt_override']`, `['solver.depth_limit']`.

### Contract Enforcement

*   `enforce_contract=True`: The runtime MUST validate any steered/modified output against the original `output_schema`. This creates a "Safe Sandbox" for user changes.

## Usage Example

```python
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    InteractionConfig,
    TransparencyLevel,
    InterventionTrigger
)

node = AgentNode(
    id="critical-step",
    agent_ref="analyst-v1",
    interaction=InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[
            InterventionTrigger.ON_START,      # Pause before running to check inputs
            InterventionTrigger.ON_FAILURE     # Pause if it crashes to let human fix it
        ],
        editable_fields=["inputs", "system_prompt_override"],
        guidance_hint="Ensure the date range is correct before approving."
    )
)
```

## Runtime-to-Design Loop (Provenance)

When a user modifies a running recipe (e.g., via the Interactive Control Plane), the system can capture this as a new "Forked" recipe. This lineage is tracked in the `ManifestMetadata`.

### Provenance Data

The `ProvenanceData` object tracks the origin of a manifest.

*   `type`: `ai`, `human`, or `hybrid`.
*   `derived_from`: The ID/URI of the parent recipe.
*   `modifications`: A log of changes applied to the parent.

```python
from coreason_manifest.spec.v2.definitions import ManifestMetadata, ProvenanceData

metadata = ManifestMetadata(
    name="Steered Analysis Recipe",
    provenance=ProvenanceData(
        type="human",
        derived_from="recipe-v1-published",
        modifications=[
            "Changed input date range on step-1",
            "Added system prompt override to clarify tone"
        ],
        generated_by="user-123"
    )
)
```
