# Semantic Model Selection & Routing

The CoReason Manifest V2 introduces **Semantic Model Selection**, enabling dynamic routing of LLM requests based on cost, performance, latency, and compliance constraints. This allows Recipes to be resilient to model availability and to optimize for specific business goals without hardcoding model IDs.

## Core Concepts

### Model Selection Policy

The `ModelSelectionPolicy` configuration object defines how the runtime should select a model for a given agent.

```yaml
model_policy:
  strategy: "lowest_cost"
  min_context_window: 16000
  max_input_cost_per_m: 5.00
  compliance:
    - "hipaa"
  provider_whitelist:
    - "azure"
    - "anthropic"
  allow_fallback: true
```

### Routing Strategies

The `strategy` field determines the primary selection algorithm:

*   `priority`: Use the first available model in the list (default behavior).
*   `lowest_cost`: Select the cheapest model that meets all constraints.
*   `lowest_latency`: Select the fastest model based on historical statistics.
*   `performance`: Select the strongest model based on benchmark scores.
*   `round_robin`: Distribute load evenly across qualifying models.

### Compliance Tiers

The `compliance` field ensures data residency and regulatory requirements are met:

*   `standard`: No specific requirements.
*   `eu_residency`: Data must be processed within the EU.
*   `hipaa`: Model provider must be HIPAA compliant.
*   `fedramp`: Model provider must be FedRAMP authorized.

## Usage in Recipes

### Global Default

You can set a default policy for the entire Recipe in the `RecipeDefinition`:

```yaml
kind: Recipe
metadata:
  name: "Financial Analyzer"
default_model_policy:
  strategy: "performance"
  compliance: ["hipaa"]
# ...
```

### Agent-Level Override

Individual `AgentNode`s can override the global policy:

```yaml
- type: "agent"
  id: "summarizer"
  agent_ref: "summarizer-v1"
  model_policy:
    strategy: "lowest_cost" # Override global strategy for this simple task
```

### Direct Model Reference

For backward compatibility or strict requirements, `model_policy` can still be a direct model ID string:

```yaml
- type: "agent"
  id: "legacy-agent"
  agent_ref: "legacy-v1"
  model_policy: "gpt-4-0613" # Forces this specific model
```
