# Agent Definitions

## Overview
This module defines the core structure of an AI Agent, including its persona, goals, tools, and knowledge sources. Agents can also be configured with specific capabilities.

## Application Pattern
This example demonstrates the configuration of an `AgentNode` with specific capabilities and constraints.

```python
# Example: Defining a Support Agent with Semantic Model Constraints
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.engines import StandardReasoning, FastPath
from coreason_manifest.spec.core.resilience import SupervisionPolicy, RetryStrategy

# Define the Cognitive Engine
profile = CognitiveProfile(
    role="Customer Service Representative",
    persona="You are a helpful assistant with 10 years of experience.",
    reasoning=StandardReasoning(
        model="gpt-4-turbo",
        thoughts_max=3,
        min_confidence=0.8
    ),
    fast_path=FastPath(
        model="gpt-3.5-turbo",
        timeout_ms=500,
        caching=True
    )
)

# Define the Agent Node
support_agent = AgentNode(
    type="agent",
    id="customer-support-v1",
    metadata={"version": "1.0"},
    profile=profile,
    tools=["zendesk-search"],
    supervision=SupervisionPolicy(
        handlers=[],
        default_strategy=RetryStrategy(max_attempts=3)
    )
)
```

## API Reference

::: coreason_manifest.spec.core.nodes.AgentNode

::: coreason_manifest.spec.core.nodes.CognitiveProfile

### Engines

::: coreason_manifest.spec.core.engines.StandardReasoning

::: coreason_manifest.spec.core.engines.TreeSearchReasoning

::: coreason_manifest.spec.core.engines.DecompositionReasoning

::: coreason_manifest.spec.core.engines.CouncilReasoning

::: coreason_manifest.spec.core.engines.FastPath

### Resilience

::: coreason_manifest.spec.core.resilience.SupervisionPolicy

::: coreason_manifest.spec.core.resilience.ErrorHandler

::: coreason_manifest.spec.core.resilience.ResilienceStrategy

::: coreason_manifest.spec.core.resilience.RetryStrategy

::: coreason_manifest.spec.core.resilience.FallbackStrategy

::: coreason_manifest.spec.core.resilience.ReflexionStrategy

::: coreason_manifest.spec.core.resilience.EscalationStrategy
