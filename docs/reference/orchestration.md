# Orchestration

## Overview
The Orchestration module controls the lifecycle and execution graph of an AI agent workflow (Recipe). It defines the `RecipeDefinition` as the root manifest and `GraphTopology` for the control flow.

For details on defining the agents within this graph, see [Agent Definitions](agents.md).
Governance policies that apply to these recipes are detailed in [Governance & Compliance](governance.md).

## Application Pattern
Here is an example of how to define a simple linear recipe using `RecipeDefinition` and `GraphTopology`.

```python
# Example: Defining a Recipe with a simple Agent loop
from coreason_manifest import (
    RecipeDefinition,
    GraphTopology,
    AgentNode,
    ManifestMetadata
)
from coreason_manifest.spec.v2.recipe import GraphEdge, RecipeStatus

# Define the Nodes
agent_node = AgentNode(
    id="research_agent",
    agent_ref="agents/researcher.yaml",
    system_prompt_override="You are a helpful research assistant."
)

# Define the Graph
topology = GraphTopology(
    nodes=[agent_node],
    edges=[],  # Single node has no edges
    entry_point="research_agent"
)

# Define the Recipe
recipe = RecipeDefinition(
    metadata=ManifestMetadata(
        name="Research Workflow",
        version="1.0.0"
    ),
    status=RecipeStatus.DRAFT,
    topology=topology,
    interface={} # Define inputs/outputs schema
)
```

## API Reference

### RecipeDefinition

::: coreason_manifest.spec.v2.recipe.RecipeDefinition

### GraphTopology

::: coreason_manifest.spec.v2.recipe.GraphTopology

### AgentNode

::: coreason_manifest.spec.v2.recipe.AgentNode
# Orchestration Core

## Architecture

This diagram illustrates the structure of a `RecipeDefinition` and the inheritance hierarchy of `RecipeNode`.

```mermaid
classDiagram
    %% SOTA Styling Init
    %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffecb3', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#e1f5fe'}}}%%

    class RecipeDefinition {
        +ManifestMetadata metadata
        +RecipeInterface interface
        +PolicyConfig policy
        +GraphTopology topology
        +list~Constraint~ requirements
        +StateDefinition state
        +ComplianceConfig compliance
        +IdentityRequirement identity
        +GuardrailsConfig guardrails
    }
    class GraphTopology {
        +str entry_point
        +list~RecipeNode~ nodes
        +list~GraphEdge~ edges
    }
    class RecipeNode {
        <<Abstract>>
        +str id
        +dict metadata
        +NodePresentation presentation
        +InteractionConfig interaction
        +RecoveryConfig recovery
        +ReasoningConfig reasoning
    }
    class AgentNode {
        +str agent_ref
        +CognitiveProfile cognitive_profile
        +ModelSelectionPolicy model_policy
        +str system_prompt_override
        +dict inputs_map
    }
    class RouterNode {
        +str input_key
        +dict routes
        +str default_route
    }
    class HumanNode {
        +str prompt
        +int timeout_seconds
        +str required_role
    }
    class EvaluatorNode {
        +str target_variable
        +str evaluator_agent_ref
        +EvaluationProfile evaluation_profile
        +float pass_threshold
        +int max_refinements
        +str pass_route
        +str fail_route
        +str feedback_variable
    }
    class GenerativeNode {
        +str goal
        +SolverConfig solver
        +list~str~ allowed_tools
        +dict output_schema
    }
    class RecipeInterface {
        +dict inputs
        +dict outputs
    }
    class PolicyConfig {
        +int max_retries
        +int timeout_seconds
        +str execution_mode
        +ExecutionPriority priority
    }

    RecipeDefinition *-- GraphTopology : contains
    RecipeDefinition *-- RecipeInterface : contains
    RecipeDefinition *-- PolicyConfig : contains
    GraphTopology *-- RecipeNode : contains
    RecipeNode <|-- AgentNode : inherits
    RecipeNode <|-- RouterNode : inherits
    RecipeNode <|-- HumanNode : inherits
    RecipeNode <|-- EvaluatorNode : inherits
    RecipeNode <|-- GenerativeNode : inherits

    %% Aggregation
    AgentNode o-- AgentDefinition : agent_ref (ID)

    class AgentDefinition {
        <<External>>
    }

    %% Styling Classes
    classDef root fill:#ffecb3,stroke:#ffb74d,stroke-width:2px;
    classDef config fill:#e1f5fe,stroke:#4fc3f7,stroke-width:1px;
    classDef node fill:#e0f2f1,stroke:#4db6ac,stroke-width:1px;
    classDef abstract fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1px,stroke-dasharray: 5 5;
    classDef external fill:#fff3e0,stroke:#ffcc80,stroke-width:1px,stroke-dasharray: 2 2;

    %% Apply Styles
    class RecipeDefinition root;
    class GraphTopology,RecipeInterface,PolicyConfig config;
    class AgentNode,RouterNode,HumanNode,EvaluatorNode,GenerativeNode node;
    class RecipeNode abstract;
    class AgentDefinition external;
```
