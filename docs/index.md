# Welcome to Coreason Manifest

This is the central documentation index for the `coreason-manifest` project, which defines the standard schemas, protocols, and governance models for the Coreason AI ecosystem.

## Core Documentation

*   **[Usage Guide](usage.md)**
    *   A comprehensive guide on how to use `coreason-manifest` to define agents, recipes, and work with the library's core concepts programmatically.

*   **[Builder SDK](builder_sdk.md)**
    *   Documentation for the fluent Builder API (`AgentBuilder`, `TypedCapability`) to simplify Agent creation.

*   **[Visualization Tools](visualization.md)**
    *   Guide for generating Mermaid.js flowcharts to visualize complex Agent workflows and routing logic.

*   **[Secure Composition](composition.md)**
    *   Explains the Secure Recursive Loader, the `$ref` syntax for modular composition, the "Jail" security model, and cycle detection mechanisms.

*   **[Governance & Policy Enforcement](governance_policy_enforcement.md)**
    *   Details the Governance module for defining and enforcing organizational rules, risk levels, and compliance policies on agents and tools.

*   **[Agent Card Generator](agent_card_generator.md)**
    *   Guide for using the automated documentation utility to generate standardized "Agent Cards" from Manifest definitions.

*   **[Mock Data Factory](mock_factory.md)**
    *   Utility for generating deterministic, schema-compliant synthetic data for Agent outputs and testing.

*   **[CLI Reference](cli.md)**
    *   Complete documentation for the `coreason` CLI, including the `init` command for project scaffolding.

*   **[Interop Layer](cli_interop.md)**
    *   Documentation for the dynamic loader utility and interoperability features.

## Specifications & Protocols

*   **[Coreason Agent Manifest (CAM) Specification](cap/specification.md)**
    *   The authoritative "Human-Centric" YAML format specification for defining Agents, Recipes, Workflows, and their components.

*   **[Coreason Agent Protocol (CAP) Wire Format](cap/wire_protocol.md)**
    *   Defines the runtime wire protocol, including standard request/response envelopes (`ServiceRequest`, `ServiceResponse`) and streaming contracts (`StreamPacket`).

*   **[Graph Recipes (Work Package JJ)](graph_recipes.md)**
    *   Describes the system for non-linear, cyclic graph execution using `RecipeDefinition` and `GraphTopology`.

*   **[Explicit Streaming Contracts](cap/streaming_contracts.md)**
    *   Defines the contracts for Agent execution (`atomic`, `graph`) and delivery modes (`request_response`, `server_sent_events`).

*   **[Stream Identity & Lifecycle](cap/stream_lifecycle.md)**
    *   Protocols and data structures for explicit, multiplexed output streams (`STREAM_START`, `STREAM_END`).

*   **[Memory Governance](memory_governance.md)**
    *   Declarative configuration for agent memory eviction policies (Sliding Window, Summary, etc.) and `MemoryConfig` models.

*   **[Session Management](session_management.md)**
    *   Architecture for strict, immutable, and stateless management of conversational memory (`SessionState`, `MemoryStrategy`).

*   **[Evaluation Metadata](evaluation_metadata.md)**
    *   Specifications for embedding testing requirements (`EvaluationProfile`) and quality criteria (`SuccessCriterion`) directly into Agent Definitions.

*   **[Active Memory Interface](active_memory_interface.md)**
    *   Protocol (`SessionHandle`) for active agent interactions with storage (history, recall, persistent variables).

*   **[Request Lineage Implementation](request_lineage_implementation.md)**
    *   Details the tracking of cryptographic causality, distributed tracing IDs (`request_id`, `root_request_id`), and auto-rooting logic.

*   **[Observability & Tracing](observability.md)**
    *   Standard telemetry envelopes (`CloudEvent`, `ReasoningTrace`) for system notifications, audit logs, and distributed tracing.

*   **[Audit Hashing & Integrity](audit_hashing.md)**
    *   Specifications for the "Tamper-Evident" audit logging system, including the `AuditLog` model and SHA-256 chain verification algorithms.

*   **[Standardized Presentation Schemas](presentation_schemas.md)**
    *   Enforces strictly typed Pydantic models for UI events (`PresentationEvent`) like citations, progress indicators, and media carousels.

*   **[Frontend Integration & Graph Events](frontend_integration.md)**
    *   Defines the strict `GraphEvent` hierarchy for internal engine state and the migration strategy to standard `CloudEvent` formats.

*   **[Event Content Types](event_content_types.md)**
    *   Specification of standard MIME types (`EventContentType`) used in CloudEvents for protocol compliance.

*   **[Semantic Error Handling](error_handling_standards.md)**
    *   Defines standard Error Domains and the `UserErrorEvent` for structured, user-friendly error reporting.

*   **[Middleware Extension Interfaces](middleware_extension_interfaces.md)**
    *   Defines the protocols (`IRequestInterceptor`, `IResponseInterceptor`) and context models for injecting cross-cutting logic like PII redaction and rate limiting.

## Architecture & Rationale

*   **[Product Requirements & Philosophy](product_requirements.md)**
    *   Outlines the "Shared Kernel" philosophy, architectural standards, and the role of `coreason-manifest` as the definitive source of truth ("The Blueprint").

*   **[Package Structure & Architecture](package_structure.md)**
    *   Explains the physical structure of the package (`spec/` vs `utils/`) and the strict separation of Pure Data Specifications from Utility Logic.

*   **[CoReasonBaseModel Rationale](coreason_base_model_rationale.md)**
    *   Explains the architectural decision to use `CoReasonBaseModel` for solving JSON serialization challenges with UUIDs and Datetimes.
