# Resilience Strategies

When orchestrating autonomous agents, failures are inevitable. External APIs timeout, LLMs generate malformed JSON, and governance boundaries are crossed. `coreason_manifest` provides a robust error-handling architecture through `ResilienceStrategies` embedded within a `SupervisionPolicy`.

This guide outlines how to configure `RetryStrategy`, `FallbackStrategy`, and `ReflexionStrategy` to build fault-tolerant AI workflows.

## The Supervision Layer

Resilience is managed by the `SupervisionPolicy` which intercepts exceptions raised during node execution (e.g., `ToolExecutionError`, `OutputParsingError`). By mapping specific exceptions to specific strategies, your `GraphFlow` can recover gracefully.

## Implementing Retry Logic

The `RetryStrategy` handles transient errors, such as rate limits or network timeouts.

```python
from coreason_manifest.core.oversight.resilience import RetryStrategy
from coreason_manifest.core.workflow.nodes import AgentNode

# Configure an exponential backoff retry strategy for API timeouts
api_retry = RetryStrategy(
    max_retries=3,
    base_delay_seconds=2,
    exponential_backoff=True,
    jitter=True
)

# Apply to a node that heavily relies on external services
search_agent = AgentNode(
    id="web_searcher",
    system_prompt="Search the web for real-time news.",
    resilience_policy={"TimeoutException": api_retry}
)
```

!!! note "Idempotency Considerations"
    When applying a `RetryStrategy` to nodes that perform side effects (e.g., writing to a database), ensure the operation is idempotent.

## Configuring Fallback Mechanisms

The `FallbackStrategy` dictates a secondary execution path when a node persistently fails. This is crucial for maintaining flow continuity when primary services are down.

```python
from coreason_manifest.core.oversight.resilience import FallbackStrategy

# Provide a static response when a summarization API fails
summary_fallback = FallbackStrategy(
    static_output="Summary unavailable due to temporary service disruption.",
    log_level="ERROR"
)

summarizer = AgentNode(
    id="doc_summarizer",
    system_prompt="Summarize the provided text.",
    resilience_policy={"ServiceUnavailableException": summary_fallback}
)
```

## Leveraging Reflexion Strategy

The `ReflexionStrategy` is an advanced mechanism for handling logic or output formatting errors (e.g., an LLM returns raw text instead of the requested JSON schema). It prompts the agent to self-correct based on the error message.

```python
from coreason_manifest.core.oversight.resilience import ReflexionStrategy

# When the LLM outputs malformed JSON, send the error back and prompt for correction
json_reflexion = ReflexionStrategy(
    max_attempts=2,
    feedback_prompt="Your previous output failed validation: {error_details}. Please fix the JSON."
)

structured_extractor = AgentNode(
    id="data_extractor",
    system_prompt="Extract names and dates into JSON.",
    resilience_policy={"ValidationError": json_reflexion}
)
```

## Best Practices

*   **Target Specific Errors:** Avoid catch-all retry policies (`Exception: RetryStrategy`). Map strategies to specific failure modes to prevent endless loops on fatal errors.
*   **Monitor Fallbacks:** Extensive use of fallbacks can hide underlying system issues. Always configure telemetry to log when a fallback strategy is triggered.