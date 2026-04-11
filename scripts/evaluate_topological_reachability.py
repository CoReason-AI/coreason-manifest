# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import sys
import types
import networkx as nx
from typing import TypeAliasType, get_args, get_origin, Union, Annotated, Any, ForwardRef

# Importing the module triggers model_rebuild() at the bottom, resolving Pydantic schemas.
import coreason_manifest.spec.ontology as onto


def get_all_subclasses(cls):
    subclasses = set()
    for sub in cls.__subclasses__():
        subclasses.add(sub)
        subclasses.update(get_all_subclasses(sub))
    return subclasses

CLASS_REGISTRY = {
    cls.__name__: cls
    for cls in get_all_subclasses(onto.CoreasonBaseState)
}

ALIAS_REGISTRY = {
    name: obj.__value__
    for name, obj in vars(onto).items()
    if isinstance(obj, TypeAliasType)
}

G = nx.DiGraph()

for cls_name in CLASS_REGISTRY:
    G.add_node(cls_name)

def extract_referenced_models(annotation: Any, seen: set = None) -> list[type]:
    if seen is None:
        seen = set()

    # Simple cycle prevention based on object id or string
    ann_id = id(annotation) if not isinstance(annotation, str) else annotation
    if ann_id in seen:
        return []
    seen.add(ann_id)

    if isinstance(annotation, str):
        clean_string = annotation.strip("'\"")
        if clean_string in ALIAS_REGISTRY:
            return extract_referenced_models(ALIAS_REGISTRY[clean_string], seen)
        elif clean_string in CLASS_REGISTRY:
            return [CLASS_REGISTRY[clean_string]]
        return []

    if isinstance(annotation, ForwardRef):
        return extract_referenced_models(annotation.__forward_arg__, seen)

    if isinstance(annotation, TypeAliasType):
        return extract_referenced_models(annotation.__value__, seen)

    origin = get_origin(annotation)

    if origin is Annotated:
        args = get_args(annotation)
        if args:
            return extract_referenced_models(args[0], seen)
        return []

    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        result = []
        for arg in args:
            result.extend(extract_referenced_models(arg, seen))
        return result

    if origin in (list, set, tuple, dict):
        args = get_args(annotation)
        result = []
        for arg in args:
            result.extend(extract_referenced_models(arg, seen))
        return result

    if isinstance(annotation, type) and issubclass(annotation, onto.CoreasonBaseState):
        return [annotation]

    return []

for cls_name, cls in CLASS_REGISTRY.items():
    for field_name, field in cls.model_fields.items():
        referenced_models = extract_referenced_models(field.annotation)
        for ref_model in referenced_models:
            if ref_model.__name__ in CLASS_REGISTRY:
                G.add_edge(cls_name, ref_model.__name__)

ROOT_NODES = [
    "WorkflowManifest", "EpistemicLedgerState", "StateHydrationManifest",
    "KinematicDeltaManifest", "TraceExportManifest",
    "FederatedSecurityMacroManifest", "CognitiveSwarmDeploymentMacro",
    "AdversarialMarketTopologyManifest", "ConsensusFederationTopologyManifest",
    "CapabilityForgeTopologyManifest", "IntentElicitationTopologyManifest",
    "NeurosymbolicVerificationTopologyManifest",
    "DAGTopologyManifest", "CouncilTopologyManifest", "SwarmTopologyManifest",
    "EvolutionaryTopologyManifest", "SMPCTopologyManifest",
    "EvaluatorOptimizerTopologyManifest", "DigitalTwinTopologyManifest",
    "DiscourseTreeManifest",
    "OntologicalSurfaceProjectionManifest", "FederatedDiscoveryManifest",
    "PresentationManifest", "DynamicManifoldProjectionManifest",
    "MCPClientIntent", "OntologyDiscoveryIntent", "SemanticMappingHeuristicProposal",
    "TerminalCognitiveEvent", "CognitiveActionSpaceManifest", "EpistemicSOPManifest",
    "EpistemicDomainGraphManifest", "EpistemicTopologicalProofManifest",
    "EpistemicCurriculumManifest"
]

reachable_nodes = set(ROOT_NODES)

for root in ROOT_NODES:
    if root in G:
        reachable_nodes.update(nx.descendants(G, root))

orphaned_nodes = set(G.nodes) - reachable_nodes

if len(orphaned_nodes) > 0:
    print("CRITICAL FAULT: True Orphaned Nodes Detected")
    print("-" * 50)
    for node in sorted(orphaned_nodes):
        print(node)
    print("-" * 50)
    sys.exit(1)
else:
    print(f"Topological Reachability Confirmed: {len(G.nodes)}/{len(G.nodes)} Nodes")
    sys.exit(0)
