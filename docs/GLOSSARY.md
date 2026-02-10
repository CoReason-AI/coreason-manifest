# Domain Glossary

This document defines the ubiquitous language used across the Coreason AI ecosystem. It ensures that terms like "Context," "State," and "Recipe" have exact, agreed-upon definitions to prevent miscommunication between Builder, Engine, and Analyst.

## A

### Agent Definition
The static blueprint defining an agent's capabilities, identity, and cognitive parameters. Distinct from an "Agent Runner" (the execution process).

### Assembler Pattern
The composition strategy of defining agent cognitive architectures inline (`construct`) within the Manifest, rather than referencing monolithic pre-built agents. It transforms the Manifest into a configuration file for the Weaver. See [The Assembler Pattern](assembler_pattern.md).

## B

### Blackboard
The shared state dictionary (`StateDefinition`) accessible to all nodes in a Graph Recipe. It serves as the "working memory" where inputs are mapped and outputs are merged. See [Graph Recipes](graph_recipes.md).

### Blueprint Philosophy, The
"If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run." The core philosophy of `coreason-manifest`, ensuring that the manifest is the immutable gatekeeper for the Agent Development Lifecycle. See [Vignette](VIGNETTE.md).

## C

### Cognitive Profile
The inline definition of an agent's identity, mode, environment, and cognition strategies within the Assembler Pattern.

### Constraint (Feasibility)
Logic gates defined in `RecipeDefinition.requirements` that the runtime must validate against the environment state *before* execution (e.g., "User must be admin"). See [Graph Recipes](graph_recipes.md).

## D

### Draft vs. Published Status
The lifecycle states of a Recipe. `DRAFT` allows for semantic references and incomplete topologies (Intent-based), while `PUBLISHED` enforces concrete IDs and structural integrity (Execution-ready).

## E

### Episteme
The framework for meta-cognition, self-correction, and "System 2" thinking within Coreason V2. It enables agents to critique their own work, detect knowledge gaps, and reason about their reasoning. See [Episteme Reasoning](episteme_reasoning.md).

### Evaluator-Optimizer
A pattern where a dedicated `EvaluatorNode` critiques the output of a Generator agent and loops back for refinements until a quality threshold is met.

## G

### Generative Component
A specific UI widget (e.g., Data Grid, Kanban Board, Code Editor) instantiated dynamically by the agent's manifest (`ComponentSpec`) rather than being hardcoded in the frontend application.

### Governance Policy
Static analysis rules (allowlists, risk levels) enforced at build time to ensure organizational standards and security compliance (e.g., "No tools from untrusted domains"). Distinct from runtime feasibility checks. See [Governance Policy Enforcement](governance_policy_enforcement.md).

## M

### Magentic UI
An interface paradigm where the user and agent collaborate on shared, mutable state objects (co-planning). In a Magentic UI, the agent can "draft" a plan or document, which the user can then "edit" directly before execution resumes.

## P

### Passive Definition, Active Execution
A core runtime principle stating that the Manifest is a static, passive declaration of intent, while the Runtime is responsible for *all* side effects and operational limits. See [Runtime Principles](runtime/runtime_principles.md).

## R

### Recipe
The *static definition* (Class) of an orchestration logic, containing the Interface, State, Policy, and Topology. It provides the blueprints that the Runtime Engine executes. See [Graph Recipes](graph_recipes.md).

### Runtime Engine (Executor)
The component responsible for interpreting the `Coreason Manifest` and executing the graph. It handles all side effects, operational limits, tool calls, and policy enforcement.

## S

### SemanticRef
A placeholder used in `DRAFT` recipes to describe *what* an agent should do without selecting a specific tool or model yet. It supports rich metadata for AI Architects.

### Shared Kernel
A passive, pure data library that serves as the definitive source of truth for schemas and contracts within the Coreason ecosystem. It strictly separates `spec` (DTOs) from `utils` (logic) and contains no active execution logic, server capabilities, or side effects upon import. See [Shared Kernel Boundaries](architecture/ADR-001-shared-kernel-boundaries.md).

### Stream Reference
A mechanism allowing agents to emit multiple named, concurrent streams (e.g., `stream_id="thinking"` vs `stream_id="default"`) during execution.

### System 2
Slow, deliberative reasoning loops (Review, Critique) used for deep thinking and self-correction, as opposed to System 1 (Fast generation/Reflex).

## T

### Task Sequence
Syntactic sugar in `RecipeDefinition` that allows defining a simple list of nodes, which is automatically compiled into a full `GraphTopology` with linear edges.

### Topology
The structural layout of a Graph Recipe, defined as a Directed Cyclic Graph (DCG) of Nodes and Edges. It is distinct from the *execution* of the graph.

## V

### Viewport
The high-level layout container (e.g., Chat, Split View, Planner Console, Canvas) requested by an agent via `ViewportMode`. It dictates the overall structure of the Magentic UI for a specific step.

## W

### Workflow (Simulation)
The *runtime instance* (Object) of a Recipe. It represents the actual execution of the graph, preserving state transitions, data flow, and audit trails (schema: `SimulationTrace`).
