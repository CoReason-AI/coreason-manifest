# Agent Definitions

## Overview
This module defines the core structure of an AI Agent, including its persona, goals, [tools][coreason_manifest.spec.v2.definitions.ToolRequirement], and knowledge sources. Agents can also be configured with specific [capabilities](../reference/capabilities.md).

## Application Pattern
This example demonstrates the configuration of an [AgentDefinition][coreason_manifest.spec.v2.definitions.AgentDefinition] with specific [ModelProfile][coreason_manifest.spec.v2.resources.ModelProfile] constraints, ensuring the semantic requirements (e.g., context window size) are explicitly defined.

```python
# Example: Defining a Support Agent with Semantic Model Constraints
from coreason_manifest.spec.v2.definitions import AgentDefinition, ToolRequirement
from coreason_manifest.spec.v2.resources import ModelProfile, ResourceConstraints, RateCard, PricingUnit

support_agent = AgentDefinition(
    id="customer-support-v1",
    name="Support Bot",
    role="Customer Service Representative",
    goal="Resolve user inquiries efficiently and politely.",
    backstory="You are a helpful assistant with 10 years of experience.",

    # Semantic Model Definition
    # Instead of just a string ID, we define the required capabilities
    model="gpt-4-turbo",
    resources=ModelProfile(
        provider="openai",
        model_id="gpt-4-turbo",
        constraints=ResourceConstraints(
            context_window_size=128000,
            max_output_tokens=4096
        ),
        pricing=RateCard(
            unit=PricingUnit.TOKEN_1M,
            input_cost=10.00,
            output_cost=30.00
        )
    ),

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

### Resources

::: coreason_manifest.spec.v2.resources.ModelProfile

::: coreason_manifest.spec.v2.resources.ResourceConstraints

::: coreason_manifest.spec.v2.resources.RateCard

::: coreason_manifest.spec.v2.resources.PricingUnit

::: coreason_manifest.spec.v2.resources.ModelSelectionPolicy
