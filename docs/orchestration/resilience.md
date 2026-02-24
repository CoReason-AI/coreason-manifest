# Orchestration Schemas: Resilience & Supervision

In a cognitive architecture, failure is not an exception—it is an expectation. LLMs hallucinate, APIs timeout, and tools return malformed JSON.

The `coreason-manifest` library provides a **Unified Supervision Schema** (`src/coreason_manifest/spec/core/resilience.py`) to handle these failures declaratively. Instead of writing custom `try/except` blocks in every agent, you define **Resilience Policies** in the manifest.

---

## The `ResilienceConfig` Schema

`ResilienceConfig` serves as the top-level container for defining failure tolerance. It acts as a **Supervision Policy** that dictates how the runtime should react when a node fails.

This configuration can be attached at multiple levels:
1.  **Node Level:** Specific rules for a single step (e.g., "Retry this search tool 3 times").
2.  **Flow Level:** Default behavior for an entire workflow.
3.  **Graph Level:** Global safety nets.

### `SupervisionPolicy` (`type: supervision`)

The core of the resilience system is the `SupervisionPolicy`. It functions as a **declarative router for errors**.

```python
class SupervisionPolicy(BaseModel):
    handlers: list[ErrorHandler]
    default_strategy: RecoveryStrategy | None = None
    max_cumulative_actions: int = 10
```

*   **`handlers`**: An ordered list of `ErrorHandler` rules. The runtime iterates through this list; the first handler to match the error triggers its strategy.
*   **`default_strategy`**: A catch-all strategy if no handler matches. If this is `None`, the error bubbles up and crashes the flow (fail-fast).
*   **`max_cumulative_actions`**: A global circuit breaker. It limits the *total* number of recovery attempts (retries + reflexions + fallbacks) to prevent infinite loops.

---

## `ErrorDomain` Classifications

To route errors effectively, the system strictly categorizes failures into **Error Domains**. This taxonomy allows architects to handle a "hallucination" differently than a "503 Service Unavailable."

| Domain | Description | Example |
| :--- | :--- | :--- |
| **`LLM`** | Failures originating from the model provider. | Rate limits, context length exceeded, refusals. |
| **`TOOL`** | Failures within a tool execution. | 404 Not Found, API timeout, malformed tool output. |
| **`SCHEMA`** | Data validation failures. | Output JSON does not match the required Pydantic schema. |
| **`SECURITY`** | Governance violations. | Prompt injection detected, PII leak, unauthorized tool access. |
| **`NETWORK`** | Transport layer issues. | DNS resolution failure, connection reset. |
| **`SYSTEM`** | Internal runtime errors. | Out of memory, worker crash. |

### Matching Logic (`ErrorHandler`)

An `ErrorHandler` maps a specific failure to a recovery strategy using three criteria:

1.  **`match_domain`**: A list of `ErrorDomain`s (e.g., `["NETWORK", "LLM"]`).
2.  **`match_error_code`**: Specific error codes (e.g., `"429"`, `"CRSN-VAL-SCHEMA"`).
3.  **`match_pattern`**: A regex pattern to match against the error message string.

**Logic:**
*   **Intra-field (OR):** If `match_domain=["LLM", "NETWORK"]`, the error can be *either*.
*   **Inter-field (AND):** If both `match_domain` and `match_pattern` are set, *both* must match.

```python
# Example: Retry on Network errors, but only if they mention "timeout"
ErrorHandler(
    match_domain=["NETWORK"],
    match_pattern=".*timeout.*",
    strategy=RetryStrategy(max_attempts=3)
)
```
