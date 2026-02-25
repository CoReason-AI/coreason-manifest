# ADR-002: Adoption of Linear vs. Graph Flow Topology

**Status:** Accepted
**Context:** The "Manifest" and "Recipe" abstractions were ambiguous and failed to clearly distinguish between deterministic sequences and cyclic graphs. This led to confusion in runtime behavior and hindered the adoption of SOTA patterns.
**Decision:** We are abandoning `Manifest` and `Recipe` in favor of a rigorous `LinearFlow` vs `GraphFlow` topology. We are also renaming internal components to align with SOTA engineering standards.

## Topological Determinism

We moved away from `Manifest` (static) to `Flow` (executable) to accurately represent the runtime behavior.

*   **LinearFlow**: Represents a deterministic sequence of steps.
*   **GraphFlow**: Represents a cyclic graph structure with branching and loops.

## Component Renaming

We are adopting standard terminology from Multi-Agent Systems, Actor Model, and DSPy.

| Old Concept (Legacy) | New Concept (Core) | Rationale |
| :--- | :--- | :--- |
| `ManifestV2` | `LinearFlow` | A deterministic script must be a "Sequence". |
| `RecipeDefinition` | `GraphFlow` | Explicitly describes the Cyclic Graph structure. |
| `StateDefinition` | `Blackboard` | "Blackboard Pattern" implies shared multi-agent memory. |
| `Episteme` | `ReasoningConfig` | System 2 slow-thinking logic. |
| `Cortex` | `FastPath` | System 1 fast-response logic. |
| `Maco` | `Supervision` | "Supervisor Pattern" (Erlang) > "Error Handling". |
| `Foundry` | `Optimizer` | DSPy-style self-improvement/compilation. |
| `CognitiveProfile` | `CognitiveProfile` | The active processing unit of an agent. |
| `RouterNode` | `SwitchNode` | Visual metaphor for branching logic tracks. |
| `GenerativeNode` | `PlannerNode` | A node that dynamically plans/solves. |
| `SemanticRef` | `PlaceholderNode` | An empty slot to be filled later. |

## The Architectural Doctrine

### Supervision (not Recovery)
We adopt the Actor Model (Erlang/Akka) philosophy. We do not just "recover" from errors passively; we implement a Supervisor hierarchy that actively manages the lifecycle, retries, and containment of crashing nodes.

### Optimizer (not Foundry)
We adopt the DSPy / TextGrad philosophy. Agents are not static artifacts to be "founded"; they are compiled programs to be optimized against a metric using teacher models and few-shot selectors.

### Blackboard (not State)
We adopt the Blackboard Pattern (Multi-Agent Systems). "State" is ambiguous (local vs global). Blackboard explicitly defines a shared, observable memory space that distinct autonomous agents read from and write to asynchronously.

### Flow (not Manifest)
We adopt the Workflow Topology (Airflow/Prefect) model. "Manifest" implies a static configuration file (like Kubernetes YAML). Flow implies a directed execution graph with runtime properties.
