# Episteme: Meta-Cognition & Reasoning

Coreason V2 introduces **Episteme**, a meta-cognitive layer that enables agents to "think about their thinking." This allows for self-correction, adversarial review, and knowledge gap analysis before and after execution.

## Concept: The Reasoning Layer

Every `RecipeNode` in a Graph Recipe can be equipped with a `ReasoningConfig`. This configuration dictates how the node should validate its own output or prepare its context before execution.

```python
from coreason_manifest.spec.v2.reasoning import ReasoningConfig, ReviewStrategy

node.reasoning = ReasoningConfig(
    strategy=ReviewStrategy.ADVERSARIAL,
    max_revisions=3
)
```

## Review Strategies

The `ReviewStrategy` enum defines the method used to critique the node's output.

| Strategy | Description |
| :--- | :--- |
| `NONE` | No review. Execution proceeds immediately. |
| `BASIC` | Simple self-correction prompt (e.g., "Check your work"). |
| `ADVERSARIAL` | A "Devil's Advocate" review using a specific persona and attack vectors. |
| `CAUSAL` | Checks for logical consistency and causal fallacies. |
| `CONSENSUS` | (Future) Multi-model agreement/voting. |

## Adversarial Review (`AdversarialConfig`)

When using `ReviewStrategy.ADVERSARIAL`, you can configure the specific persona and angles of attack. This is useful for security auditing, bias detection, or rigorous fact-checking.

```python
from coreason_manifest.spec.v2.reasoning import AdversarialConfig

config = ReasoningConfig(
    strategy=ReviewStrategy.ADVERSARIAL,
    adversarial=AdversarialConfig(
        persona="security_auditor",
        attack_vectors=[
            "pii_leakage",
            "prompt_injection_susceptibility",
            "hallucination"
        ],
        temperature=0.5
    ),
    max_revisions=2
)
```

*   **`persona`**: The role the reviewer adopts (e.g., `skeptic`, `compliance_officer`).
*   **`attack_vectors`**: A list of specific criteria to critique.
*   **`temperature`**: The creativity level of the critique.

## Knowledge Gap Scanning (`GapScanConfig`)

Episteme also supports **Pre-Execution** reasoning via `GapScanConfig`. If enabled, the agent will scan the available context (Blackboard) *before* attempting the task to determine if it has sufficient information.

```python
from coreason_manifest.spec.v2.reasoning import GapScanConfig

config = ReasoningConfig(
    gap_scan=GapScanConfig(
        enabled=True,
        confidence_threshold=0.9
    )
)
```

*   **`enabled`**: If True, the scan runs before the main task.
*   **`confidence_threshold`**: The minimum confidence (0.0 - 1.0) required to proceed. If confidence is lower, the agent may ask clarifying questions (depending on the runtime implementation).

## Integration with Recipe Nodes

The `reasoning` field is available on the base `RecipeNode` class, meaning it can be applied to `AgentNode`, `EvaluatorNode`, and others.

```python
from coreason_manifest.spec.v2.recipe import AgentNode

step1 = AgentNode(
    id="generate_report",
    agent_ref="analyst",
    reasoning=ReasoningConfig(strategy=ReviewStrategy.BASIC)
)
```
