# Welcome to Coreason Manifest

This is the central documentation index for the `coreason-manifest` project, which defines the standard schemas, protocols, and governance models for the Coreason AI ecosystem.

## Core Documentation

*   **[Usage Guide](usage.md)**
    *   A comprehensive guide on how to use `coreason-manifest` to define agents, recipes, and work with the library's core concepts programmatically.

*   **[Secure Composition](composition.md)**
    *   Explains the Secure Recursive Loader, the `$ref` syntax for modular composition, the "Jail" security model, and cycle detection mechanisms.

*   **[Governance & Policy Enforcement](governance_policy_enforcement.md)**
    *   Details the Governance module for defining and enforcing organizational rules, risk levels, and compliance policies on agents and tools.

## Specifications & Protocols

*   **[Coreason Agent Manifest (CAM) Specification](cap/specification.md)**
    *   The authoritative "Human-Centric" YAML format specification for defining Agents, Recipes, Workflows, and their components.

*   **[Coreason Agent Protocol (CAP) Wire Format](cap/wire_protocol.md)**
    *   Defines the runtime wire protocol, including standard request/response envelopes (`ServiceRequest`, `ServiceResponse`) and streaming contracts (`StreamPacket`).

*   **[Observability & Tracing](observability.md)**
    *   Standard telemetry envelopes (`CloudEvent`, `ReasoningTrace`) for system notifications, audit logs, and distributed tracing.

*   **[Semantic Error Handling](error_handling_standards.md)**
    *   Defines standard Error Domains and the `UserErrorEvent` for structured, user-friendly error reporting.

## Architecture & Rationale

*   **[Product Requirements & Philosophy](product_requirements.md)**
    *   Outlines the "Shared Kernel" philosophy, architectural standards, and the role of `coreason-manifest` as the definitive source of truth ("The Blueprint").

*   **[CoReasonBaseModel Rationale](coreason_base_model_rationale.md)**
    *   Explains the architectural decision to use `CoReasonBaseModel` for solving JSON serialization challenges with UUIDs and Datetimes.
