# Welcome to Coreason Manifest

This is the documentation for the `coreason-manifest` project, which defines the standard schemas and protocols for the Coreason AI ecosystem.

## Authoring & Definitions

*   **[Coreason Agent Manifest (CAM V2)](coreason_agent_manifest.md)**: The authoritative "Human-Centric" YAML format for defining Agents and Recipes. Start here if you are building agents.
*   **[Runtime Agent Definition (V1)](runtime_agent_definition.md)**: The machine-optimized execution contract for Agents (Pydantic models).
*   **[Runtime Recipe Definition (V1)](runtime_recipe_definition.md)**: The machine-optimized execution contract for Workflows/Recipes.
*   **[Builder SDK](builder_sdk.md)**: How to generate manifests programmatically using Python.

## Runtime & Execution

*   **[Runtime Deployment Configuration](runtime_deployment_configuration.md)**: "Zero-Surprise Deployment" specs for hosting agents.
*   **[V2 Loader Bridge](v2_bridge.md)**: How the engine compiles V2 YAML manifests into V1 Runtime objects.
*   **[Atomic Agents](atomic_agents.md)**: Deep dive into Atomic (Prompt-based) vs Graph-based topologies.
*   **[Session Management](session_management.md)**: Decoupling execution from memory with standardized Session and Interaction models.
*   **[Agent Behavior Protocols](agent_behavior_protocols.md)**: The standard interfaces (`AgentInterface`) for agent implementation.

## Interfaces & Contracts

*   **[Interface Contracts](interface_contracts.md)**: Defining input/output schemas.
*   **[Transport-Layer Specification](transport_layer_specification.md)**: The HTTP/SSE contract for serving agents.
*   **[Event Content-Types](event_content_types.md)**: Standard MIME types.
*   **[Agent Request Envelope](agent_request_envelope.md)**: The standard envelope for agent invocations.
*   **[SSE Wire Protocol](sse_wire_protocol.md)**: Server-Sent Events spec.

## Observability & Governance

*   **[Observability](observability.md)**: Tracing, logging, and metrics.
*   **[Request Lineage](request_lineage.md)**: Unified lineage across requests and traces.
*   **[Identity Model](identity_model.md)**: Canonical representation of actors.
*   **[Governance & Policy](governance_policy_enforcement.md)**: Enforcing organizational rules.
*   **[Evaluation-Ready Metadata](evaluation.md)**: Defining test contracts and success criteria.

## Advanced Topics

*   **[Interoperability](interoperability.md)**: Adapter Hints for external frameworks.
*   **[Middleware Extension Interface](middleware_extension_interface.md)**: Extending the runtime.
