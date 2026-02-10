# Agent Capabilities

## Overview
This module defines the feature flags and architectural capabilities of an agent, such as history support and delivery mode.

## Application Pattern
This example shows how to configure an agent's capabilities to support server-sent events (streaming) and disable history for a stateless micro-agent.

```python
# Example: Configuring Agent Capabilities
from coreason_manifest.spec.common.capabilities import AgentCapabilities, DeliveryMode, CapabilityType

capabilities = AgentCapabilities(
    type=CapabilityType.ATOMIC,
    delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    history_support=False
)
```

## API Reference

::: coreason_manifest.spec.common.capabilities.AgentCapabilities
