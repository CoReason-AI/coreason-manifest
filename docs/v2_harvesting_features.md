# V2 Recipe Schema Enrichment (Harvesting)

Coreason V2 acts as a "Shared Kernel" for the ecosystem, consolidating configuration needs from legacy systems like Foundry, Human-Layer, Connect, and Simulacrum into a single, unified `RecipeDefinition`.

This document details the new fields added to the V2 Schema to support these "harvested" features.

## 1. Optimization Intent (Harvested from Foundry)

The `OptimizationIntent` class, used within `SemanticRef`, now supports advanced directives for DSPy-based prompt compiling and optimization.

### New Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `metric_name` | `str` | The grading function to optimize against (e.g., 'faithfulness', 'json_validity'). |
| `teacher_model` | `str \| None` | ID of a stronger model to use for bootstrapping synthetic training data (e.g., 'gpt-4-turbo'). |
| `max_demonstrations` | `int` | Maximum number of few-shot examples to learn and inject. |

### Example

```python
intent = OptimizationIntent(
    base_ref="rag-agent-v1",
    improvement_goal="Reduce hallucinations",
    metric_name="faithfulness",
    teacher_model="gpt-4-turbo",
    max_demonstrations=5
)
```

## 2. Collaboration Config (Harvested from Human-Layer)

The `CollaborationConfig` class, attached to `RecipeNode`, now includes fields for multi-channel notifications and timeout handling.

### New Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `channels` | `list[str]` | Communication channels to notify (e.g., `['slack', 'email', 'mobile_push']`). |
| `timeout_seconds` | `int \| None` | Duration to wait for human input before triggering fallback. |
| `fallback_behavior` | `Literal` | Action to take if timeout is exceeded (`fail`, `proceed_with_default`, `escalate`). |

### Example

```python
collab = CollaborationConfig(
    mode=CollaborationMode.INTERACTIVE,
    channels=["slack", "email"],
    timeout_seconds=3600,
    fallback_behavior="escalate"
)
```

## 3. Policy Config (Harvested from Connect)

The `PolicyConfig` class, part of the top-level `RecipeDefinition`, now includes governance rules for spending and sensitive tool usage.

### New Fields

| Field | Type | Description |
| :--- | :--- | :--- |
| `budget_cap_usd` | `float \| None` | Hard limit for estimated token + tool costs. Execution halts if exceeded. |
| `token_budget` | `int \| None` | Max tokens for the assembled prompt. Low-priority contexts will be pruned if exceeded. |
| `sensitive_tools` | `list[str]` | List of tool names that ALWAYS require human confirmation, overriding node-level interaction configs. |

### Example

```python
policy = PolicyConfig(
    max_retries=3,
    budget_cap_usd=50.00,
    token_budget=8000,
    sensitive_tools=["delete_database", "refund_payment"]
)
```

## 4. Embedded Simulations (Harvested from Simulacrum)

The `RecipeDefinition` now includes a `tests` field, allowing authors to embed self-contained test scenarios directly within the recipe manifest.

### New Field

| Field | Type | Description |
| :--- | :--- | :--- |
| `tests` | `list[SimulationScenario]` | A list of `SimulationScenario` objects defining inputs and expected validation logic. |

### Example

```python
from coreason_manifest.spec.simulation import SimulationScenario, ValidationLogic

tests = [
    SimulationScenario(
        id="happy-path-1",
        description="Verify basic Q&A",
        inputs={"query": "Hello"},
        validation_logic=ValidationLogic.EXACT_MATCH
    )
]

recipe = RecipeDefinition(
    ...,
    tests=tests
)
```

## 5. Cognitive Profile (Harvested from Weaver)

The `AgentNode` now supports an inline `CognitiveProfile` (`construct` field) to configure the agent's identity, mode, environment, and task directly. This pattern is documented in [The Assembler Pattern](assembler_pattern.md).
