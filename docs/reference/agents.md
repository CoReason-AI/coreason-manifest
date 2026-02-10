# Agent Definition

## Architecture

This diagram illustrates the composition of an `AgentDefinition`, highlighting its relationships with resources (Model), tools, and knowledge.

```mermaid
classDiagram
    %% SOTA Styling Init
    %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffecb3', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#e1f5fe'}}}%%

    class AgentDefinition {
        +str id
        +str name
        +str role
        +str goal
        +str backstory
        +list~str~ knowledge
        +list~str~ skills
        +InterfaceDefinition interface
        +AgentCapabilities capabilities
        +AgentRuntimeConfig runtime
        +EvaluationProfile evaluation
        +ModelProfile resources
    }
    class ModelProfile {
        +str provider
        +str model_id
        +RateCard pricing
        +ResourceConstraints constraints
    }
    class ToolRequirement {
        +str uri
        +str hash
    }
    class InlineToolDefinition {
        +str name
        +str description
        +dict parameters
        +str code_hash
    }
    class InterfaceDefinition {
        +dict inputs
        +dict outputs
    }

    %% Composition
    AgentDefinition *-- ModelProfile : resources
    AgentDefinition *-- InterfaceDefinition : interface

    %% Aggregation/Composition for tools (Polymorphic list)
    AgentDefinition o-- ToolRequirement : tools (reference)
    AgentDefinition *-- InlineToolDefinition : tools (embedded)

    %% Note: Knowledge is represented as a list of strings (IDs/Paths) within AgentDefinition

    %% Styling Classes
    classDef root fill:#ffecb3,stroke:#ffb74d,stroke-width:2px;
    classDef config fill:#e1f5fe,stroke:#4fc3f7,stroke-width:1px;
    classDef tool fill:#e0f2f1,stroke:#4db6ac,stroke-width:1px;

    %% Apply Styles
    class AgentDefinition root;
    class ModelProfile,InterfaceDefinition config;
    class ToolRequirement,InlineToolDefinition tool;
```
