# Welcome to Coreason Manifest

This is the central documentation index for the `coreason-manifest` project, which defines the standard schemas, protocols, and governance models for the Coreason AI ecosystem.

## Core Doctrine: Code is Source of Truth

This project follows the **"Code is Source of Truth"** doctrine. The Pydantic models in `src/coreason_manifest/spec` are the definitive contract. This documentation strives to reflect that reality accurately. If a discrepancy exists, the code takes precedence.

## Core Specifications (V2)

The V2 specification introduces a graph-based architecture for complex agent orchestration.

*   **[Graph Recipes (Orchestration)](graph_recipes.md)**: The definitive guide to `RecipeDefinition` and `GraphTopology`, enabling cycles, conditionals, and advanced flows.
*   **[The Assembler Pattern](assembler_pattern.md)**: Inline agent definitions and cognitive architecture composition.
*   **[Episteme (Meta-Cognition)](episteme_reasoning.md)**: Configuration for System 2 reasoning, review loops, and gap scanning.
*   **[Flow Governance](flow_governance.md)**: Resilience mechanisms including retries, fallbacks, and circuit breakers.
*   **[Identity & Access Management](identity_access_management.md)**: RBAC, user context injection, and security scopes.
*   **[Generative Solvers](generative_solvers.md)**: Configuration for autonomous planning strategies (Tree Search, Ensemble).
*   **[Evaluator-Optimizer](evaluator_optimizer.md)**: Patterns for self-correcting agent loops.

## Runtime Protocols

*   **[Runtime Behavior](behavior.md)**: The expected behavior of the execution engine.
*   **[Transport Layer](transport_layer.md)**: Distributed tracing, request lineage, and the `AgentRequest` envelope.
*   **[Streaming Contracts](cap/streaming_contracts.md)**: Protocols for real-time token streaming and event delivery.
*   **[MCP Runtime](mcp_runtime.md)**: Integration with the Model Context Protocol for tool access.

## Developer Tools

*   **[Builder SDK](builder_sdk.md)**: Fluent API for constructing Agents programmatically.
*   **[CLI Reference](cli.md)**: Guide to the `coreason` command-line interface.
*   **[Agent Card Generator](agent_card_generator.md)**: Automating documentation from manifests.

## Architecture & Governance

*   **[Shared Kernel Strategy](architecture/ADR-001-shared-kernel-boundaries.md)**: The architectural philosophy behind this library.
*   **[Compliance & Audit](veritas_integrity.md)**: The Veritas framework for tamper-evident logging and regulatory compliance.
*   **[Governance Policy](governance_policy_enforcement.md)**: Defining organizational rules and risk limits.
*   **[Observability](observability.md)**: Telemetry standards and `CloudEvent` specifications.
