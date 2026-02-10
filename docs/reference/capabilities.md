# Capabilities

## Overview
The Capabilities module manages feature flags and architectural properties of an agent. `AgentCapabilities` defines what an agent *can* do, rather than *how* it does it.

## Application Pattern
This pattern illustrates how to enable complex graph processing and server-sent events for real-time applications.

```python
# Example: Configuring Agent Capabilities
from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode
)

# Enable Graph-based reasoning and SSE
caps = AgentCapabilities(
    type=CapabilityType.GRAPH,
    delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    history_support=True
)

# This configuration tells the runner to:
# 1. Provide a blackboard for state management (GRAPH)
# 2. Stream tokens incrementally (SSE)
# 3. Maintain conversational memory (history_support)
```

## API Reference

### AgentCapabilities

::: coreason_manifest.spec.common.capabilities.AgentCapabilities
