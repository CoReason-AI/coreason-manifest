# Active Defense: Guardrails & Sentinel

Coreason V2 introduces an **Active Defense** layer (`GuardrailsConfig`) to complement the passive governance model. While Policy Governance (`PolicyConfig`) sets static limits (timeouts, retries), Guardrails define dynamic, runtime protection mechanisms that can halt execution based on statistical anomalies.

This configuration is consumed by the **Sentinel** service (runtime monitor).

## Guardrails Schema (`GuardrailsConfig`)

The `guardrails` field in a `RecipeDefinition` allows you to configure three key defense mechanisms:

1.  **Circuit Breakers**: Automated stoppage when error rates spike.
2.  **Drift Detection**: Alerts when inputs/outputs deviate from a baseline distribution.
3.  **Spot Checks**: Sampling rate for human quality assurance.

```python
from coreason_manifest.spec.v2.guardrails import (
    GuardrailsConfig,
    CircuitBreakerConfig,
    DriftConfig,
    BreakerScope
)

guardrails = GuardrailsConfig(
    # 1. Stop if > 50% failure rate in 1 minute
    circuit_breaker=CircuitBreakerConfig(
        failure_rate_threshold=0.5,
        window_seconds=60,
        recovery_timeout_seconds=300,
        scope=BreakerScope.RECIPE
    ),

    # 2. Flag if semantic distance > 0.4 from 'gold-standard'
    drift_check=DriftConfig(
        input_drift_threshold=0.4,
        output_drift_threshold=0.4,
        baseline_dataset_id="gold-standard-v1"
    ),

    # 3. Randomly sample 5% of traces for human review
    spot_check_rate=0.05
)
```

## 1. Circuit Breakers (`CircuitBreakerConfig`)

Prevents cascading failures by temporarily disabling an agent or the entire recipe when error rates exceed a threshold.

*   `failure_rate_threshold` (float): The error rate (0.0 - 1.0) that triggers the breaker. e.g., `0.5` means 50% of requests failed.
*   `window_seconds` (int): The rolling time window to calculate the rate (e.g., 60 seconds).
*   `recovery_timeout_seconds` (int): How long to keep the breaker open (blocking requests) before attempting a "half-open" state to test recovery.
*   `scope` (`BreakerScope`):
    *   `AGENT`: Only disable this specific agent instance.
    *   `RECIPE`: Pause the entire workflow.
    *   `GLOBAL`: (Rare) Pause the entire system.

## 2. Drift Detection (`DriftConfig`)

Detects **Out-of-Distribution (OOD)** data—inputs or outputs that are semantically distinct from the training/baseline data. This helps identify hallucinations or concept drift.

*   `input_drift_threshold` (float | None): Maximum allowed cosine distance (or similar metric) from the baseline embedding cluster for inputs. Lower is stricter.
*   `output_drift_threshold` (float | None): Maximum allowed distance for outputs.
*   `baseline_dataset_id` (str | None): The ID of the dataset used as the "normal" baseline.

## 3. Spot Checks (`spot_check_rate`)

A simple probability (0.0 - 1.0) that any given execution trace will be flagged for human review. This is essential for continuous improvement and quality assurance in production.

*   `spot_check_rate`: `0.05` implies 5% of traffic is flagged.

## Integration with Recipe

The `guardrails` block sits alongside `policy` and `compliance` in the `RecipeDefinition`.

```python
recipe = RecipeDefinition(
    ...,
    policy=PolicyConfig(max_retries=3),       # Static Limits
    guardrails=guardrails,                    # Active Defense
    compliance=ComplianceConfig(...)          # Audit Logging
)
```

### Difference from Policy & Compliance

| Component | Focus | Example | Action |
| :--- | :--- | :--- | :--- |
| **Policy** | Governance | "Max 3 retries" | Hard limit enforcement |
| **Compliance** | Audit | "Log all PII" | Logging & Artifact generation |
| **Guardrails** | **Active Defense** | "Error rate > 50%" | **Dynamic Stoppage (Circuit Breaker)** |
