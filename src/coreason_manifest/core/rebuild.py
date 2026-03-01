import contextlib
import hashlib
import json

from coreason_manifest.core.primitives.registry import (
    _ENGINE_REGISTRY,
    _NODE_REGISTRY,
    resolve_engine_union,
    resolve_node_union,
)

_LAST_BUILD_HASH: str | None = None


def _compute_registry_hash() -> str:
    state = {"nodes": sorted(_NODE_REGISTRY.keys()), "engines": sorted(_ENGINE_REGISTRY.keys())}
    return hashlib.sha256(json.dumps(state).encode("utf-8")).hexdigest()


def rebuild_manifest() -> None:
    """
    Rebuilds the Pydantic models in the manifest to include newly registered nodes and engines.
    This is necessary because Pydantic V2 resolves unions at import time, so dynamic
    additions to the registry require an explicit rebuild of the schema.
    """
    global _LAST_BUILD_HASH
    current_hash = _compute_registry_hash()

    if _LAST_BUILD_HASH is not None and current_hash == _LAST_BUILD_HASH:
        return

    _LAST_BUILD_HASH = current_hash

    # Import modules lazily to avoid circular dependencies
    from coreason_manifest.core.compute import reasoning
    from coreason_manifest.core.oversight import governance
    from coreason_manifest.core.primitives import types
    from coreason_manifest.core.workflow import flow, nodes

    # Force rebuild of Governance immediately before any models that depend on it
    with contextlib.suppress(Exception):
        governance.Governance.model_rebuild(force=True)

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
        flow.Graph.model_fields["nodes"].annotation = dict[str, new_node_union]  # type: ignore[valid-type]
        flow.Graph.model_rebuild(force=True)

    # Patch LinearFlow
    if "steps" in flow.LinearFlow.model_fields:
        flow.LinearFlow.model_fields["steps"].annotation = list[new_node_union]  # type: ignore[valid-type]
        flow.LinearFlow.model_rebuild(force=True)

    # Patch Engine-dependent models
    # CognitiveProfile uses ReasoningConfig

    # Update ReasoningConfig alias in engines module
    reasoning.ReasoningConfig = new_engine_union

    if "reasoning" in nodes.CognitiveProfile.model_fields:
        nodes.CognitiveProfile.model_fields["reasoning"].annotation = new_engine_union | None
        nodes.CognitiveProfile.model_rebuild(force=True)

    # 3. Rebuild downstream dependencies
    # AgentNode depends on CognitiveProfile
    nodes.AgentNode.model_rebuild(force=True)
    nodes.HumanNode.model_rebuild(force=True)
    nodes.SwarmNode.model_rebuild(force=True)

    # GraphFlow depends on Graph
    flow.GraphFlow.model_rebuild(force=True)

    # Wait, Governance model_rebuild is failing because it imports other things or hasn't fully imported.
    # Actually, Governance doesn't depend on new unions, we might not need to rebuild it explicitly.

    # AgentRequest depends on GraphFlow | LinearFlow
    from coreason_manifest.core.request import AgentRequest

    AgentRequest.model_rebuild(force=True)

    # 4. Rebuild newly added isolated models that don't depend on unions
    # but still might need to resolve types
    types.WasmMiddlewareDef.model_rebuild(force=True)
    reasoning.WasmExecutionReasoning.model_rebuild(force=True)
