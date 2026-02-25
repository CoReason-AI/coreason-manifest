# Traffic Governance & Quality of Service (QoS)

Coreason V2 introduces **Traffic Governance** at the manifest level, allowing Recipes to declare their importance, resource needs, and behavior under load. These settings are consumed by the **CoReason AI Gateway** to enforce rate limits, prioritize critical traffic, and optimize costs.

## Concepts

### 1. Execution Priority (Load Shedding)

The `ExecutionPriority` enum defines the relative importance of a Recipe's execution request. During periods of high congestion, the Gateway may delay or drop lower-priority requests to preserve capacity for critical workloads.

| Level | Value | Description | Use Case |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | 10 | Real-time, user-facing, strictly synchronous. | CEO Chatbot, Customer Support Live Agent. |
| **HIGH** | 8 | Important but slightly tolerant of latency. | Internal Tools, Standard User Requests. |
| **NORMAL** | 5 | Default. Standard priority. | Most background workflows. |
| **LOW** | 2 | Latency-tolerant, can be queued. | Bulk data processing, Analysis jobs. |
| **BATCH** | 1 | Lowest priority, overnight processing. | Daily summaries, archival tasks. |

### 2. Rate Limiting

Recipes can self-impose limits to prevent abuse or control costs.

*   **`rate_limit_rpm` (Requests Per Minute)**: Hard cap on the number of executions started per minute.
*   **`rate_limit_tpm` (Tokens Per Minute)**: Hard cap on the estimated token consumption (input + output).

### 3. Semantic Caching

*   **`caching_enabled`**: If `True` (default), the Gateway is permitted to serve a cached response for identical inputs. This saves cost and latency but may be undesirable for non-deterministic or strictly fresh data requirements.

## Configuration

These settings are defined in the `policy` field of the `RecipeDefinition`.

```python
from coreason_manifest.spec.v2.recipe import RecipeDefinition, PolicyConfig, ExecutionPriority

recipe = RecipeDefinition(
    # ...
    policy=PolicyConfig(
        priority=ExecutionPriority.BATCH, # Run overnight
        rate_limit_rpm=100,               # Don't flood the system
        caching_enabled=True              # Reuse results if possible
    )
)
```

## Gateway Behavior

1.  **Admission Control**: When a request arrives, the Gateway checks the `rate_limit_rpm`. If exceeded, it returns `429 Too Many Requests`.
2.  **Prioritization**: If the system is under heavy load (e.g., GPU saturation), the Gateway prioritizes requests with higher `priority` values. `BATCH` requests may be paused or queued until load subsides.
3.  **Caching**: If `caching_enabled` is True, the Gateway checks its semantic cache (e.g., Redis/Vector DB) for a matching query vector. If found, it returns the cached result immediately.

## Best Practices

*   Use `CRITICAL` sparingly. Overuse dilutes its effectiveness.
*   Set `rate_limit_rpm` for all public-facing or untrusted recipes.
*   Disable `caching_enabled` only if the recipe relies on real-time external data (e.g., "What is the current stock price?").
