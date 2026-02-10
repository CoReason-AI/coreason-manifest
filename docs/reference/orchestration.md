# Orchestration Core

## Architecture

This diagram illustrates the structure of a `RecipeDefinition` and the inheritance hierarchy of `RecipeNode`.

```mermaid
classDiagram
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

    %% Styling
    classDef abstract fill:#f9f9f9,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5;
    class RecipeNode abstract;
```
