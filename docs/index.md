# Welcome to coreason_manifest

This is the documentation for the coreason_manifest project.

## Core Definitions

*   [Coreason Agent Manifest (CAM)](coreason_agent_manifest.md): The primary V2 YAML authoring format for Agents and Recipes.
*   [Runtime Agent Definition](runtime_agent_definition.md): The machine-optimized execution definition for Agents (`AgentDefinition`).
*   [Runtime Recipe Definition](runtime_recipe_definition.md): The machine-optimized execution definition for Recipes (`RecipeManifest`).

## Core Concepts

*   [Atomic Agents](atomic_agents.md): Understand how to define simple, prompt-based agents without complex topologies.
*   [Agent Behavior Protocols](agent_behavior_protocols.md): The standard interfaces (`AgentInterface`) for agent implementation.
*   [Transport-Layer Specification](transport_layer_specification.md): The HTTP/SSE contract for serving agents.
*   [Event Content-Types](event_content_types.md): Standard MIME types for Coreason events.
*   [Session Management](session_management.md): Decoupling execution from memory with standardized Session and Interaction models.
*   [Agent Request Envelope](agent_request_envelope.md): The standard envelope for agent invocations and distributed tracing.
*   [Request Lineage](request_lineage.md): The unified approach to lineage across requests, traces, and audit logs.
*   [Identity Model](identity_model.md): The canonical representation of actors (`Identity`) within the ecosystem.
*   [Evaluation-Ready Metadata](evaluation.md): How to define test contracts and success criteria within your agents.
*   [Observability](observability.md): Details on tracing, logging, and metrics.
*   [Interoperability](interoperability.md): Using "Adapter Hints" to translate agents to frameworks like LangGraph or AutoGen.
*   [V2 Loader Bridge](v2_bridge.md): Using the Bridge to load V2 YAML manifests into the Runtime.
