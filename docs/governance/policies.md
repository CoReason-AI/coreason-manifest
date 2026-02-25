# Governance: Organizational Guardrails

In an autonomous agent system, trust is paramount. The `coreason-manifest` architecture includes a dedicated **Governance Schema** (`src/coreason_manifest/spec/core/governance.py`) that acts as the supreme law for an agent's operation.

This schema is not just a suggestion; it is a strict, declarative object that restricts what a flow is legally or organizationally allowed to do.

## The `Governance` Schema

The `Governance` model sits at the root of a Manifest (or is inherited from a global policy registry). It overrides any individual tool or agent configuration.

```python
class Governance(CoreasonModel):
    max_risk_level: RiskLevel | None
    allowed_domains: list[str]
    circuit_breaker: CircuitBreaker | None
    safety: Safety | None
    audit: Audit | None
    # ... additional constraints
```

### Risk & Network Constraints

#### 1. `max_risk_level`
The absolute ceiling for tool execution risk.
*   **Function:** If set to `STANDARD`, any attempt to execute a `CRITICAL` tool (e.g., database write, code execution) will be rejected by the runtime, *even if the agent explicitly requested it*.
*   **Use Case:** Deploying a "Safe Mode" version of an agent for public testing.

#### 2. `allowed_domains`
A strict allowlist of network boundaries.
*   **Security:** The schema enforces **IDNA canonicalization** (RFC 8785 / IDNA 2008) on all domains. This prevents homograph attacks (e.g., where a malicious actor uses Cyrillic characters to spoof `google.com`).
*   **Scope:** Any tool attempting to contact a URL outside these domains is blocked.

### `CircuitBreaker` Schema
Defines the structural thresholds that trigger a hard stop to prevent runaway processes or budget drain.

*   **`error_threshold_count`**: Number of consecutive failures allowed before the circuit opens.
*   **`reset_timeout_seconds`**: Time to wait before attempting a "half-open" check.
*   **`fallback_node_id`**: Optional jump target when the circuit is open (e.g., route to a static "System Unavailable" message).

### `Safety` Schema
Configures the data sanitization layer.

*   **`input_filtering`**: Boolean flag to enable prompt injection detection on user inputs.
*   **`pii_redaction`**: Boolean flag to trigger automatic PII (Personally Identifiable Information) scrubbing before data is sent to external LLMs.
*   **`content_safety`**: `high`, `medium`, `low`. Strictness level for output filtering.

### `Audit` Schema
Defines the compliance retention policy.

*   **`trace_retention_days`**: How long full execution traces must be kept.
*   **`log_payloads`**: Boolean flag. If `True`, full request/response bodies are logged. If `False`, only metadata is retained (useful for high-privacy environments).
