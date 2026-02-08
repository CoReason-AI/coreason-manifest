# The Assembler Pattern

The **Assembler Pattern** transforms the Manifest from a purely passive definition into a configuration file for the **Weaver** (in `coreason-construct`). This allows you to define an agent's cognitive architecture inline, specifying its Identity, Environment, Mode, and Task.

## Concept: Inline Cognitive Architecture

Instead of referencing a pre-built agent by ID (`agent_ref`), you can now define the agent's "Cognitive Profile" directly within the `AgentNode`. This profile tells the Weaver how to assemble the prompt and what context to inject.

### The `CognitiveProfile`

The `CognitiveProfile` consists of four key components:

1.  **Identity (Who)**: The role or persona (e.g., `safety_scientist`).
2.  **Mode (How)**: The reasoning style (e.g., `standard`, `six_hats`, `socratic`).
3.  **Environment (Where)**: Dynamic context modules (`knowledge_contexts`) to inject.
4.  **Task (What)**: The logic primitive to apply (`task_primitive`, e.g., `extract`, `classify`).

## Usage in `AgentNode`

The `AgentNode` now supports a `construct` field. If provided, this inline definition takes precedence over `agent_ref`.

```python
from coreason_manifest.spec.v2.recipe import AgentNode
from coreason_manifest.spec.v2.agent import (
    CognitiveProfile,
    ContextDependency,
    ComponentPriority
)

# Define an inline agent
profile = CognitiveProfile(
    role="senior_editor",
    reasoning_mode="critique",
    knowledge_contexts=[
        ContextDependency(
            name="brand_guidelines",
            priority=ComponentPriority.CRITICAL
        ),
        ContextDependency(
            name="recent_articles",
            priority=ComponentPriority.LOW,
            parameters={"limit": 5}
        )
    ],
    task_primitive="review_and_edit"
)

# Create the node
node = AgentNode(
    id="editor_step",
    construct=profile,
    # agent_ref is optional when construct is used
)
```

## Token Optimization

To support the Weaver's token optimization logic, we've added `ComponentPriority` and `token_budget`.

### Context Priority

Each `ContextDependency` has a `priority` level:
*   `CRITICAL` (10): Must be included.
*   `HIGH` (8): Should be included.
*   `MEDIUM` (5): Standard priority.
*   `LOW` (1): Can be pruned if the budget is tight.

### Global Token Budget

The `PolicyConfig` now includes a `token_budget` field. The Weaver uses this budget to decide which context modules to prune.

```python
from coreason_manifest.spec.v2.recipe import PolicyConfig

policy = PolicyConfig(
    token_budget=8000,  # Max tokens for the assembled prompt
    budget_cap_usd=5.0
)
```
