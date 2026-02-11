# Agent Definitions

## Overview
This module defines the core structure of an AI Agent, including its persona, goals, tools, and knowledge sources. Agents can also be configured with specific capabilities.

## Application Pattern
This example demonstrates the configuration of an `AgentNode` with specific capabilities and constraints.

```python
# Example: Defining a Support Agent with Semantic Model Constraints
from coreason_manifest.spec.core.nodes import AgentNode, Brain
from coreason_manifest.spec.core.engines import ReasoningEngine, Reflex, Supervision

# Define the Cognitive Engine
brain = Brain(
    role="Customer Service Representative",
    persona="You are a helpful assistant with 10 years of experience.",
    reasoning=ReasoningEngine(
        model="gpt-4-turbo",
        thoughts_max=3,
        min_confidence=0.8
    ),
    reflex=Reflex(
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
    brain=brain,
    tools=["zendesk-search"],
    supervision=Supervision(
        strategy="restart",
        max_retries=3,
        fallback="escalate-to-human"
    )
)
```

## API Reference

::: coreason_manifest.spec.core.nodes.AgentNode

::: coreason_manifest.spec.core.nodes.Brain

### Engines

::: coreason_manifest.spec.core.engines.ReasoningEngine

::: coreason_manifest.spec.core.engines.Reflex

::: coreason_manifest.spec.core.engines.Supervision
