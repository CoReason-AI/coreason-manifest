# Council & Ensemble Features

The **Council** feature set, part of the **Ensemble (SPIO)** strategy, introduces advanced multi-agent consensus and diversity controls. This allows a `GenerativeNode` to simulate a "Board of Directors" or "Red Team" dynamic, where multiple diverse plans are generated, critiqued by a dissenter, and ratified by a super-majority.

## Overview

In high-stakes environments (e.g., financial planning, critical infrastructure control), a single AI generated plan—or even a simple majority vote—may not be sufficient. The Council feature set addresses this by enforcing:

1.  **Diversity**: Preventing "Echo Chambers" by ensuring candidate plans are structurally distinct.
2.  **Dissent**: Introducing an adversarial "Devil's Advocate" to challenge assumptions.
3.  **Consensus**: Requiring a configurable quorum (e.g., 60% or 100%) to proceed.

## Configuration

These features are configured within the `SolverConfig` when `strategy="ensemble"`.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `n_samples` | `int` | `1` | The size of the council (number of plans to generate). |
| `diversity_threshold` | `float` | `0.3` | Minimum Jaccard distance (0.0-1.0) required between generated plans. Higher values force more distinct approaches. |
| `enable_dissenter` | `bool` | `False` | If `True`, a dedicated "Dissenter" agent will critique the leading plan(s) before the final vote. |
| `consensus_threshold` | `float` | `0.6` | The percentage of votes (0.0-1.0) required to ratify a plan. |

## Mechanisms

### 1. Diversity Sampling
The solver generates `n_samples` plans. As each plan is generated, it is compared against the existing set using **Jaccard Distance** (based on tool usage and key steps). If a new plan is too similar (distance < `diversity_threshold`), it is rejected and regenerated with a higher "temperature" or different seed prompt to force divergent thinking.

### 2. The Dissenter (Red Teaming)
If `enable_dissenter` is `True`, an adversarial step is injected after plan generation but before voting. The Dissenter reviews the top candidates and produces a "Critique" artifact, highlighting risks, assumptions, and potential failure modes. This critique is injected into the context of the voting agents.

### 3. Voting & Consensus
The generated plans are voted on by the council (or a scoring model).
*   **Simple Majority**: Standard behavior.
*   **Super-Majority**: If `consensus_threshold` is set to `0.8` (80%), a plan must receive 80% of the score mass to be selected.
*   **Gridlock**: If no plan meets the threshold, the solver triggers a "Debate" phase (if configured) or falls back to the highest-scoring plan with a warning metadata flag.

## Example Configuration

```python
from coreason_manifest.spec.v2.recipe import GenerativeNode, SolverConfig, SolverStrategy

council_node = GenerativeNode(
    id="strategic_planning",
    goal="Develop a Q3 marketing strategy",
    output_schema={"type": "object", ...},
    solver=SolverConfig(
        strategy=SolverStrategy.ENSEMBLE,
        n_samples=5,                     # 5 Board Members
        diversity_threshold=0.4,         # Ensure diverse perspectives
        enable_dissenter=True,           # Invite the skeptic
        consensus_threshold=0.75         # Require 75% agreement
    )
)
```
