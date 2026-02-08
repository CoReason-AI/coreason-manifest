# Episteme: Meta-Cognition & Reasoning

The **Episteme Schema** (`coreason_manifest.spec.v2.reasoning`) defines the "System 2" capabilities of an agent. It allows a `Recipe` to configure advanced meta-cognitive loops, such as self-correction, adversarial review, and knowledge gap scanning.

Additionally, this schema includes the "System 1" **Reflex** configuration for fast-path execution.

## Core Concepts

### 1. Reasoning Configuration (System 2)

The `ReasoningConfig` model governs the depth of thought applied *before* or *after* a response is generated.

#### Review Strategy

The `ReviewStrategy` defines how the output is critiqued.

*   `NONE` (`"none"`): No critique step. Default.
*   `BASIC` (`"basic"`): Simple self-correction loop where the model reviews its own output.
*   `ADVERSARIAL` (`"adversarial"`): A "Devil's Advocate" reviewer challenges the output.
*   `CAUSAL` (`"causal"`): Checks for logical consistency and fallacies.
*   `CONSENSUS` (`"consensus"`): Uses multi-model agreement (see Council features).

#### Adversarial Review

If `strategy="adversarial"`, the `AdversarialConfig` controls the critic:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `persona` | `str` | `"skeptic"` | The persona of the critic (e.g., "security_auditor"). |
| `attack_vectors` | `list[str]` | `[]` | Specific angles of critique (e.g., "pii_leakage"). |
| `temperature` | `float` | `0.7` | Creativity level of the critique. |

#### Knowledge Gap Scanning

The `GapScanConfig` enables pre-execution validation:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled` | `bool` | `False` | Scans context for missing prerequisites. |
| `confidence_threshold` | `float` | `0.8` | Min confidence to proceed without asking clarifying questions. |

### 2. Reflex Configuration (System 1)

The `ReflexConfig` enables fast-path execution, bypassing deep reasoning for simple, high-confidence queries.

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled` | `bool` | `True` | Allow fast-path responses. |
| `confidence_threshold` | `float` | `0.9` | Minimum confidence required to skip the solver loop. |
| `allowed_tools` | `list[str]` | `[]` | Read-only tools permissible in Reflex mode (e.g., "get_time"). |

## Integration with Cognitive Profile

The `CognitiveProfile` (in `coreason_manifest.spec.v2.agent`) includes both `reasoning` and `reflex` fields.

```python
from coreason_manifest.spec.v2.agent import CognitiveProfile
from coreason_manifest.spec.v2.reasoning import (
    ReasoningConfig,
    ReflexConfig,
    ReviewStrategy,
    AdversarialConfig
)

# Define a robust agent with fast and slow thinking
profile = CognitiveProfile(
    role="security_analyst",

    # System 1: Handle simple checks instantly
    reflex=ReflexConfig(
        enabled=True,
        confidence_threshold=0.95,
        allowed_tools=["lookup_ip_reputation"]
    ),

    # System 2: Deep review for complex analysis
    reasoning=ReasoningConfig(
        strategy=ReviewStrategy.ADVERSARIAL,
        adversarial=AdversarialConfig(
            persona="red_team_lead",
            attack_vectors=["false_negative_risk"]
        ),
        max_revisions=2
    )
)
```
