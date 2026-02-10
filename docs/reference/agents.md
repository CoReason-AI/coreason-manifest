# Agent Definitions

## Overview
This module defines the core structure of an AI Agent, including its persona, goals, tools, and knowledge sources.

## Application Pattern
This example demonstrates the minimal configuration required to define a compliant agent with a specific tool requirement.

```python
# Example: Defining a Support Agent
from coreason_manifest.spec.v2.definitions import AgentDefinition, ToolRequirement

support_agent = AgentDefinition(
    id="customer-support-v1",
    name="Support Bot",
    role="Customer Service Representative",
    goal="Resolve user inquiries efficiently and politely.",
    backstory="You are a helpful assistant with 10 years of experience.",
    model="gpt-4-turbo",
    tools=[
        ToolRequirement(
            uri="mcp://zendesk/ticket-search",
            hash="sha256:..."
        )
    ],
    knowledge=["s3://company-docs/faq.pdf"]
)
```

## API Reference

::: coreason_manifest.spec.v2.definitions.AgentDefinition

::: coreason_manifest.spec.v2.definitions.ToolRequirement
