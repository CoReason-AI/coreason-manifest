# Orchestration Schemas: Recovery Strategies

When a node fails, the `ResilienceConfig` must decide *how* to recover. The manifest provides a library of strictly typed **Recovery Strategies**, organized as a **Discriminated Union**.

```python
RecoveryStrategy = Annotated[
    RetryStrategy
    | FallbackStrategy
    | ReflexionStrategy
    | EscalationStrategy
    | DiagnosisReasoning
    | HumanHandoffStrategy,
    Field(discriminator="type")
]
```

This guarantees that every strategy is a **configuration blueprint**, not executable code. The runtime is responsible for implementing the logic (e.g., executing the retry, calling the fallback agent).

---

## 1. `RetryStrategy` (`type: retry`)
The most basic form of recovery. Use this for transient failures (e.g., 503 API error, network glitch).
*   **`max_attempts`**: The hard limit on retries.
*   **`backoff_factor`**: Exponential backoff multiplier (e.g., 2.0 = 1s, 2s, 4s).
*   **`jitter`**: Randomizes the delay to prevent thundering herds.

**Note:** The system enforces a **Security Policy**: Retries are *forbidden* for `SECURITY` domain errors (e.g., prompt injection). You must use `EscalationStrategy` or `ReflexionStrategy` instead.

## 2. `FallbackStrategy` (`type: fallback`)
Configures a graceful degradation path. Instead of retrying the failed node, the system routes execution to a designated backup.
*   **`fallback_node_id`**: The ID of the backup node/agent to execute.
*   **`fallback_payload`**: Static data to inject if the node is skipped entirely (e.g., return a default "I don't know" message).

## 3. `ReflexionStrategy` (`type: reflexion`)
A cognitive self-correction loop. The runtime feeds the generated error message (e.g., "JSON schema validation failed: missing key 'summary'") back into the agent's context window for another attempt.
*   **`critic_model`**: The model used to analyze the error (can be the same or a stronger model).
*   **`critic_prompt`**: Instructions for the critic (e.g., "Identify the logic error and propose a fix.").
*   **`include_trace`**: Whether to include the full execution trace in the critic's context.
*   **`critic_schema`**: JSON Schema to enforce structured output from the critic.

## 4. `EscalationStrategy` (`type: escalate`)
Explicitly bubbles the error up to a parent scope (e.g., from a Node up to the GraphFlow's supervision layer) when local recovery is impossible.
*   **`bubble_to`**: Optional target scope (e.g., `flow`, `graph`, `global`). If omitted, defaults to the immediate parent.
*   **`enrich_context`**: Boolean flag to append the local node's blackboard state to the error trace before bubbling up.

## 5. `DiagnosisReasoning` (`type: diagnosis`)
While technically a reasoning config, this schema is used as a specialized recovery step to perform **Root Cause Analysis (RCA)** on complex sub-graph failures.
*   **`diagnostic_model`**: Spawns a dedicated "Debugger Agent" to analyze the failure.
*   **`fix_strategies`**: Allowed remediation actions (e.g., `schema_repair`, `parameter_tuning`, `context_pruning`).

## 6. `HumanHandoffStrategy` (`type: human_handoff`)
Safely suspends execution, persists state, and alerts a human operator for manual resolution before resuming the flow.
*   **`queue_name`**: The task queue where the suspended session will be parked.
*   **`timeout_seconds`**: How long to wait for human intervention before failing completely.
*   **`urgency`**: `low`, `medium`, `high`, `critical`.
*   **Use Case:** Critical business logic failures or high-risk security alerts where automated recovery is unsafe.
