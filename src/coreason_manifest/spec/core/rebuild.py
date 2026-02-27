from typing import Any

from coreason_manifest.spec.core.primitives.registry import resolve_engine_union, resolve_node_union


def rebuild_manifest() -> None:
    """
    Rebuilds the Pydantic models in the manifest to include newly registered nodes and engines.
    This is necessary because Pydantic V2 resolves unions at import time, so dynamic
    additions to the registry require an explicit rebuild of the schema.
    """
    # Import modules lazily to avoid circular dependencies
    from coreason_manifest.spec.core.compute import reasoning
    from coreason_manifest.spec.core.workflow import flow, nodes

    # 1. Resolve fresh unions
    new_node_union = resolve_node_union()
    new_engine_union = resolve_engine_union()

    # 2. Patch Node-dependent models
    # Graph uses dict[str, AnyNode]
    # We must update the annotation on the field itself

    # Update AnyNode alias in nodes module (affects future imports)
    nodes.AnyNode = new_node_union

    # Patch Graph
    if "nodes" in flow.Graph.model_fields:
        flow.Graph.model_fields["nodes"].annotation = dict[str, new_node_union]  # type: ignore
        flow.Graph.model_rebuild(force=True)

    # Patch LinearFlow
    if "steps" in flow.LinearFlow.model_fields:
        flow.LinearFlow.model_fields["steps"].annotation = list[new_node_union]  # type: ignore
        flow.LinearFlow.model_rebuild(force=True)

    # Patch Engine-dependent models
    # CognitiveProfile uses ReasoningConfig

    # Update ReasoningConfig alias in engines module
    reasoning.ReasoningConfig = new_engine_union

    if "reasoning" in nodes.CognitiveProfile.model_fields:
        nodes.CognitiveProfile.model_fields["reasoning"].annotation = new_engine_union | None  # type: ignore
        nodes.CognitiveProfile.model_rebuild(force=True)

    # 3. Rebuild downstream dependencies
    # AgentNode depends on CognitiveProfile
    nodes.AgentNode.model_rebuild(force=True)
    nodes.HumanNode.model_rebuild(force=True)
    nodes.SwarmNode.model_rebuild(force=True)

    # GraphFlow depends on Graph
    flow.GraphFlow.model_rebuild(force=True)

    # AgentRequest depends on GraphFlow | LinearFlow
    flow.AgentRequest.model_rebuild(force=True)
