from typing import TYPE_CHECKING, Any

from coreason_manifest.spec.core.primitives.registry import resolve_engine_union, resolve_node_union

if TYPE_CHECKING:
    from coreason_manifest.spec.core.cognitive import engines, nodes
    from coreason_manifest.spec.core.topology import flow


def rebuild_manifest() -> None:
    """
    Rebuilds the Pydantic models in the manifest to include newly registered nodes and engines.
    This is necessary because Pydantic V2 resolves unions at import time, so dynamic
    additions to the registry require an explicit rebuild of the schema.
    """
    # Import modules lazily to avoid circular dependencies
    from coreason_manifest.spec.core.cognitive import engines, nodes
    from coreason_manifest.spec.core.oversight import co_intelligence, governance, resilience
    from coreason_manifest.spec.core.topology import flow

    # 1. Resolve fresh unions
    new_node_union = resolve_node_union()
    new_engine_union = resolve_engine_union()

    # 2. Patch Node-dependent models
    # Graph uses dict[str, AnyNode]
    # We must update the annotation on the field itself

    # Update AnyNode alias in nodes module (affects future imports)
    nodes.AnyNode = new_node_union

    # Namespace for type resolution
    oversight_types = {
        "Governance": governance.Governance,
        "OperationalPolicy": governance.OperationalPolicy,
        "ResilienceConfig": resilience.ResilienceConfig,
        "EscalationStrategy": resilience.EscalationStrategy,
        "EscalationCriteria": co_intelligence.EscalationCriteria,
    }

    # Patch Graph
    if "nodes" in flow.Graph.model_fields:
        flow.Graph.model_fields["nodes"].annotation = dict[str, new_node_union]  # type: ignore
        flow.Graph.model_rebuild(force=True, _types_namespace=oversight_types)

    # Patch LinearFlow
    if "steps" in flow.LinearFlow.model_fields:
        flow.LinearFlow.model_fields["steps"].annotation = list[new_node_union]  # type: ignore
        flow.LinearFlow.model_rebuild(force=True, _types_namespace=oversight_types)

    # Patch Engine-dependent models
    # CognitiveProfile uses ReasoningConfig

    # Update ReasoningConfig alias in engines module
    engines.ReasoningConfig = new_engine_union

    if "reasoning" in nodes.CognitiveProfile.model_fields:
        nodes.CognitiveProfile.model_fields["reasoning"].annotation = new_engine_union | None  # type: ignore
        nodes.CognitiveProfile.model_rebuild(force=True, _types_namespace=oversight_types)

    # 3. Rebuild downstream dependencies
    # AgentNode depends on CognitiveProfile
    nodes.AgentNode.model_rebuild(force=True, _types_namespace=oversight_types)
    nodes.HumanNode.model_rebuild(force=True, _types_namespace=oversight_types)
    nodes.SwarmNode.model_rebuild(force=True, _types_namespace=oversight_types)

    # GraphFlow depends on Graph
    flow.GraphFlow.model_rebuild(force=True, _types_namespace=oversight_types)

    # AgentRequest depends on GraphFlow | LinearFlow
    flow.AgentRequest.model_rebuild(force=True, _types_namespace=oversight_types)
