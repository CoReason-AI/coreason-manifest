# Episteme: Meta-Cognition & Reasoning

Coreason V2 introduces **Episteme**, a framework for meta-cognition that enables agents to critique their own work, detect knowledge gaps, and reason about their reasoning.

This is configured via the `reasoning` field on any `RecipeNode`.

## Concepts

Episteme provides two main capabilities:

1.  **Review Strategies**: How the node output is critiqued (Self-Correction, Devil's Advocate).
2.  **Gap Scanning**: Pre-execution checks for missing prerequisites (Knowledge Gaps).

## Configuration (`ReasoningConfig`)

```python
from coreason_manifest.spec.v2.reasoning import (
    ReasoningConfig,
    ReviewStrategy,
    AdversarialConfig,
    GapScanConfig
)

# Define meta-cognition settings
reasoning = ReasoningConfig(
    strategy=ReviewStrategy.ADVERSARIAL, # "Devil's Advocate"
    max_revisions=3, # Allow up to 3 self-correction loops

    # Strategy-specific config
    adversarial=AdversarialConfig(
        persona="security_auditor",
        attack_vectors=["pii_leakage", "prompt_injection"],
        temperature=0.7
    ),

    # Pre-execution knowledge check
    gap_scan=GapScanConfig(
        enabled=True,
        confidence_threshold=0.9
    )
)

# Attach to a node
node = AgentNode(
    id="writer",
    agent_ref="copywriter-v1",
    reasoning=reasoning
)
```

### 1. Review Strategies (`ReviewStrategy`)

The `strategy` field determines how the node's output is critiqued before being finalized.

*   `NONE`: No review (Default).
*   `BASIC`: Simple self-correction prompt ("Review your work and correct errors").
*   `ADVERSARIAL`: A distinct "Devil's Advocate" persona critiques the output.
*   `CAUSAL`: Checks for logical consistency and fallacies.
*   `CONSENSUS`: Multi-model agreement (requires Council features).

### 2. Adversarial Review (`AdversarialConfig`)

When `strategy="adversarial"`, you can configure the critic's persona.

*   `persona`: The role adopted by the reviewer (e.g., "skeptic", "security_auditor").
*   `attack_vectors`: Specific angles of critique (e.g., "hallucination", "bias").
*   `temperature`: Creativity level of the critique (default: 0.7).

### 3. Gap Scanning (`GapScanConfig`)

Episteme can scan the context *before* execution to ensure all prerequisites are met.

*   `enabled`: If True, runs a check before the agent starts.
*   `confidence_threshold`: Minimum confidence (0.0-1.0) required to proceed without asking clarifying questions.
