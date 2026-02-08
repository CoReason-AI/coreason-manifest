# Interactive Control Plane

The **Interactive Control Plane** transforms the Coreason Manifest from a static script into a "Steerable Glass Box." This architecture allows any node in a `RecipeDefinition` (Agents, Generative Solvers, etc.) to declare its level of transparency and specific points where human intervention is required or allowed.

This design adheres to the **Passive by Design** principle: The Manifest defines the *configuration* for interaction, while the Runtime is responsible for the actual execution (pausing, resuming, and collecting feedback).

## Core Concepts

### 1. Transparency Level (`TransparencyLevel`)

Defines how much internal reasoning and state is exposed to the observer.

*   **`OPAQUE`** (Default): Black box execution. Only final inputs and outputs are visible. Suitable for simple utility tasks.
*   **`OBSERVABLE`**: "Glass Box". The node emits granular thought traces, sub-plan events, and internal state changes. It does not strictly require pausing but provides rich telemetry.
*   **`INTERACTIVE`**: "Step-Through". Implies `OBSERVABLE` behavior AND signals the runtime to expect potential intervention commands. The runtime may offer a UI for stepping through execution.

### 2. Intervention Triggers (`InterventionTrigger`)

Defines specific lifecycle hooks where the engine MUST pause execution and wait for a signal (e.g., human approval or edits).

*   **`ON_START`**: Pause before the node begins execution. Useful for reviewing inputs or modifying the initial prompt.
*   **`ON_PLAN_GENERATION`**: specific to `GenerativeNode`. Pause after the solver creates a plan but *before* it executes it. This is critical for "Review & Refine" workflows where a human validates the decomposition.
*   **`ON_FAILURE`**: Pause if the node encounters an error or exception. Allows for manual recovery, editing inputs, or skipping the step.
*   **`ON_COMPLETION`**: Pause after execution finishes but *before* passing data to the next node. Useful for output review and final sign-off.

### 3. Interaction Configuration (`InteractionConfig`)

This configuration object is attached to any `RecipeNode` via the `interaction` field.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `transparency` | `TransparencyLevel` | `OPAQUE` | Visibility level. |
| `triggers` | `list[InterventionTrigger]` | `[]` | List of lifecycle hooks where execution must pause. |
| `editable_fields` | `list[str]` | `[]` | Whitelist of fields the user is allowed to modify during an intervention (e.g., `["goal", "inputs", "solver.n_samples"]`). |
| `guidance_hint` | `str` | `None` | Static instructions for the human on what to verify (e.g., "Ensure the plan covers all 3 competitors"). |

## Examples

### 1. Interactive Generative Node (Review Plan)

A `GenerativeNode` that solves a complex goal. We want to review the generated plan before it executes.

```python
from coreason_manifest.spec.v2.recipe import (
    GenerativeNode,
    InteractionConfig,
    TransparencyLevel,
    InterventionTrigger
)

node = GenerativeNode(
    id="market-research",
    goal="Analyze competitor pricing strategies",
    output_schema={"type": "object"},
    interaction=InteractionConfig(
        transparency=TransparencyLevel.INTERACTIVE,
        triggers=[InterventionTrigger.ON_PLAN_GENERATION],
        editable_fields=["goal", "solver.max_iterations"],
        guidance_hint="Verify that the plan includes at least 3 distinct pricing models."
    )
)
```

### 2. Observable Agent with Failure Recovery

An `AgentNode` that is critical. We want to see its thought process (`OBSERVABLE`) and pause only if it fails (`ON_FAILURE`).

```python
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    InteractionConfig,
    TransparencyLevel,
    InterventionTrigger
)

node = AgentNode(
    id="critical-task",
    agent_ref="agent/v1/processor",
    interaction=InteractionConfig(
        transparency=TransparencyLevel.OBSERVABLE,
        triggers=[InterventionTrigger.ON_FAILURE],
        editable_fields=["inputs", "system_prompt_override"],
        guidance_hint="If this fails, check for malformed input data."
    )
)
```

### 3. Human Sign-Off (Completion Trigger)

An agent that generates a draft, requiring human approval before proceeding.

```python
node = AgentNode(
    id="draft-email",
    agent_ref="agent/v1/writer",
    interaction=InteractionConfig(
        transparency=TransparencyLevel.OPAQUE,
        triggers=[InterventionTrigger.ON_COMPLETION],
        editable_fields=["outputs"], # Allow editing the final email text
        guidance_hint="Ensure tone is professional."
    )
)
```

## Architectural Notes

*   **Universal Inheritance**: The `interaction` field is available on the base `RecipeNode`, meaning all node types (Agents, Humans, Routers, Evaluators, Generative) support these settings.
*   **Runtime Responsibility**: The Manifest only declares the *intent* for interaction. The Runtime is responsible for implementing the pause/resume mechanism, exposing the state to the user, and applying edits to `editable_fields`.
